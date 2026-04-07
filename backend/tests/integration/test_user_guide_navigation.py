from __future__ import annotations

from app.repositories.user_guide_repository import UserGuideRepository


def test_user_guide_sections_are_ordered_for_repeat_navigation(app_client, operational_manager_headers):
    UserGuideRepository.reset_for_tests()
    response = app_client.get(
        "/api/v1/help/user-guide",
        params={"entryPoint": "app_user_guide_page"},
        headers=operational_manager_headers,
    )
    assert response.status_code == 200
    sections = response.json()["sections"]
    assert [section["orderIndex"] for section in sections] == sorted(section["orderIndex"] for section in sections)
