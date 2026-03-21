from __future__ import annotations

from app.repositories.review_needed_repository import ReviewNeededRepository
from app.repositories.validation_repository import ValidationRepository


class BlockedOutcomePipeline:
    def __init__(
        self,
        validation_repository: ValidationRepository,
        review_needed_repository: ReviewNeededRepository,
    ) -> None:
        self.validation_repository = validation_repository
        self.review_needed_repository = review_needed_repository

    def hold_for_review(
        self,
        validation_run_id: str,
        duplicate_analysis_id: str,
        duplicate_percentage: float,
        reason: str,
    ) -> None:
        self.review_needed_repository.create(validation_run_id, duplicate_analysis_id, reason)
        self.validation_repository.finalize_run(
            validation_run_id,
            status="review_needed",
            duplicate_percentage=duplicate_percentage,
            review_reason=reason,
            summary=reason,
        )

    def fail(self, validation_run_id: str, stage: str, reason: str) -> None:
        self.validation_repository.finalize_run(
            validation_run_id,
            status="failed",
            failure_stage=stage,
            summary=reason,
        )
