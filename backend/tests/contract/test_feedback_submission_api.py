from __future__ import annotations

import pytest

from app.clients.issue_tracker_client import IssueTrackerClient


@pytest.fixture(autouse=True)
def reset_issue_tracker_client():
    IssueTrackerClient.reset_for_tests()
    yield
    IssueTrackerClient.reset_for_tests()


def test_feedback_submission_contract_allows_anonymous_create_and_reviewer_reads(app_client, planner_headers):
    create = app_client.post(
        "/api/v1/feedback-submissions",
        json={
            "reportType": "Bug Report",
            "description": "The forecast chart fails when I switch service categories.",
        },
    )
    assert create.status_code == 201
    body = create.json()
    assert body["reportType"] == "Bug Report"
    assert body["processingStatus"] == "forwarded"
    assert body["userOutcome"] == "accepted"
    assert "statusMessage" in body

    forwarded = IssueTrackerClient.get_records_for_tests()
    assert len(forwarded) == 1
    assert forwarded[0].submitter_kind == "anonymous"

    listing = app_client.get("/api/v1/feedback-submissions", headers=planner_headers)
    assert listing.status_code == 200
    assert listing.json()["items"][0]["feedbackSubmissionId"] == body["feedbackSubmissionId"]

    detail = app_client.get(f"/api/v1/feedback-submissions/{body['feedbackSubmissionId']}", headers=planner_headers)
    assert detail.status_code == 200
    assert detail.json()["statusEvents"][0]["eventType"] == "accepted"

    unauthorized = app_client.get("/api/v1/feedback-submissions")
    assert unauthorized.status_code == 401


def test_feedback_submission_contract_supports_delayed_processing_and_validation_errors(
    app_client,
    operational_manager_headers,
):
    IssueTrackerClient.set_mode_for_tests("unavailable")
    delayed = app_client.post(
        "/api/v1/feedback-submissions",
        headers=operational_manager_headers,
        json={
            "reportType": "Feedback",
            "description": "A delayed-forwarding path should still save the report.",
            "contactEmail": "manager@example.com",
        },
    )
    assert delayed.status_code == 201
    delayed_body = delayed.json()
    assert delayed_body["processingStatus"] == "deferred_for_retry"
    assert delayed_body["userOutcome"] == "accepted_with_delay"

    review = app_client.get(
        f"/api/v1/feedback-submissions/{delayed_body['feedbackSubmissionId']}",
        headers=operational_manager_headers,
    )
    assert review.status_code == 200
    assert review.json()["submitterKind"] == "authenticated"

    invalid = app_client.post(
        "/api/v1/feedback-submissions",
        json={
            "reportType": "Feedback",
            "description": "   ",
            "contactEmail": "not-an-email",
        },
    )
    assert invalid.status_code == 422
