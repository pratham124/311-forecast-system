from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CandidateDataset, CurrentDatasetMarker, DatasetRecord, DatasetVersion


class DatasetRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_candidate(self, run_id: str, record_count: int, validation_status: str) -> CandidateDataset:
        candidate = CandidateDataset(
            ingestion_run_id=run_id,
            record_count=record_count,
            validation_status=validation_status,
            is_current=False,
        )
        self.session.add(candidate)
        self.session.flush()
        return candidate

    def update_candidate_status(self, candidate_id: str, validation_status: str) -> CandidateDataset | None:
        candidate = self.session.get(CandidateDataset, candidate_id)
        if candidate is None:
            return None
        candidate.validation_status = validation_status
        self.session.flush()
        return candidate

    def create_dataset_version(
        self,
        source_name: str,
        run_id: str,
        candidate_id: str | None,
        record_count: int,
        records: list[dict[str, object]] | None = None,
        *,
        validation_status: str = "pending",
        storage_status: str = "stored",
        dataset_kind: str = "source",
        source_dataset_version_id: str | None = None,
        duplicate_group_count: int = 0,
        approved_by_validation_run_id: str | None = None,
    ) -> DatasetVersion:
        dataset_version = DatasetVersion(
            source_name=source_name,
            ingestion_run_id=run_id,
            candidate_dataset_id=candidate_id,
            source_dataset_version_id=source_dataset_version_id,
            record_count=record_count,
            validation_status=validation_status,
            storage_status=storage_status,
            dataset_kind=dataset_kind,
            duplicate_group_count=duplicate_group_count,
            approved_by_validation_run_id=approved_by_validation_run_id,
            is_current=False,
            stored_at=datetime.utcnow(),
        )
        self.session.add(dataset_version)
        self.session.flush()
        if records:
            self.session.add_all(
                [DatasetRecord.from_normalized_row(dataset_version.dataset_version_id, record) for record in records]
            )
            self.session.flush()
        return dataset_version

    def activate_dataset(self, source_name: str, dataset_version_id: str, run_id: str) -> CurrentDatasetMarker:
        prior_current = self.session.scalars(
            select(DatasetVersion).where(
                DatasetVersion.source_name == source_name,
                DatasetVersion.is_current.is_(True),
            )
        ).all()
        for dataset in prior_current:
            dataset.is_current = False

        dataset_version = self.session.get(DatasetVersion, dataset_version_id)
        if dataset_version is None:
            raise ValueError("Dataset version not found")
        dataset_version.is_current = True
        dataset_version.activated_at = datetime.utcnow()

        marker = self.session.get(CurrentDatasetMarker, source_name)
        if marker is None:
            marker = CurrentDatasetMarker(
                source_name=source_name,
                dataset_version_id=dataset_version_id,
                updated_by_run_id=run_id,
                record_count=dataset_version.record_count,
            )
            self.session.add(marker)
        else:
            marker.dataset_version_id = dataset_version_id
            marker.updated_at = datetime.utcnow()
            marker.updated_by_run_id = run_id
            marker.record_count = dataset_version.record_count
        self.session.flush()
        return marker

    def get_current(self, source_name: str) -> CurrentDatasetMarker | None:
        return self.session.get(CurrentDatasetMarker, source_name)

    def list_dataset_records(self, dataset_version_id: str) -> list[DatasetRecord]:
        statement = select(DatasetRecord).where(DatasetRecord.dataset_version_id == dataset_version_id)
        return list(self.session.scalars(statement))
