from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.clients.issue_tracker_client import IssueTrackerClient
from app.models import FeedbackSubmission, ReviewQueueRecord, SubmissionStatusEvent
from app.repositories.feedback_submission_repository import FeedbackSubmissionRepository


@pytest.fixture(autouse=True)
def reset_issue_tracker_client():
    IssueTrackerClient.reset_for_tests()
    yield
    IssueTrackerClient.reset_for_tests()


def test_feedback_submission_success_persists_submission_queue_and_status_history(app_client, planner_headers, session):
    response = app_client.post(
        "/api/v1/feedback-submissions",
        headers=planner_headers,
        json={
            "reportType": "Bug Report",
            "description": "The review queue should persist successful submissions.",
            "contactEmail": "planner@example.com",
        },
    )
    assert response.status_code == 201
    body = response.json()

    submission = session.get(FeedbackSubmission, body["feedbackSubmissionId"])
    assert submission is not None
    assert submission.submitter_kind == "authenticated"
    assert submission.submitter_user_id == "test-user"
    assert submission.external_reference == "FB-00001"

    review_row = session.scalar(
        select(ReviewQueueRecord).where(
            ReviewQueueRecord.feedback_submission_id == body["feedbackSubmissionId"]
        )
    )
    assert review_row is not None
    assert review_row.triage_status == "new"

    events = session.scalars(
        select(SubmissionStatusEvent)
        .where(SubmissionStatusEvent.feedback_submission_id == body["feedbackSubmissionId"])
        .order_by(SubmissionStatusEvent.recorded_at.asc(), SubmissionStatusEvent.submission_status_event_id.asc())
    ).all()
    assert [event.event_type for event in events] == ["accepted", "forwarded"]


def test_feedback_submission_unavailable_issue_tracker_retains_retryable_submission(app_client, session):
    IssueTrackerClient.set_mode_for_tests("unavailable")
    response = app_client.post(
        "/api/v1/feedback-submissions",
        json={
            "reportType": "Feedback",
            "description": "Keep this report locally when the issue tracker is down.",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["processingStatus"] == "deferred_for_retry"

    submission = session.get(FeedbackSubmission, body["feedbackSubmissionId"])
    assert submission is not None
    assert submission.processing_status == "deferred_for_retry"

    events = session.scalars(
        select(SubmissionStatusEvent)
        .where(SubmissionStatusEvent.feedback_submission_id == body["feedbackSubmissionId"])
        .order_by(SubmissionStatusEvent.recorded_at.asc(), SubmissionStatusEvent.submission_status_event_id.asc())
    ).all()
    assert [event.event_type for event in events] == ["accepted", "deferred_for_retry"]


def test_feedback_submission_storage_failure_returns_503_after_forwarding(monkeypatch, app_client, session):
    original_append_status_event = FeedbackSubmissionRepository.append_status_event

    def failing_append_status_event(self, *, feedback_submission_id, event_type, event_reason, correlation_id, recorded_at=None):
        if event_type != "accepted":
            raise SQLAlchemyError("database write failed")
        return original_append_status_event(
            self,
            feedback_submission_id=feedback_submission_id,
            event_type=event_type,
            event_reason=event_reason,
            correlation_id=correlation_id,
            recorded_at=recorded_at,
        )

    monkeypatch.setattr(FeedbackSubmissionRepository, "append_status_event", failing_append_status_event)

    response = app_client.post(
        "/api/v1/feedback-submissions",
        json={
            "reportType": "Bug Report",
            "description": "Forwarding succeeds before local persistence fails.",
        },
    )
    assert response.status_code == 503
    assert "could not be fully recorded" in response.json()["detail"].lower()
    assert len(IssueTrackerClient.get_records_for_tests()) == 1
    assert session.scalar(select(FeedbackSubmission)) is None
