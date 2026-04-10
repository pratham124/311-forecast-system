from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.core.logging import summarize_feedback_error, summarize_feedback_event, summarize_feedback_success
from app.repositories.feedback_submission_repository import FeedbackSubmissionRepository
from app.schemas.feedback_submissions import FeedbackSubmissionCreateRequest, FeedbackSubmissionCreateResponse
from app.services.feedback_forwarding_service import FeedbackForwardingService


@dataclass(slots=True)
class FeedbackIntakeResult:
    response: FeedbackSubmissionCreateResponse
    feedback_submission_id: str


class FeedbackIntakeService:
    def __init__(
        self,
        *,
        repository: FeedbackSubmissionRepository,
        forwarding_service: FeedbackForwardingService,
        logger: logging.Logger | None = None,
    ) -> None:
        self.repository = repository
        self.forwarding_service = forwarding_service
        self.logger = logger or logging.getLogger("feedback.intake")

    def submit_feedback(
        self,
        payload: FeedbackSubmissionCreateRequest,
        *,
        claims: dict[str, Any] | None,
        correlation_id: str | None = None,
    ) -> FeedbackIntakeResult:
        submitter_user_id = None
        submitter_kind = "anonymous"
        if claims is not None:
            submitter_kind = "authenticated"
            subject = claims.get("sub")
            if isinstance(subject, str) and subject:
                submitter_user_id = subject

        submission = self.repository.create_submission(
            report_type=payload.report_type,
            description=payload.description,
            contact_email=payload.contact_email,
            submitter_kind=submitter_kind,
            submitter_user_id=submitter_user_id,
            correlation_id=correlation_id,
        )
        self.logger.info(
            "%s",
            summarize_feedback_event(
                "feedback.submission_accepted",
                feedback_submission_id=submission.feedback_submission_id,
                report_type=submission.report_type,
                submitter_kind=submission.submitter_kind,
                correlation_id=correlation_id,
            ),
        )

        forwarding_result = self.forwarding_service.forward_submission(submission, correlation_id=correlation_id)
        if forwarding_result.external_reference:
            self.repository.set_external_reference(submission.feedback_submission_id, forwarding_result.external_reference)

        self.repository.append_status_event(
            feedback_submission_id=submission.feedback_submission_id,
            event_type=forwarding_result.event_type,
            event_reason=forwarding_result.event_reason,
            correlation_id=correlation_id,
        )

        if forwarding_result.event_type == "forwarded":
            self.logger.info(
                "%s",
                summarize_feedback_success(
                    "feedback.submission_forwarded",
                    feedback_submission_id=submission.feedback_submission_id,
                    external_reference=forwarding_result.external_reference,
                    correlation_id=correlation_id,
                ),
            )
        else:
            self.logger.warning(
                "%s",
                summarize_feedback_error(
                    "feedback.submission_forwarding_delayed",
                    feedback_submission_id=submission.feedback_submission_id,
                    processing_status=forwarding_result.event_type,
                    failure_reason=forwarding_result.event_reason,
                    correlation_id=correlation_id,
                ),
            )

        final_submission = self.repository.require_submission(submission.feedback_submission_id)
        response = FeedbackSubmissionCreateResponse(
            feedbackSubmissionId=final_submission.feedback_submission_id,
            reportType=final_submission.report_type,
            processingStatus=final_submission.processing_status,
            acceptedAt=final_submission.submitted_at,
            userOutcome=forwarding_result.user_outcome,
            statusMessage=forwarding_result.status_message,
        )
        return FeedbackIntakeResult(
            response=response,
            feedback_submission_id=final_submission.feedback_submission_id,
        )
