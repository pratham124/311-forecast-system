from __future__ import annotations

from app.repositories.dataset_repository import DatasetRepository
from app.repositories.validation_repository import ValidationRepository
from app.models import DatasetVersion


class CleanedDatasetService:
    def __init__(
        self,
        dataset_repository: DatasetRepository,
        validation_repository: ValidationRepository,
    ) -> None:
        self.dataset_repository = dataset_repository
        self.validation_repository = validation_repository

    def store_and_approve_cleaned_dataset(
        self,
        *,
        source_name: str,
        ingestion_run_id: str,
        source_dataset_version_id: str,
        validation_run_id: str,
        cleaned_records: list[dict[str, object]],
        duplicate_group_count: int,
    ) -> DatasetVersion:
        dataset_version = self.dataset_repository.create_dataset_version(
            source_name=source_name,
            run_id=ingestion_run_id,
            candidate_id=None,
            record_count=len(cleaned_records),
            records=cleaned_records,
            validation_status="approved",
            dataset_kind="cleaned",
            source_dataset_version_id=source_dataset_version_id,
            duplicate_group_count=duplicate_group_count,
            approved_by_validation_run_id=validation_run_id,
        )
        self.dataset_repository.activate_dataset(source_name, dataset_version.dataset_version_id, ingestion_run_id)
        return dataset_version
