from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.core.auth import get_current_claims, require_operational_manager, require_planner_or_manager
from tests.conftest import build_token


class Creds:
    def __init__(self, token: str) -> None:
        self.credentials = token


@pytest.mark.unit
def test_operational_manager_role_allowed() -> None:
    claims = get_current_claims(Creds(build_token(["OperationalManager"])))
    resolved = require_operational_manager(claims)
    assert "OperationalManager" in resolved["roles"]


@pytest.mark.unit
def test_city_planner_cannot_trigger_manager_only_endpoint() -> None:
    claims = get_current_claims(Creds(build_token(["CityPlanner"])))
    with pytest.raises(HTTPException) as exc:
        require_operational_manager(claims)
    assert exc.value.status_code == 403


@pytest.mark.unit
def test_city_planner_can_access_read_surfaces() -> None:
    claims = get_current_claims(Creds(build_token(["CityPlanner"])))
    resolved = require_planner_or_manager(claims)
    assert "CityPlanner" in resolved["roles"]


@pytest.mark.unit
def test_expired_token_is_rejected() -> None:
    with pytest.raises(HTTPException) as exc:
        get_current_claims(Creds(build_token(["OperationalManager"], expires_in_seconds=-60)))
    assert exc.value.status_code == 401
