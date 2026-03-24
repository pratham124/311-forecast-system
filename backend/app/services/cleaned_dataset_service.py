from __future__ import annotations

from app.models import DatasetVersion
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.validation_repository import ValidationRepository


class CleanedDatasetService:
    def __init__(
        self,
        dataset_repository: DatasetRepository,
        validation_repository: ValidationRepository,
        cleaned_dataset_repository: CleanedDatasetRepository | DatasetRepository | None = None,
    ) -> None:
        self.dataset_repository = dataset_repository
        self.validation_repository = validation_repository
        self.cleaned_dataset_repository = cleaned_dataset_repository or dataset_repository

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
            record_count=0,
            records=None,
            validation_status="approved",
            dataset_kind="cleaned",
            source_dataset_version_id=source_dataset_version_id,
            duplicate_group_count=duplicate_group_count,
            approved_by_validation_run_id=validation_run_id,
        )
        self.cleaned_dataset_repository.upsert_current_cleaned_records(
            source_name=source_name,
            ingestion_run_id=ingestion_run_id,
            source_dataset_version_id=source_dataset_version_id,
            approved_dataset_version_id=dataset_version.dataset_version_id,
            approved_by_validation_run_id=validation_run_id,
            cleaned_records=cleaned_records,
        )
        dataset_version.record_count = self.cleaned_dataset_repository.count_current_cleaned_records(source_name)
        self.dataset_repository.activate_dataset(source_name, dataset_version.dataset_version_id, ingestion_run_id)
        return dataset_version
