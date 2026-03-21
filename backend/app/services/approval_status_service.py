from __future__ import annotations

from fastapi import HTTPException, status

from app.repositories.approval_status_repository import ApprovalStatusRepository
from app.schemas.validation_status import ApprovedDatasetStatus


class ApprovalStatusService:
    def __init__(self, repository: ApprovalStatusRepository) -> None:
        self.repository = repository

    def get_current_approved_dataset(self, source_name: str) -> ApprovedDatasetStatus:
        marker = self.repository.get_current_marker(source_name)
        if marker is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No approved dataset found")
        dataset = self.repository.get_dataset_version(marker.dataset_version_id)
        if dataset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approved dataset not found")
        return ApprovedDatasetStatus(
            dataset_version_id=dataset.dataset_version_id,
            source_dataset_version_id=dataset.source_dataset_version_id,
            approved_at=dataset.activated_at or marker.updated_at,
            approved_by_validation_run_id=dataset.approved_by_validation_run_id,
            cleaned_record_count=dataset.record_count,
            duplicate_group_count=dataset.duplicate_group_count or 0,
            summary="Current approved cleaned dataset.",
        )
