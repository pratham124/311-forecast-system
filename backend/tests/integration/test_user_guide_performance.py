from __future__ import annotations

from time import perf_counter

from app.repositories.user_guide_repository import UserGuideRepository


def test_user_guide_open_completes_within_latency_target(app_client, planner_headers):
    UserGuideRepository.reset_for_tests()
    started = perf_counter()
    response = app_client.get(
        "/api/v1/help/user-guide",
        params={"entryPoint": "app_user_guide_page"},
        headers=planner_headers,
    )
    duration = perf_counter() - started

    assert response.status_code == 200
    assert duration < 10
