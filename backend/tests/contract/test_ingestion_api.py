from __future__ import annotations

import logging

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.api.routes.ingestion import (
    get_current_dataset,
    get_run_status,
    list_failure_notifications,
    trigger_ingestion,
)
from app.clients.edmonton_311 import Edmonton311Client
from app.core.auth import get_current_claims, require_operational_manager, require_planner_or_manager
from app.services.ingestion_logging_service import IngestionLoggingService
from tests.conftest import FakeTransport, build_token


class Creds:
    def __init__(self, token: str) -> None:
        self.credentials = token


def _run_background_tasks(tasks: BackgroundTasks) -> None:
    for task in tasks.tasks:
        task.func(*task.args, **task.kwargs)


@pytest.mark.contract
def test_trigger_requires_operational_manager_role() -> None:
    claims = get_current_claims(Creds(build_token(["Viewer"])))
    with pytest.raises(HTTPException) as exc:
        require_operational_manager(claims)
    assert exc.value.status_code == 403


@pytest.mark.contract
def test_trigger_accepts_operational_manager(session) -> None:
    background_tasks = BackgroundTasks()
    response = trigger_ingestion(
        background_tasks=background_tasks,
        session=session,
        client=Edmonton311Client(FakeTransport("new_data")),
        _claims={"roles": ["OperationalManager"]},
    )
    assert response.status == "running"
    _run_background_tasks(background_tasks)


@pytest.mark.contract
def test_run_status_and_current_dataset_endpoints_are_readable(session, planner_headers, seed_current_dataset) -> None:
    background_tasks = BackgroundTasks()
    trigger = trigger_ingestion(
        background_tasks=background_tasks,
        session=session,
        client=Edmonton311Client(FakeTransport("new_data")),
        _claims={"roles": ["OperationalManager"]},
    )
    _run_background_tasks(background_tasks)

    run_response = get_run_status(trigger.run_id, session=session, _claims={"roles": ["CityPlanner"]})
    current_response = get_current_dataset(session=session, _claims={"roles": ["CityPlanner"]})

    assert run_response.run_id == trigger.run_id
    assert current_response.source_name == "edmonton_311"


@pytest.mark.contract
def test_failure_notification_query_returns_summary_only(session, seed_current_dataset) -> None:
    background_tasks = BackgroundTasks()
    trigger = trigger_ingestion(
        background_tasks=background_tasks,
        session=session,
        client=Edmonton311Client(FakeTransport("auth_failure")),
        _claims={"roles": ["OperationalManager"]},
    )
    _run_background_tasks(background_tasks)

    response = list_failure_notifications(
        run_id=trigger.run_id,
        session=session,
        _claims={"roles": ["CityPlanner"]},
    )

    assert len(response.items) == 1
    assert response.items[0].run_id == trigger.run_id
    assert "invalid credentials" in response.items[0].message


@pytest.mark.contract
def test_operational_manager_headers_fixture_builds_bearer_token(operational_manager_headers) -> None:
    assert operational_manager_headers["Authorization"].startswith("Bearer ")


@pytest.mark.contract
def test_viewer_headers_fixture_builds_bearer_token(viewer_headers) -> None:
    assert viewer_headers["Authorization"].startswith("Bearer ")
