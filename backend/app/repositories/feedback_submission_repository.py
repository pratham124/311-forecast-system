from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models import FeedbackSubmission, ReviewQueueRecord, SubmissionStatusEvent


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class FeedbackReviewRow:
    submission: FeedbackSubmission
    review_queue_record: ReviewQueueRecord


@dataclass(slots=True)
class FeedbackDetailRow:
    submission: FeedbackSubmission
    review_queue_record: ReviewQueueRecord
    status_events: list[SubmissionStatusEvent]


class FeedbackSubmissionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_submission(
        self,
        *,
        report_type: str,
        description: str,
        contact_email: str | None,
        submitter_kind: str,
        submitter_user_id: str | None,
        correlation_id: str | None,
    ) -> FeedbackSubmission:
        timestamp = _utc_now()
        submission = FeedbackSubmission(
            report_type=report_type,
            description=description,
            contact_email=contact_email,
            submitter_kind=submitter_kind,
            submitter_user_id=submitter_user_id,
            processing_status="accepted",
            submitted_at=timestamp,
            last_status_at=timestamp,
        )
        self.session.add(submission)
        self.session.flush()

        review_row = ReviewQueueRecord(
            feedback_submission_id=submission.feedback_submission_id,
            visibility_status="visible",
            triage_status="new",
            updated_at=timestamp,
        )
        self.session.add(review_row)
        self.session.flush()

        self.append_status_event(
            feedback_submission_id=submission.feedback_submission_id,
            event_type="accepted",
            event_reason=None,
            correlation_id=correlation_id,
            recorded_at=timestamp,
        )
        return submission

    def append_status_event(
        self,
        *,
        feedback_submission_id: str,
        event_type: str,
        event_reason: str | None,
        correlation_id: str | None,
        recorded_at: datetime | None = None,
    ) -> SubmissionStatusEvent:
        timestamp = recorded_at or _utc_now()
        event = SubmissionStatusEvent(
            feedback_submission_id=feedback_submission_id,
            event_type=event_type,
            event_reason=event_reason,
            correlation_id=correlation_id,
            recorded_at=timestamp,
        )
        self.session.add(event)
        submission = self.require_submission(feedback_submission_id)
        submission.processing_status = event_type
        submission.last_status_at = timestamp
        review_row = self.require_review_queue_record(feedback_submission_id)
        review_row.updated_at = timestamp
        self.session.flush()
        return event

    def set_external_reference(self, feedback_submission_id: str, external_reference: str | None) -> FeedbackSubmission:
        submission = self.require_submission(feedback_submission_id)
        submission.external_reference = external_reference
        self.session.flush()
        return submission

    def list_review_rows(
        self,
        *,
        report_type: str | None = None,
        processing_status: str | None = None,
        submitted_after: datetime | None = None,
        submitted_before: datetime | None = None,
    ) -> list[FeedbackReviewRow]:
        filters = [ReviewQueueRecord.visibility_status == "visible"]
        if report_type:
            filters.append(FeedbackSubmission.report_type == report_type)
        if processing_status:
            filters.append(FeedbackSubmission.processing_status == processing_status)
        if submitted_after:
            filters.append(FeedbackSubmission.submitted_at >= submitted_after)
        if submitted_before:
            filters.append(FeedbackSubmission.submitted_at <= submitted_before)

        statement = (
            select(FeedbackSubmission, ReviewQueueRecord)
            .join(
                ReviewQueueRecord,
                ReviewQueueRecord.feedback_submission_id == FeedbackSubmission.feedback_submission_id,
            )
            .where(and_(*filters))
            .order_by(FeedbackSubmission.submitted_at.desc(), FeedbackSubmission.feedback_submission_id.desc())
        )
        rows = self.session.execute(statement).all()
        return [FeedbackReviewRow(submission=submission, review_queue_record=review_row) for submission, review_row in rows]

    def get_detail_row(self, feedback_submission_id: str) -> FeedbackDetailRow | None:
        statement = (
            select(FeedbackSubmission, ReviewQueueRecord)
            .join(
                ReviewQueueRecord,
                ReviewQueueRecord.feedback_submission_id == FeedbackSubmission.feedback_submission_id,
            )
            .where(
                FeedbackSubmission.feedback_submission_id == feedback_submission_id,
                ReviewQueueRecord.visibility_status == "visible",
            )
        )
        row = self.session.execute(statement).one_or_none()
        if row is None:
            return None
        submission, review_row = row
        status_events = self.list_status_events(feedback_submission_id)
        return FeedbackDetailRow(submission=submission, review_queue_record=review_row, status_events=status_events)

    def list_status_events(self, feedback_submission_id: str) -> list[SubmissionStatusEvent]:
        statement = (
            select(SubmissionStatusEvent)
            .where(SubmissionStatusEvent.feedback_submission_id == feedback_submission_id)
            .order_by(SubmissionStatusEvent.recorded_at.asc(), SubmissionStatusEvent.submission_status_event_id.asc())
        )
        return list(self.session.scalars(statement))

    def list_submissions_for_retry(self, limit: int = 50) -> list[FeedbackSubmission]:
        statement = (
            select(FeedbackSubmission)
            .where(FeedbackSubmission.processing_status == "deferred_for_retry")
            .order_by(FeedbackSubmission.last_status_at.asc(), FeedbackSubmission.feedback_submission_id.asc())
            .limit(limit)
        )
        return list(self.session.scalars(statement))

    def require_submission(self, feedback_submission_id: str) -> FeedbackSubmission:
        submission = self.session.get(FeedbackSubmission, feedback_submission_id)
        if submission is None:
            raise LookupError("Feedback submission not found")
        return submission

    def require_review_queue_record(self, feedback_submission_id: str) -> ReviewQueueRecord:
        statement = select(ReviewQueueRecord).where(ReviewQueueRecord.feedback_submission_id == feedback_submission_id)
        review_row = self.session.scalar(statement)
        if review_row is None:
            raise LookupError("Feedback review queue record not found")
        return review_row
