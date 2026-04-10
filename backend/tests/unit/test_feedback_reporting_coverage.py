from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.dependencies import auth as auth_dependencies
from app.clients.issue_tracker_client import (
    IssueTrackerClient,
    IssueTrackerPayload,
    IssueTrackerUnavailableError,
)
from app.core.auth import get_optional_claims, require_planner_or_manager
from app.core.logging import (
    summarize_feedback_error,
    summarize_feedback_success,
    summarize_threshold_alert_failure,
    summarize_threshold_alert_success,
)
from app.models import FeedbackSubmission
from app.repositories.feedback_submission_repository import FeedbackSubmissionRepository
from app.schemas.feedback_submissions import (
    FeedbackSubmissionCreateRequest,
    FeedbackSubmissionDetail,
)
from app.services.feedback_forwarding_service import FeedbackForwardingResult, FeedbackForwardingService
from app.services.feedback_intake_service import FeedbackIntakeService
from app.services.feedback_retry_service import FeedbackRetryService
from app.services.feedback_review_service import FeedbackReviewService


class Creds:
    def __init__(self, token: str) -> None:
        self.credentials = token


class StubLogger:
    def __init__(self) -> None:
        self.infos: list[str] = []
        self.warnings: list[str] = []

    def info(self, message: str, payload: str) -> None:
        self.infos.append(payload)

    def warning(self, message: str, payload: str) -> None:
        self.warnings.append(payload)


class StubForwardingService:
    def __init__(self, results_by_id: dict[str, FeedbackForwardingResult]) -> None:
        self.results_by_id = results_by_id

    def forward_submission(self, submission: FeedbackSubmission, *, correlation_id: str | None):
        return self.results_by_id[submission.feedback_submission_id]


def _set_submission_timestamp(
    repository: FeedbackSubmissionRepository,
    submission_id: str,
    *,
    submitted_at: datetime,
) -> None:
    submission = repository.require_submission(submission_id)
    review_row = repository.require_review_queue_record(submission_id)
    submission.submitted_at = submitted_at
    submission.last_status_at = submitted_at
    review_row.updated_at = submitted_at


def _create_submission(
    repository: FeedbackSubmissionRepository,
    *,
    report_type: str,
    description: str,
    submitted_at: datetime,
    status_event: str | None = None,
) -> FeedbackSubmission:
    submission = repository.create_submission(
        report_type=report_type,
        description=description,
        contact_email=None,
        submitter_kind="anonymous",
        submitter_user_id=None,
        correlation_id="corr-1",
    )
    _set_submission_timestamp(repository, submission.feedback_submission_id, submitted_at=submitted_at)
    if status_event is not None:
        repository.append_status_event(
            feedback_submission_id=submission.feedback_submission_id,
            event_type=status_event,
            event_reason=None,
            correlation_id="corr-1",
            recorded_at=submitted_at + timedelta(minutes=1),
        )
    return submission


@pytest.mark.unit
def test_issue_tracker_client_modes_and_reset() -> None:
    IssueTrackerClient.reset_for_tests()
    client = IssueTrackerClient()
    payload = IssueTrackerPayload(
        report_type="Feedback",
        description="Something broke",
        contact_email="person@example.com",
        submitter_kind="anonymous",
        submitter_user_id=None,
        correlation_id="corr-1",
    )

    ticket = client.submit(payload)
    assert ticket.external_reference == "FB-00001"
    assert IssueTrackerClient.get_records_for_tests() == [payload]

    IssueTrackerClient.set_mode_for_tests("unavailable")
    with pytest.raises(IssueTrackerUnavailableError):
        client.submit(payload)

    IssueTrackerClient.set_mode_for_tests("error")
    with pytest.raises(RuntimeError, match="rejected"):
        client.submit(payload)

    IssueTrackerClient.reset_for_tests()
    assert IssueTrackerClient.get_records_for_tests() == []


@pytest.mark.unit
def test_feedback_schema_normalization_and_validation() -> None:
    request = FeedbackSubmissionCreateRequest(
        reportType="Feedback",
        description="  A helpful note.  ",
        contactEmail="  TEAM@Example.com  ",
    )
    assert request.description == "A helpful note."
    assert request.contact_email == "team@example.com"

    blank_email = FeedbackSubmissionCreateRequest(
        reportType="Bug Report",
        description="The chart froze",
        contactEmail="   ",
    )
    assert blank_email.contact_email is None

    none_email = FeedbackSubmissionCreateRequest(
        reportType="Feedback",
        description="Works fine",
        contactEmail=None,
    )
    assert none_email.contact_email is None

    with pytest.raises(ValidationError):
        FeedbackSubmissionCreateRequest(
            reportType="Feedback",
            description="Still broken",
            contactEmail="not-an-email",
        )

    with pytest.raises(ValidationError):
        FeedbackSubmissionDetail(
            feedbackSubmissionId="fb-1",
            reportType="Feedback",
            description="Needs a timeline",
            contactEmail=None,
            submitterKind="anonymous",
            processingStatus="accepted",
            externalReference=None,
            submittedAt=datetime.now(timezone.utc),
            triageStatus="new",
            visibilityStatus="visible",
            statusEvents=[],
        )


