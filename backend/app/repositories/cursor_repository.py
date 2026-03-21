from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import SuccessfulPullCursor


class CursorRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, source_name: str) -> SuccessfulPullCursor | None:
        return self.session.get(SuccessfulPullCursor, source_name)

    def upsert(self, source_name: str, cursor_value: str, run_id: str) -> SuccessfulPullCursor:
        record = self.get(source_name)
        if record is None:
            record = SuccessfulPullCursor(
                source_name=source_name,
                cursor_value=cursor_value,
                updated_by_run_id=run_id,
            )
            self.session.add(record)
        else:
            record.cursor_value = cursor_value
            record.updated_at = datetime.utcnow()
            record.updated_by_run_id = run_id
        self.session.flush()
        return record
