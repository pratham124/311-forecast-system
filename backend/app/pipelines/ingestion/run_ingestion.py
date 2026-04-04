from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.clients.edmonton_311 import (
    Edmonton311AuthError,
    Edmonton311Client,
    Edmonton311UnavailableError,
)
from app.core.config import get_settings
from app.pipelines.ingestion.validation_pipeline import ValidationPipeline
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
        self.validation_pipeline = ValidationPipeline(self.session)

    def start_run(self, trigger_type: str = "scheduled") -> tuple[str, str | None, object | None]:
        cursor = self.cursor_repository.get(self.settings.source_name)
        previous_marker = self.dataset_repository.get_current(self.settings.source_name)
        run = self.run_repository.create_run(trigger_type=trigger_type, cursor_used=cursor.cursor_value if cursor else None)
        self.logging_service.log(
            "ingestion.started",
            run_id=run.run_id,
            trigger_type=trigger_type,
            cursor_used=cursor.cursor_value if cursor else None,
            previous_dataset_version_id=previous_marker.dataset_version_id if previous_marker else None,
        )
        return run.run_id, cursor.cursor_value if cursor else None, previous_marker

    def run(
        self,
        trigger_type: str = "scheduled",
        inject_storage_failure: bool = False,
        existing_run_id: str | None = None,
        existing_cursor: str | None = None,
        previous_marker=None,
        run_follow_on_jobs: bool = True,
    ) -> IngestionRunStatus:
        if existing_run_id is None:
            run_id, cursor_value, previous_marker = self.start_run(trigger_type=trigger_type)
        else:
            run_id, cursor_value = existing_run_id, existing_cursor
            if previous_marker is None:
                previous_marker = self.dataset_repository.get_current(self.settings.source_name)
            self.logging_service.log(
                "ingestion.resumed",
                run_id=run_id,
                trigger_type=trigger_type,
                cursor_used=cursor_value,
                previous_dataset_version_id=previous_marker.dataset_version_id if previous_marker else None,
            )

        try:
            self.logging_service.log("ingestion.fetch.started", run_id=run_id, cursor_used=cursor_value)
            fetch_result = self.client.fetch_records(cursor_value)
        except Edmonton311AuthError as exc:
            return self._fail_run(run_id, "auth_failure", str(exc), previous_marker)
        except Edmonton311UnavailableError as exc:
            return self._fail_run(run_id, "source_unavailable", str(exc), previous_marker)

        self.logging_service.log(
            "ingestion.fetch.completed",
            run_id=run_id,
            result_type=fetch_result.result_type,
            records_received=len(fetch_result.records),
            cursor_value=fetch_result.cursor_value,
        )

        if fetch_result.result_type == "no_new_records":
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
            return IngestionRunStatus.model_validate(finalized)

        records = fetch_result.records
        self.logging_service.log("ingestion.candidate.started", run_id=run_id, records_received=len(records))
        candidate = self.candidate_service.create_candidate(run_id, records)
        self.logging_service.log(
            "ingestion.candidate.completed",
            run_id=run_id,
            candidate_dataset_id=candidate.candidate_dataset_id,
            record_count=len(records),
        )
        if inject_storage_failure:
            return self._fail_run(
                run_id,
                "storage_failure",
                "Injected storage failure",
                previous_marker,
                candidate_dataset_id=candidate.candidate_dataset_id,
                records_received=len(records),
            )

        self.logging_service.log(
            "ingestion.source_dataset.started",
            run_id=run_id,
            candidate_dataset_id=candidate.candidate_dataset_id,
            record_count=len(records),
        )
        source_dataset = self.dataset_repository.create_dataset_version(
            source_name=self.settings.source_name,
            run_id=run_id,
            candidate_id=candidate.candidate_dataset_id,
            record_count=len(records),
            records=records,
            validation_status="pending",
            dataset_kind="source",
        )
        self.logging_service.log(
            "ingestion.source_dataset.completed",
            run_id=run_id,
            dataset_version_id=source_dataset.dataset_version_id,
            record_count=len(records),
        )
        self.logging_service.log(
            "ingestion.validation.started",
            run_id=run_id,
            dataset_version_id=source_dataset.dataset_version_id,
        )
        validation_run_id = self.validation_pipeline.run(
            run_id,
            source_dataset.dataset_version_id,
            records,
            run_follow_on_jobs=run_follow_on_jobs,
        )

        validation_run = self.validation_pipeline.validation_repository.get_run(validation_run_id)
        self.logging_service.log(
            "ingestion.validation.completed",
            run_id=run_id,
            validation_run_id=validation_run_id,
            validation_status=validation_run.status if validation_run is not None else "missing",
        )
        candidate_status = validation_run.status if validation_run is not None else "failed"
        self.dataset_repository.update_candidate_status(candidate.candidate_dataset_id, candidate_status)
        if validation_run is not None:
            source_dataset.validation_status = validation_run.status

        if fetch_result.cursor_value:
            self.cursor_repository.upsert(self.settings.source_name, fetch_result.cursor_value, run_id)
            self.logging_service.log(
                "ingestion.cursor.updated",
                run_id=run_id,
                cursor_value=fetch_result.cursor_value,
            )

        result_type = "new_data"
        if validation_run is not None and validation_run.status != "approved":
            result_type = validation_run.status

        self.logging_service.log(
            "ingestion.finalize.started",
            run_id=run_id,
            result_type=result_type,
            validation_run_id=validation_run_id,
        )
        finalized = self.run_repository.finalize_run(
            run_id,
            status="success",
            result_type=result_type,
            records_received=len(records),
            candidate_dataset_id=candidate.candidate_dataset_id,
            dataset_version_id=source_dataset.dataset_version_id,
            cursor_advanced=bool(fetch_result.cursor_value),
        )
        self.logging_service.log(
            "ingestion.completed",
            run_id=run_id,
            result_type=result_type,
            status="success",
            dataset_version_id=source_dataset.dataset_version_id,
            validation_run_id=validation_run_id,
            records_received=len(records),
            cursor_advanced=bool(fetch_result.cursor_value),
        )
        self.session.commit()
        return IngestionRunStatus.model_validate(finalized)

    def fail_unexpected_run(
        self,
        run_id: str,
        reason: str,
        previous_marker,
    ) -> IngestionRunStatus:
        return self._fail_run(run_id, "unexpected_failure", reason, previous_marker)

    def _fail_run(
        self,
        run_id: str,
        failure_category: str,
        reason: str,
        previous_marker,
        candidate_dataset_id: str | None = None,
        records_received: int | None = None,
    ) -> IngestionRunStatus:
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
        return IngestionRunStatus.model_validate(finalized)
