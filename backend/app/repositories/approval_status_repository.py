from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ValidationRun
from app.models import CurrentDatasetMarker, DatasetVersion


class ApprovalStatusRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_current_marker(self, source_name: str) -> CurrentDatasetMarker | None:
        return self.session.get(CurrentDatasetMarker, source_name)

    def get_dataset_version(self, dataset_version_id: str) -> DatasetVersion | None:
        return self.session.get(DatasetVersion, dataset_version_id)

    def get_validation_run(self, validation_run_id: str) -> ValidationRun | None:
        return self.session.get(ValidationRun, validation_run_id)

    def get_validation_run_by_approved_dataset(self, dataset_version_id: str) -> ValidationRun | None:
        statement = select(ValidationRun).where(ValidationRun.approved_dataset_version_id == dataset_version_id)
        return self.session.scalars(statement).first()
