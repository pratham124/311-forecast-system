from __future__ import annotations

from fastapi import HTTPException, status

from app.repositories.approval_status_repository import ApprovalStatusRepository
from app.repositories.review_needed_repository import ReviewNeededRepository
from app.schemas.validation_status import ReviewNeededStatus, ReviewNeededStatusList, ValidationRunStatus


class ValidationStatusService:
    def __init__(
        self,
        approval_repository: ApprovalStatusRepository,
        review_needed_repository: ReviewNeededRepository,
    ) -> None:
        self.approval_repository = approval_repository
        self.review_needed_repository = review_needed_repository

    def get_validation_run_status(self, validation_run_id: str) -> ValidationRunStatus:
        run = self.approval_repository.get_validation_run(validation_run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Validation run not found")
        visibility_state = "in_progress"
        if run.status == "approved":
            visibility_state = "approved_active"
        elif run.status != "running":
            visibility_state = "blocked"
        return ValidationRunStatus(
            validation_run_id=run.validation_run_id,
            ingestion_run_id=run.ingestion_run_id,
            source_dataset_version_id=run.source_dataset_version_id,
            approved_dataset_version_id=run.approved_dataset_version_id,
            status=run.status,
            failure_stage=run.failure_stage,
            visibility_state=visibility_state,
            duplicate_percentage=float(run.duplicate_percentage) if run.duplicate_percentage is not None else None,
            started_at=run.started_at,
            completed_at=run.completed_at,
            review_reason=run.review_reason,
            summary=run.summary,
        )

    def list_review_needed(self, validation_run_id: str | None) -> ReviewNeededStatusList:
        items = []
        for review_record, analysis in self.review_needed_repository.list(validation_run_id):
            items.append(
                ReviewNeededStatus(
                    review_record_id=review_record.review_record_id,
                    validation_run_id=review_record.validation_run_id,
                    duplicate_percentage=float(analysis.duplicate_percentage),
                    threshold_percentage=float(analysis.threshold_percentage),
                    recorded_at=review_record.recorded_at,
                    reason=review_record.reason,
                    summary=review_record.reason,
                )
            )
        return ReviewNeededStatusList(items=items)
