from __future__ import annotations

from sqlalchemy import select

from app.models import GuideAccessEvent, GuideRenderOutcomeRecord
from app.repositories.user_guide_repository import UserGuideRepository


def test_user_guide_open_records_retrieval_event(app_client, planner_headers, session):
    UserGuideRepository.reset_for_tests()
    response = app_client.get(
        "/api/v1/help/user-guide",
        params={"entryPoint": "app_user_guide_page"},
        headers=planner_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"

    event = session.scalar(select(GuideAccessEvent).where(GuideAccessEvent.guide_access_event_id == body["guideAccessEventId"]))
    assert event is not None
    assert event.entry_point == "app_user_guide_page"
    assert event.outcome == "retrieved"


def test_user_guide_rendered_transition_updates_terminal_outcome(app_client, planner_headers, session):
    UserGuideRepository.reset_for_tests()
    guide = app_client.get(
        "/api/v1/help/user-guide",
        params={"entryPoint": "app_user_guide_page"},
        headers=planner_headers,
    ).json()

    render = app_client.post(
        f"/api/v1/help/user-guide/{guide['guideAccessEventId']}/render-events",
        headers=planner_headers,
        json={"renderOutcome": "rendered"},
    )
    assert render.status_code == 202

    event = session.get(GuideAccessEvent, guide["guideAccessEventId"])
    assert event is not None
    assert event.outcome == "rendered"


def test_user_guide_second_render_event_updates_existing_outcome_record(app_client, planner_headers, session):
    UserGuideRepository.reset_for_tests()
    guide = app_client.get(
        "/api/v1/help/user-guide",
        params={"entryPoint": "app_user_guide_page"},
        headers=planner_headers,
    ).json()

    first = app_client.post(
        f"/api/v1/help/user-guide/{guide['guideAccessEventId']}/render-events",
        headers=planner_headers,
        json={"renderOutcome": "rendered"},
    )
    assert first.status_code == 202

    second = app_client.post(
        f"/api/v1/help/user-guide/{guide['guideAccessEventId']}/render-events",
        headers=planner_headers,
        json={"renderOutcome": "render_failed", "failureMessage": "re-report failure"},
    )
    assert second.status_code == 202

    rows = session.scalars(
        select(GuideRenderOutcomeRecord).where(
            GuideRenderOutcomeRecord.guide_access_event_id == guide["guideAccessEventId"]
        )
    ).all()
    assert len(rows) == 1
    assert rows[0].render_outcome == "render_failed"
    assert rows[0].failure_message == "re-report failure"
