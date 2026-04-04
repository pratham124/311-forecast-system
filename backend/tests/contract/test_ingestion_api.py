from __future__ import annotations

import logging

import pytest
from fastapi import BackgroundTasks, HTTPException

import app.api.routes.ingestion as ingestion_routes
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
    assert current_response.latest_requested_at is not None


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


@pytest.mark.contract
def test_trigger_background_failure_path_finalizes_unexpected_error(session, monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    class FakeSession:
        def commit(self) -> None:
            events.append("background_commit")

        def rollback(self) -> None:
            events.append("background_rollback")

        def close(self) -> None:
            events.append("background_close")

    class FakePipeline:
        def __init__(self, session, client, logging_service) -> None:
            self.session = session

        def start_run(self, trigger_type: str = "scheduled"):
            return "run-1", "cursor-1", None

        def run(self, **kwargs):
            raise RuntimeError("boom")

        def fail_unexpected_run(self, run_id: str, reason: str, previous_marker):
            events.append(f"finalized:{run_id}:{reason}")
            return None

    monkeypatch.setattr(ingestion_routes, "IngestionPipeline", FakePipeline)
    monkeypatch.setattr(ingestion_routes, "get_session_factory", lambda: lambda: FakeSession())

    background_tasks = BackgroundTasks()
    response = trigger_ingestion(
        background_tasks=background_tasks,
        session=session,
        client=Edmonton311Client(FakeTransport("new_data")),
        _claims={"roles": ["OperationalManager"]},
    )
    _run_background_tasks(background_tasks)

    assert response.run_id == "run-1"
    assert "background_rollback" in events
    assert "background_commit" in events
    assert "background_close" in events
    assert any(item.startswith("finalized:run-1:boom") for item in events)


@pytest.mark.contract
def test_trigger_background_failure_path_logs_finalize_failure(session, monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    class FakeSession:
        def commit(self) -> None:
            events.append("background_commit")

        def rollback(self) -> None:
            events.append("background_rollback")

        def close(self) -> None:
            events.append("background_close")

    class FakePipeline:
        def __init__(self, session, client, logging_service) -> None:
            pass

        def start_run(self, trigger_type: str = "scheduled"):
            return "run-2", None, None

        def run(self, **kwargs):
            raise RuntimeError("boom")

        def fail_unexpected_run(self, run_id: str, reason: str, previous_marker):
            raise RuntimeError("cannot finalize")

    class FakeLogger:
        def info(self, *args, **kwargs) -> None:
            return None

        def exception(self, message, *args, **kwargs) -> None:
            events.append(message)

    monkeypatch.setattr(ingestion_routes, "IngestionPipeline", FakePipeline)
    monkeypatch.setattr(ingestion_routes, "get_session_factory", lambda: lambda: FakeSession())
    monkeypatch.setattr(ingestion_routes, "logging", type("FakeLogging", (), {"getLogger": staticmethod(lambda name=None: FakeLogger())})())

    background_tasks = BackgroundTasks()
    trigger_ingestion(
        background_tasks=background_tasks,
        session=session,
        client=Edmonton311Client(FakeTransport("new_data")),
        _claims={"roles": ["OperationalManager"]},
    )
    _run_background_tasks(background_tasks)

    assert events.count("ingestion.background_task.failed run_id=%s") == 1
    assert events.count("ingestion.background_task.fail_finalize_failed run_id=%s") == 1
    assert events.count("background_close") == 1