@pytest.mark.unit
def test_feedback_repository_filters_retry_listing_and_lookup_edges(session) -> None:
    repository = FeedbackSubmissionRepository(session)
    base = datetime(2026, 4, 9, 18, 0, tzinfo=timezone.utc)

    forwarded = _create_submission(
        repository,
        report_type="Feedback",
        description="Forward this normally",
        submitted_at=base,
        status_event="forwarded",
    )
    retryable = _create_submission(
        repository,
        report_type="Bug Report",
        description="Retry this later",
        submitted_at=base + timedelta(hours=1),
        status_event="deferred_for_retry",
    )
    hidden = _create_submission(
        repository,
        report_type="Feedback",
        description="Do not show this in the queue",
        submitted_at=base + timedelta(hours=2),
    )
    repository.require_review_queue_record(hidden.feedback_submission_id).visibility_status = "hidden"
    session.commit()

    visible_rows = repository.list_review_rows()
    assert [row.submission.feedback_submission_id for row in visible_rows] == [
        retryable.feedback_submission_id,
        forwarded.feedback_submission_id,
    ]

    filtered_feedback = repository.list_review_rows(report_type="Feedback")
    assert [row.submission.feedback_submission_id for row in filtered_feedback] == [forwarded.feedback_submission_id]

    filtered_retry = repository.list_review_rows(processing_status="deferred_for_retry")
    assert [row.submission.feedback_submission_id for row in filtered_retry] == [retryable.feedback_submission_id]

    submitted_after = repository.list_review_rows(submitted_after=base + timedelta(minutes=30))
    assert [row.submission.feedback_submission_id for row in submitted_after] == [retryable.feedback_submission_id]

    submitted_before = repository.list_review_rows(submitted_before=base + timedelta(minutes=30))
    assert [row.submission.feedback_submission_id for row in submitted_before] == [forwarded.feedback_submission_id]

    detail_row = repository.get_detail_row(forwarded.feedback_submission_id)
    assert detail_row is not None
    assert sorted(event.event_type for event in detail_row.status_events) == ["accepted", "forwarded"]
    assert repository.get_detail_row("missing") is None

    retry_rows = repository.list_submissions_for_retry(limit=1)
    assert [submission.feedback_submission_id for submission in retry_rows] == [retryable.feedback_submission_id]

    with pytest.raises(LookupError, match="submission not found"):
        repository.require_submission("missing")

    with pytest.raises(LookupError, match="review queue record not found"):
        repository.require_review_queue_record("missing")


@pytest.mark.unit
def test_feedback_review_service_returns_none_for_missing_submission(session) -> None:
    service = FeedbackReviewService(FeedbackSubmissionRepository(session))
    assert service.get_submission("missing") is None


@pytest.mark.unit
def test_feedback_forwarding_service_handles_generic_client_errors() -> None:
    class ExplodingClient:
        def submit(self, payload):
            raise RuntimeError("tracker rejected the record")

    service = FeedbackForwardingService(client=ExplodingClient())
    submission = FeedbackSubmission(
        feedback_submission_id="fb-1",
        report_type="Bug Report",
        description="Chart does not load",
        contact_email=None,
        submitter_kind="anonymous",
        submitter_user_id=None,
        processing_status="accepted",
        submitted_at=datetime.now(timezone.utc),
        last_status_at=datetime.now(timezone.utc),
    )

    result = service.forward_submission(submission, correlation_id="corr-7")

    assert result.event_type == "forward_failed"
    assert result.user_outcome == "accepted_with_delay"
    assert result.event_reason == "tracker rejected the record"


@pytest.mark.unit
def test_feedback_intake_service_marks_authenticated_submitter_without_subject(session) -> None:
    repository = FeedbackSubmissionRepository(session)
    logger = StubLogger()

    class SuccessfulForwarder:
        def forward_submission(self, submission: FeedbackSubmission, *, correlation_id: str | None):
            return FeedbackForwardingResult(
                event_type="forwarded",
                user_outcome="accepted",
                status_message="Recorded",
                external_reference="FB-11111",
            )

    service = FeedbackIntakeService(
        repository=repository,
        forwarding_service=SuccessfulForwarder(),
        logger=logger,
    )

    result = service.submit_feedback(
        FeedbackSubmissionCreateRequest(
            reportType="Feedback",
            description="  Missing subject claim should still be authenticated.  ",
            contactEmail=None,
        ),
        claims={"sub": 123, "roles": ["CityPlanner"]},
        correlation_id="corr-12",
    )

    saved = repository.require_submission(result.feedback_submission_id)
    assert saved.submitter_kind == "authenticated"
    assert saved.submitter_user_id is None
    assert saved.external_reference == "FB-11111"
    assert logger.infos


