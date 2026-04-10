from __future__ import annotations

import logging

from app.core.logging import summarize_feedback_error, summarize_feedback_success
from app.repositories.feedback_submission_repository import FeedbackSubmissionRepository
from app.services.feedback_forwarding_service import FeedbackForwardingService


class FeedbackRetryService:
    def __init__(
        self,
        *,
        repository: FeedbackSubmissionRepository,
        forwarding_service: FeedbackForwardingService,
        logger: logging.Logger | None = None,
    ) -> None:
        self.repository = repository
        self.forwarding_service = forwarding_service
        self.logger = logger or logging.getLogger("feedback.retry")

    def retry_deferred_submissions(self, *, limit: int = 50) -> list[str]:
        retried_ids: list[str] = []
        for submission in self.repository.list_submissions_for_retry(limit=limit):
            result = self.forwarding_service.forward_submission(submission, correlation_id=None)
            if result.external_reference:
                self.repository.set_external_reference(submission.feedback_submission_id, result.external_reference)
            self.repository.append_status_event(
                feedback_submission_id=submission.feedback_submission_id,
                event_type=result.event_type,
                event_reason=result.event_reason,
                correlation_id=None,
            )
            retried_ids.append(submission.feedback_submission_id)
            if result.event_type == "forwarded":
                self.logger.info(
                    "%s",
                    summarize_feedback_success(
                        "feedback.retry_forwarded",
                        feedback_submission_id=submission.feedback_submission_id,
                        external_reference=result.external_reference,
                    ),
                )
            else:
                self.logger.warning(
                    "%s",
                    summarize_feedback_error(
                        "feedback.retry_failed",
                        feedback_submission_id=submission.feedback_submission_id,
                        processing_status=result.event_type,
                        failure_reason=result.event_reason,
                    ),
                )
        return retried_ids
