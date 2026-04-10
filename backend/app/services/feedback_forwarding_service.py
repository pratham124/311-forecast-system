from __future__ import annotations

from dataclasses import dataclass

from app.clients.issue_tracker_client import IssueTrackerClient, IssueTrackerPayload, IssueTrackerUnavailableError
from app.models import FeedbackSubmission


@dataclass(slots=True)
class FeedbackForwardingResult:
    event_type: str
    user_outcome: str
    status_message: str
    external_reference: str | None = None
    event_reason: str | None = None


class FeedbackForwardingService:
    def __init__(self, client: IssueTrackerClient | None = None) -> None:
        self.client = client or IssueTrackerClient()

    def forward_submission(
        self,
        submission: FeedbackSubmission,
        *,
        correlation_id: str | None,
    ) -> FeedbackForwardingResult:
        payload = IssueTrackerPayload(
            report_type=submission.report_type,
            description=submission.description,
            contact_email=submission.contact_email,
            submitter_kind=submission.submitter_kind,
            submitter_user_id=submission.submitter_user_id,
            correlation_id=correlation_id,
        )
        try:
            ticket = self.client.submit(payload)
        except IssueTrackerUnavailableError as exc:
            return FeedbackForwardingResult(
                event_type="deferred_for_retry",
                user_outcome="accepted_with_delay",
                status_message="Your report was received and saved. Developer review may be delayed while the issue tracker recovers.",
                event_reason=str(exc),
            )
        except Exception as exc:
            return FeedbackForwardingResult(
                event_type="forward_failed",
                user_outcome="accepted_with_delay",
                status_message="Your report was received and saved, but automatic forwarding failed. The team can still review it locally.",
                event_reason=str(exc),
            )
        return FeedbackForwardingResult(
            event_type="forwarded",
            user_outcome="accepted",
            status_message="Your report was received, recorded, and forwarded for team review.",
            external_reference=ticket.external_reference,
        )
