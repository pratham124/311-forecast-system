from __future__ import annotations

from app.repositories.feedback_submission_repository import FeedbackSubmissionRepository
from app.schemas.feedback_submissions import (
    FeedbackSubmissionDetail,
    FeedbackSubmissionSummary,
    SubmissionStatusEventRead,
)


class FeedbackReviewService:
    def __init__(self, repository: FeedbackSubmissionRepository) -> None:
        self.repository = repository

    def list_submissions(
        self,
        *,
        report_type: str | None = None,
        processing_status: str | None = None,
        submitted_after=None,
        submitted_before=None,
    ) -> list[FeedbackSubmissionSummary]:
        rows = self.repository.list_review_rows(
            report_type=report_type,
            processing_status=processing_status,
            submitted_after=submitted_after,
            submitted_before=submitted_before,
        )
        return [
            FeedbackSubmissionSummary(
                feedbackSubmissionId=row.submission.feedback_submission_id,
                reportType=row.submission.report_type,
                submitterKind=row.submission.submitter_kind,
                processingStatus=row.submission.processing_status,
                submittedAt=row.submission.submitted_at,
                triageStatus=row.review_queue_record.triage_status,
            )
            for row in rows
        ]

    def get_submission(self, feedback_submission_id: str) -> FeedbackSubmissionDetail | None:
        row = self.repository.get_detail_row(feedback_submission_id)
        if row is None:
            return None
        return FeedbackSubmissionDetail(
            feedbackSubmissionId=row.submission.feedback_submission_id,
            reportType=row.submission.report_type,
            description=row.submission.description,
            contactEmail=row.submission.contact_email,
            submitterKind=row.submission.submitter_kind,
            processingStatus=row.submission.processing_status,
            externalReference=row.submission.external_reference,
            submittedAt=row.submission.submitted_at,
            triageStatus=row.review_queue_record.triage_status,
            visibilityStatus=row.review_queue_record.visibility_status,
            statusEvents=[
                SubmissionStatusEventRead(
                    eventType=event.event_type,
                    eventReason=event.event_reason,
                    recordedAt=event.recorded_at,
                    correlationId=event.correlation_id,
                )
                for event in row.status_events
            ],
        )
