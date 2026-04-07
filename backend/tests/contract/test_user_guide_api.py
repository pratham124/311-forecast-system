from __future__ import annotations

from app.repositories.user_guide_repository import UserGuideRepository


def test_get_user_guide_success_and_auth(app_client, planner_headers):
    UserGuideRepository.reset_for_tests()
    response = app_client.get(
        "/api/v1/help/user-guide",
        params={"entryPoint": "app_user_guide_page"},
        headers=planner_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"
    assert body["title"] == "Operations Analytics User Guide"
    assert len(body["sections"]) >= 1

    unauthenticated = app_client.get("/api/v1/help/user-guide", params={"entryPoint": "app_user_guide_page"})
    assert unauthenticated.status_code == 401


def test_get_user_guide_unavailable_and_render_event_contract(app_client, operational_manager_headers):
    UserGuideRepository.set_source_for_tests(None)
    unavailable = app_client.get(
        "/api/v1/help/user-guide",
        params={"entryPoint": "app_user_guide_page"},
        headers=operational_manager_headers,
    )
    assert unavailable.status_code == 200
    assert unavailable.json()["status"] == "unavailable"

    UserGuideRepository.reset_for_tests()
    guide = app_client.get(
        "/api/v1/help/user-guide",
        params={"entryPoint": "app_user_guide_page"},
        headers=operational_manager_headers,
    ).json()
    render = app_client.post(
        f"/api/v1/help/user-guide/{guide['guideAccessEventId']}/render-events",
        headers=operational_manager_headers,
        json={"renderOutcome": "render_failed", "failureMessage": "Renderer crashed"},
    )
    assert render.status_code == 202

    missing = app_client.post(
        "/api/v1/help/user-guide/missing/render-events",
        headers=operational_manager_headers,
        json={"renderOutcome": "rendered"},
    )
    assert missing.status_code == 404


def test_post_user_guide_render_event_returns_409_when_access_event_not_eligible(app_client, operational_manager_headers):
    UserGuideRepository.set_source_for_tests(None)
    try:
        guide = app_client.get(
            "/api/v1/help/user-guide",
            params={"entryPoint": "app_user_guide_page"},
            headers=operational_manager_headers,
        ).json()
        assert guide["status"] == "unavailable"
        conflict = app_client.post(
            f"/api/v1/help/user-guide/{guide['guideAccessEventId']}/render-events",
            headers=operational_manager_headers,
            json={"renderOutcome": "rendered"},
        )
        assert conflict.status_code == 409
    finally:
        UserGuideRepository.reset_for_tests()
