from __future__ import annotations

from sqlalchemy import select

from app.models import GuideAccessEvent, GuideRenderOutcomeRecord
from app.repositories.user_guide_repository import UserGuideRepository


def test_user_guide_retrieval_failure_records_failure_event(app_client, planner_headers, session):
    UserGuideRepository.set_source_for_tests(None)
    response = app_client.get(
        "/api/v1/help/user-guide",
        params={"entryPoint": "app_user_guide_page"},
        headers=planner_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unavailable"

    event = session.scalar(select(GuideAccessEvent).where(GuideAccessEvent.guide_access_event_id == body["guideAccessEventId"]))
    assert event is not None
    assert event.outcome == "retrieval_failed"
    assert event.failure_category == "guide_unavailable"


def test_user_guide_render_failure_records_render_outcome(app_client, planner_headers, session):
    UserGuideRepository.reset_for_tests()
    guide = app_client.get(
        "/api/v1/help/user-guide",
        params={"entryPoint": "app_user_guide_page"},
        headers=planner_headers,
    ).json()
    response = app_client.post(
        f"/api/v1/help/user-guide/{guide['guideAccessEventId']}/render-events",
        headers=planner_headers,
        json={"renderOutcome": "render_failed", "failureMessage": "Unable to render markdown"},
    )
    assert response.status_code == 202

    event = session.get(GuideAccessEvent, guide["guideAccessEventId"])
    render_record = session.scalar(
        select(GuideRenderOutcomeRecord).where(GuideRenderOutcomeRecord.guide_access_event_id == guide["guideAccessEventId"])
    )
    assert event is not None
    assert event.outcome == "render_failed"
    assert render_record is not None
    assert render_record.render_outcome == "render_failed"
