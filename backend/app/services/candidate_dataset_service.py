from __future__ import annotations

from app.repositories.dataset_repository import DatasetRepository
from app.repositories.models import CandidateDataset
from app.services.dataset_validation_service import DatasetValidationService


class CandidateDatasetService:
    def __init__(
        self,
        dataset_repository: DatasetRepository,
        validation_service: DatasetValidationService,
    ) -> None:
        self.dataset_repository = dataset_repository
        self.validation_service = validation_service

    def create_candidate(self, run_id: str, records: list[dict[str, object]]) -> CandidateDataset:
        return self.dataset_repository.create_candidate(
            run_id=run_id,
            record_count=len(records),
            validation_status="pending",
        )

    def validate_candidate(self, candidate_id: str, records: list[dict[str, object]]) -> tuple[CandidateDataset | None, str | None]:
        result = self.validation_service.validate(records)
        status = "passed" if result.passed else "failed"
        candidate = self.dataset_repository.update_candidate_status(candidate_id, status)
        return candidate, result.reason
