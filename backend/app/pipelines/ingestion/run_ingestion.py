from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.clients.edmonton_311 import (
    Edmonton311AuthError,
    Edmonton311Client,
    Edmonton311UnavailableError,
)
from app.core.config import get_settings
from app.repositories.cursor_repository import CursorRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.failure_notification_repository import FailureNotificationRepository
from app.repositories.run_repository import RunRepository
from app.schemas.ingestion import IngestionRunStatus
from app.services.activation_guard_service import ActivationGuardService
from app.services.candidate_dataset_service import CandidateDatasetService
from app.services.dataset_validation_service import DatasetValidationService
from app.services.failure_notification_service import FailureNotificationService
from app.services.ingestion_logging_service import IngestionLoggingService


@dataclass
class IngestionPipeline:
    session: Session
    client: Edmonton311Client
    logging_service: IngestionLoggingService

    def __post_init__(self) -> None:
        self.settings = get_settings()
        self.cursor_repository = CursorRepository(self.session)
        self.dataset_repository = DatasetRepository(self.session)
        self.run_repository = RunRepository(self.session)
        self.failure_repository = FailureNotificationRepository(self.session)
        self.validation_service = DatasetValidationService()
        self.candidate_service = CandidateDatasetService(self.dataset_repository, self.validation_service)
        self.notification_service = FailureNotificationService(self.failure_repository)
        self.guard_service = ActivationGuardService()

    def start_run(self, trigger_type: str = "scheduled") -> tuple[str, str | None, object | None]:
        cursor = self.cursor_repository.get(self.settings.source_name)
        previous_marker = self.dataset_repository.get_current(self.settings.source_name)
        run = self.run_repository.create_run(trigger_type=trigger_type, cursor_used=cursor.cursor_value if cursor else None)
        return run.run_id, cursor.cursor_value if cursor else None, previous_marker

    def run(
        self,
        trigger_type: str = "scheduled",
        inject_storage_failure: bool = False,
        existing_run_id: str | None = None,
        existing_cursor: str | None = None,
        previous_marker=None,
    ) -> IngestionRunStatus:
        print(f"[debug] pipeline.run entered trigger_type={trigger_type} existing_run_id={existing_run_id}")
        if existing_run_id is None:
            run_id, cursor_value, previous_marker = self.start_run(trigger_type=trigger_type)
        else:
            run_id, cursor_value = existing_run_id, existing_cursor
            if previous_marker is None:
                previous_marker = self.dataset_repository.get_current(self.settings.source_name)
        print(f"[debug] pipeline.run using run_id={run_id} cursor_value={cursor_value}")

        try:
            fetch_result = self.client.fetch_records(cursor_value)
            print(
                f"[debug] fetch completed run_id={run_id} result_type={fetch_result.result_type} "
                f"records={len(fetch_result.records)} cursor_value={fetch_result.cursor_value}"
            )
        except Edmonton311AuthError as exc:
            print(f"[debug] auth failure run_id={run_id} error={exc}")
            return self._fail_run(run_id, "auth_failure", str(exc), previous_marker)
        except Edmonton311UnavailableError as exc:
            print(f"[debug] source unavailable run_id={run_id} error={exc}")
            return self._fail_run(run_id, "source_unavailable", str(exc), previous_marker)

        if fetch_result.result_type == "no_new_records":
            print(f"[debug] no_new_records run_id={run_id}")
            finalized = self.run_repository.finalize_run(
                run_id,
                status="success",
                result_type="no_new_records",
                records_received=0,
                cursor_advanced=False,
            )
            self.logging_service.log(
                "ingestion.completed",
                run_id=run_id,
                result_type="no_new_records",
                status="success",
                cursor_advanced=False,
                current_dataset_version_id=previous_marker.dataset_version_id if previous_marker else None,
            )
            self.session.commit()
            print(f"[debug] no_new_records finalized run_id={run_id}")
            return IngestionRunStatus.model_validate(finalized)

        records = fetch_result.records
        print(f"[debug] creating candidate run_id={run_id} record_count={len(records)}")
        candidate = self.candidate_service.create_candidate(run_id, records)
        candidate, validation_reason = self.candidate_service.validate_candidate(candidate.candidate_dataset_id, records)
        if validation_reason:
            print(f"[debug] validation failed run_id={run_id} reason={validation_reason}")
            return self._fail_run(
                run_id,
                "validation_failure",
                validation_reason,
                previous_marker,
                candidate_dataset_id=candidate.candidate_dataset_id if candidate else None,
                records_received=len(records),
            )

        if inject_storage_failure:
            print(f"[debug] injected storage failure run_id={run_id}")
            return self._fail_run(
                run_id,
                "storage_failure",
                "Injected storage failure",
                previous_marker,
                candidate_dataset_id=candidate.candidate_dataset_id if candidate else None,
                records_received=len(records),
            )

        dataset_version = self.dataset_repository.create_dataset_version(
            source_name=self.settings.source_name,
            run_id=run_id,
            candidate_id=candidate.candidate_dataset_id if candidate else None,
            record_count=len(records),
            records=records,
        )
        print(f"[debug] stored dataset_version run_id={run_id} dataset_version_id={dataset_version.dataset_version_id}")
        self.dataset_repository.activate_dataset(self.settings.source_name, dataset_version.dataset_version_id, run_id)
        if fetch_result.cursor_value:
            self.cursor_repository.upsert(self.settings.source_name, fetch_result.cursor_value, run_id)
            print(f"[debug] cursor advanced run_id={run_id} cursor_value={fetch_result.cursor_value}")

        finalized = self.run_repository.finalize_run(
            run_id,
            status="success",
            result_type="new_data",
            records_received=len(records),
            candidate_dataset_id=candidate.candidate_dataset_id if candidate else None,
            dataset_version_id=dataset_version.dataset_version_id,
            cursor_advanced=bool(fetch_result.cursor_value),
        )
        self.logging_service.log(
            "ingestion.completed",
            run_id=run_id,
            result_type="new_data",
            status="success",
            dataset_version_id=dataset_version.dataset_version_id,
            records_received=len(records),
            cursor_advanced=bool(fetch_result.cursor_value),
        )
        self.session.commit()
        print(f"[debug] success finalized run_id={run_id} result_type=new_data")
        return IngestionRunStatus.model_validate(finalized)

    def _fail_run(
        self,
        run_id: str,
        failure_category: str,
        reason: str,
        previous_marker,
        candidate_dataset_id: str | None = None,
        records_received: int | None = None,
    ) -> IngestionRunStatus:
        print(f"[debug] fail_run run_id={run_id} category={failure_category} reason={reason}")
        notification = self.notification_service.create_notification(run_id, failure_category, reason)
        finalized = self.run_repository.finalize_run(
            run_id,
            status="failed",
            result_type=failure_category,
            records_received=records_received,
            candidate_dataset_id=candidate_dataset_id,
            cursor_advanced=False,
            failure_reason=reason,
        )
        current_marker = self.dataset_repository.get_current(self.settings.source_name)
        self.guard_service.assert_marker_unchanged(previous_marker, current_marker)
        self.guard_service.assert_not_current(None, None)
        self.logging_service.log(
            "ingestion.failed",
            run_id=run_id,
            result_type=failure_category,
            status="failed",
            failure_reason=reason,
            notification_id=notification.notification_id,
            current_dataset_version_id=previous_marker.dataset_version_id if previous_marker else None,
        )
        self.session.commit()
        print(f"[debug] fail_run finalized run_id={run_id} notification_id={notification.notification_id}")
        return IngestionRunStatus.model_validate(finalized)
