from __future__ import annotations

from fastapi import HTTPException, status

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.failure_notification_repository import FailureNotificationRepository
from app.repositories.run_repository import RunRepository
from app.schemas.failure_notifications import FailureNotification, FailureNotificationList
from app.schemas.ingestion import CurrentDataset, IngestionRunStatus


class IngestionQueryService:
    def __init__(
        self,
        run_repository: RunRepository,
        dataset_repository: DatasetRepository,
        cleaned_dataset_repository: CleanedDatasetRepository,
        failure_repository: FailureNotificationRepository,
    ) -> None:
        self.run_repository = run_repository
        self.dataset_repository = dataset_repository
        self.cleaned_dataset_repository = cleaned_dataset_repository
        self.failure_repository = failure_repository

    def get_run_status(self, run_id: str) -> IngestionRunStatus:
        run = self.run_repository.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
        return IngestionRunStatus.model_validate(run)

    def get_current_dataset(self, source_name: str) -> CurrentDataset:
        marker = self.dataset_repository.get_current(source_name)
        if marker is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Current dataset not found")
        return CurrentDataset(
            source_name=marker.source_name,
            dataset_version_id=marker.dataset_version_id,
            updated_at=marker.updated_at,
            updated_by_run_id=marker.updated_by_run_id,
            record_count=marker.record_count,
            latest_requested_at=self.cleaned_dataset_repository.get_latest_current_requested_at(source_name),
        )

    def list_failure_notifications(self, run_id: str | None = None) -> FailureNotificationList:
        return FailureNotificationList(
            items=[FailureNotification.model_validate(item) for item in self.failure_repository.list(run_id)]
        )