@pytest.mark.unit
def test_feedback_retry_service_handles_forwarded_and_failed_retries(session) -> None:
    repository = FeedbackSubmissionRepository(session)
    logger = StubLogger()
    base = datetime(2026, 4, 9, 18, 0, tzinfo=timezone.utc)

    forwarded = _create_submission(
        repository,
        report_type="Feedback",
        description="Forward me now",
        submitted_at=base,
        status_event="deferred_for_retry",
    )
    failed = _create_submission(
        repository,
        report_type="Bug Report",
        description="Still failing",
        submitted_at=base + timedelta(hours=1),
        status_event="deferred_for_retry",
    )
    session.commit()

    service = FeedbackRetryService(
        repository=repository,
        forwarding_service=StubForwardingService(
            {
                forwarded.feedback_submission_id: FeedbackForwardingResult(
                    event_type="forwarded",
                    user_outcome="accepted",
                    status_message="Forwarded",
                    external_reference="FB-22222",
                ),
                failed.feedback_submission_id: FeedbackForwardingResult(
                    event_type="forward_failed",
                    user_outcome="accepted_with_delay",
                    status_message="Still local only",
                    event_reason="tracker offline",
                ),
            }
        ),
        logger=logger,
    )

    retried = service.retry_deferred_submissions(limit=10)

    assert retried == [forwarded.feedback_submission_id, failed.feedback_submission_id]
    assert repository.require_submission(forwarded.feedback_submission_id).external_reference == "FB-22222"
    assert repository.require_submission(forwarded.feedback_submission_id).processing_status == "forwarded"
    assert repository.require_submission(failed.feedback_submission_id).processing_status == "forward_failed"
    assert logger.infos
    assert logger.warnings


@pytest.mark.unit
def test_feedback_routes_cover_passthrough_500_and_missing_detail(monkeypatch, app_client, planner_headers) -> None:
    class PassthroughService:
        def submit_feedback(self, payload, *, claims, correlation_id):
            raise HTTPException(status_code=418, detail="Short and stout")

    class ExplodingService:
        def submit_feedback(self, payload, *, claims, correlation_id):
            raise RuntimeError("unexpected boom")

    monkeypatch.setattr(
        "app.api.routes.feedback_submissions.build_feedback_intake_service",
        lambda session: PassthroughService(),
    )
    passthrough = app_client.post(
        "/api/v1/feedback-submissions",
        json={
            "reportType": "Feedback",
            "description": "Raise the original HTTP exception.",
        },
    )
    assert passthrough.status_code == 418
    assert passthrough.json()["detail"] == "Short and stout"

    monkeypatch.setattr(
        "app.api.routes.feedback_submissions.build_feedback_intake_service",
        lambda session: ExplodingService(),
    )
    exploded = app_client.post(
        "/api/v1/feedback-submissions",
        json={
            "reportType": "Bug Report",
            "description": "Raise the generic error path.",
        },
    )
    assert exploded.status_code == 500
    assert exploded.json()["detail"] == "Feedback submission failed. Please try again."

    missing = app_client.get("/api/v1/feedback-submissions/missing-id", headers=planner_headers)
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Feedback submission not found"


@pytest.mark.unit
def test_feedback_logging_auth_and_model_exports(monkeypatch) -> None:
    assert summarize_feedback_success("feedback.forwarded", correlation_id="abc")["outcome"] == "success"
    assert summarize_feedback_error("feedback.failed", correlation_id="abc")["outcome"] == "error"
    assert summarize_threshold_alert_success("threshold.sent", configuration_id="cfg")["outcome"] == "success"
    assert summarize_threshold_alert_failure("threshold.failed", configuration_id="cfg")["outcome"] == "failure"

    assert get_optional_claims(None) is None

    monkeypatch.setattr("app.core.auth._decode_jwt_payload", lambda token: {"token_type": "refresh"})
    with pytest.raises(HTTPException, match="Invalid token"):
        get_optional_claims(Creds("bad-token"))

    assert auth_dependencies.require_feedback_review_reader is require_planner_or_manager

    models_module = importlib.import_module("app.models")
    repository_models = importlib.import_module("app.repositories.models")
    assert "SubmissionStatusEvent" in models_module.__all__
    assert "ThresholdConfiguration" in models_module.__all__
    assert "SubmissionStatusEvent" in repository_models.__all__
    assert "ThresholdConfiguration" in repository_models.__all__
