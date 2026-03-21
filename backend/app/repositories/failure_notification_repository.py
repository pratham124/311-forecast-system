from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FailureNotificationRecord


class FailureNotificationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, run_id: str, failure_category: str, message: str) -> FailureNotificationRecord:
        record = FailureNotificationRecord(
            run_id=run_id,
            failure_category=failure_category,
            run_status="failed",
            message=message,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def list(self, run_id: str | None = None) -> list[FailureNotificationRecord]:
        statement = select(FailureNotificationRecord).order_by(FailureNotificationRecord.recorded_at.desc())
        if run_id:
            statement = statement.where(FailureNotificationRecord.run_id == run_id)
        return list(self.session.scalars(statement))
