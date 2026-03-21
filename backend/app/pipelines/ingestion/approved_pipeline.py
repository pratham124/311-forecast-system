from __future__ import annotations

from app.repositories.validation_repository import ValidationRepository
from app.services.cleaned_dataset_service import CleanedDatasetService


class ApprovedPipeline:
    def __init__(
        self,
        cleaned_dataset_service: CleanedDatasetService,
        validation_repository: ValidationRepository,
    ) -> None:
        self.cleaned_dataset_service = cleaned_dataset_service
        self.validation_repository = validation_repository

    def approve(
        self,
        *,
        source_name: str,
        ingestion_run_id: str,
        source_dataset_version_id: str,
        validation_run_id: str,
        cleaned_records: list[dict[str, object]],
        duplicate_group_count: int,
    ) -> str:
        cleaned_version = self.cleaned_dataset_service.store_and_approve_cleaned_dataset(
            source_name=source_name,
            ingestion_run_id=ingestion_run_id,
            source_dataset_version_id=source_dataset_version_id,
            validation_run_id=validation_run_id,
            cleaned_records=cleaned_records,
            duplicate_group_count=duplicate_group_count,
        )
        self.validation_repository.finalize_run(
            validation_run_id,
            status="approved",
            approved_dataset_version_id=cleaned_version.dataset_version_id,
            summary="Validation and deduplication completed successfully.",
        )
        return cleaned_version.dataset_version_id
