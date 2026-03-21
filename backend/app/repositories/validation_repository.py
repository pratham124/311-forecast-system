from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import (
    DuplicateAnalysisResult,
    DuplicateGroup,
    ValidationResultRecord,
    ValidationRun,
)


class ValidationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_run(
        self,
        ingestion_run_id: str,
        source_dataset_version_id: str,
        threshold_percentage: float,
    ) -> ValidationRun:
        run = ValidationRun(
            ingestion_run_id=ingestion_run_id,
            source_dataset_version_id=source_dataset_version_id,
            duplicate_threshold_type="percentage",
            duplicate_percentage=None,
            status="running",
            summary="Validation is in progress.",
        )
        self.session.add(run)
        self.session.flush()
        return run

    def record_validation_result(
        self,
        validation_run_id: str,
        *,
        status: str,
        required_field_check: str,
        type_check: str,
        format_check: str,
        completeness_check: str,
        issue_summary: str | None,
    ) -> ValidationResultRecord:
        result = ValidationResultRecord(
            validation_run_id=validation_run_id,
            status=status,
            required_field_check=required_field_check,
            type_check=type_check,
            format_check=format_check,
            completeness_check=completeness_check,
            issue_summary=issue_summary,
        )
        self.session.add(result)
        self.session.flush()
        return result

    def record_duplicate_analysis(
        self,
        validation_run_id: str,
        *,
        status: str,
        total_record_count: int,
        duplicate_record_count: int,
        duplicate_percentage: float,
        threshold_percentage: float,
        duplicate_group_count: int,
        issue_summary: str | None = None,
    ) -> DuplicateAnalysisResult:
        result = DuplicateAnalysisResult(
            validation_run_id=validation_run_id,
            status=status,
            total_record_count=total_record_count,
            duplicate_record_count=duplicate_record_count,
            duplicate_percentage=duplicate_percentage,
            threshold_percentage=threshold_percentage,
            duplicate_group_count=duplicate_group_count,
            issue_summary=issue_summary,
        )
        self.session.add(result)
        self.session.flush()
        return result

    def record_duplicate_groups(
        self,
        duplicate_analysis_id: str,
        groups: list[dict[str, object]],
    ) -> list[DuplicateGroup]:
        stored_groups = [
            DuplicateGroup(
                duplicate_analysis_id=duplicate_analysis_id,
                group_key=str(group["group_key"]),
                source_record_count=int(group["source_record_count"]),
                resolution_status=str(group["resolution_status"]),
                cleaned_record_id=group.get("cleaned_record_id"),
                resolution_summary=group.get("resolution_summary"),
            )
            for group in groups
        ]
        self.session.add_all(stored_groups)
        self.session.flush()
        return stored_groups

    def finalize_run(
        self,
        validation_run_id: str,
        *,
        status: str,
        duplicate_percentage: float | None = None,
        failure_stage: str | None = None,
        approved_dataset_version_id: str | None = None,
        review_reason: str | None = None,
        summary: str | None = None,
    ) -> ValidationRun:
        run = self.get_run(validation_run_id)
        if run is None:
            raise ValueError("Validation run not found")
        run.status = status
        run.completed_at = datetime.utcnow()
        run.failure_stage = failure_stage
        run.duplicate_percentage = Decimal(str(duplicate_percentage)) if duplicate_percentage is not None else None
        run.approved_dataset_version_id = approved_dataset_version_id
        run.review_reason = review_reason
        run.summary = summary
        self.session.flush()
        return run

    def get_run(self, validation_run_id: str) -> ValidationRun | None:
        return self.session.get(ValidationRun, validation_run_id)
