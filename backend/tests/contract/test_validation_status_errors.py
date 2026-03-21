from __future__ import annotations

import pytest


@pytest.mark.contract
def test_validation_status_surfaces_auth_errors(app_client, viewer_headers) -> None:
    missing = app_client.get("/api/v1/validation-runs/00000000-0000-0000-0000-000000000000")
    forbidden = app_client.get("/api/v1/validation-runs/00000000-0000-0000-0000-000000000000", headers=viewer_headers)

    assert missing.status_code == 401
    assert forbidden.status_code == 403


@pytest.mark.contract
def test_validation_status_surfaces_not_found_and_invalid_id(app_client, planner_headers) -> None:
    not_found = app_client.get("/api/v1/validation-runs/00000000-0000-0000-0000-000000000000", headers=planner_headers)
    invalid = app_client.get("/api/v1/validation-runs/not-a-uuid", headers=planner_headers)

    assert not_found.status_code == 404
    assert invalid.status_code == 422
