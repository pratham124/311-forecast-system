from __future__ import annotations

from app.repositories.validation_repository import ValidationRepository


class RejectionPipeline:
    def __init__(self, validation_repository: ValidationRepository) -> None:
        self.validation_repository = validation_repository

    def reject(self, validation_run_id: str, reason: str) -> None:
        self.validation_repository.finalize_run(
            validation_run_id,
            status="rejected",
            failure_stage="schema_validation",
            summary=reason,
        )
