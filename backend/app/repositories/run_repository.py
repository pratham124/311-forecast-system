from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.repositories.models import IngestionRun


class RunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_run(self, trigger_type: str, cursor_used: str | None) -> IngestionRun:
        run = IngestionRun(
            trigger_type=trigger_type,
            status="running",
            cursor_used=cursor_used,
            cursor_advanced=False,
        )
        self.session.add(run)
        self.session.flush()
        return run

    def finalize_run(
        self,
        run_id: str,
        status: str,
        result_type: str,
        records_received: int | None = None,
        candidate_dataset_id: str | None = None,
        dataset_version_id: str | None = None,
        cursor_advanced: bool = False,
        failure_reason: str | None = None,
    ) -> IngestionRun:
        run = self.session.get(IngestionRun, run_id)
        if run is None:
            raise ValueError("Ingestion run not found")
        run.status = status
        run.result_type = result_type
        run.records_received = records_received
        run.candidate_dataset_id = candidate_dataset_id
        run.dataset_version_id = dataset_version_id
        run.cursor_advanced = cursor_advanced
        run.failure_reason = failure_reason
        run.completed_at = datetime.utcnow()
        self.session.flush()
        return run

    def get_run(self, run_id: str) -> IngestionRun | None:
        return self.session.get(IngestionRun, run_id)
