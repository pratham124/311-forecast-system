from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DuplicateAnalysisResult, ReviewNeededRecord


class ReviewNeededRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, validation_run_id: str, duplicate_analysis_id: str, reason: str) -> ReviewNeededRecord:
        record = ReviewNeededRecord(
            validation_run_id=validation_run_id,
            duplicate_analysis_id=duplicate_analysis_id,
            reason=reason,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def list(self, validation_run_id: str | None = None) -> list[tuple[ReviewNeededRecord, DuplicateAnalysisResult]]:
        statement = (
            select(ReviewNeededRecord, DuplicateAnalysisResult)
            .join(
                DuplicateAnalysisResult,
                DuplicateAnalysisResult.duplicate_analysis_id == ReviewNeededRecord.duplicate_analysis_id,
            )
            .order_by(ReviewNeededRecord.recorded_at.desc())
        )
        if validation_run_id:
            statement = statement.where(ReviewNeededRecord.validation_run_id == validation_run_id)
        return list(self.session.execute(statement).all())
