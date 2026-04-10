from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks, HTTPException, Response

from app.api.routes import forecast_alerts as forecast_alerts_route
from app.api.routes import weather_overlay as weather_overlay_route


def _run_background_tasks(tasks: BackgroundTasks) -> None:
    for task in tasks.tasks:
        task.func(*task.args, **task.kwargs)


@pytest.mark.unit
def test_forecast_alert_route_not_found_paths(session) -> None:
    payload = SimpleNamespace(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=10,
        notification_channels=["dashboard"],
    )

    with pytest.raises(HTTPException) as update_exc:
        forecast_alerts_route.update_threshold_configuration(
            "missing-threshold",
            background_tasks=BackgroundTasks(),
            payload=payload,
            session=session,
            _claims={"roles": ["OperationalManager"]},
        )
    assert update_exc.value.status_code == 404

    with pytest.raises(HTTPException) as delete_exc:
        forecast_alerts_route.delete_threshold_configuration(
            "missing-threshold",
            session=session,
            _claims={"roles": ["OperationalManager"]},
        )
    assert delete_exc.value.status_code == 404


@pytest.mark.unit
def test_schedule_recheck_covers_hourly_weekly_and_failure_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[tuple[str, object]] = []

    class FakeSession:
        def commit(self) -> None:
            events.append(("commit", None))

        def rollback(self) -> None:
            events.append(("rollback", None))

        def close(self) -> None:
            events.append(("close", None))

    session_factory = lambda: FakeSession()
    monkeypatch.setattr(forecast_alerts_route, "get_session_factory", lambda: session_factory)
    monkeypatch.setattr(
        forecast_alerts_route,
        "get_settings",
        lambda: SimpleNamespace(
            forecast_product_name="daily-product",
            weekly_forecast_product_name="weekly-product",
        ),
    )

    class FakeForecastRepository:
        def __init__(self, session) -> None:
            self.session = session

        def get_current_marker(self, product_name):
            events.append(("hourly-marker", product_name))
            return SimpleNamespace(forecast_version_id="daily-version")

    class FakeWeeklyForecastRepository:
        def __init__(self, session) -> None:
            self.session = session

        def get_current_marker(self, product_name):
            events.append(("weekly-marker", product_name))
            return SimpleNamespace(weekly_forecast_version_id="weekly-version")

    def fake_run_threshold_alert_evaluation(session, **kwargs):
        events.append(("run", kwargs))
        if kwargs["forecast_product"] == "weekly":
            raise RuntimeError("boom")
        return SimpleNamespace(threshold_evaluation_run_id="run-1")

    warnings: list[str] = []
    monkeypatch.setattr(forecast_alerts_route, "ForecastRepository", FakeForecastRepository)
    monkeypatch.setattr(forecast_alerts_route, "WeeklyForecastRepository", FakeWeeklyForecastRepository)
    monkeypatch.setattr(forecast_alerts_route, "run_threshold_alert_evaluation", fake_run_threshold_alert_evaluation)
    monkeypatch.setattr(forecast_alerts_route.logger, "warning", lambda message, *args: warnings.append(message % args))

    hourly_tasks = BackgroundTasks()
    forecast_alerts_route._schedule_recheck(
        hourly_tasks,
        "hourly",
        trigger_source="manual_replay",
        service_category="Roads",
    )
    _run_background_tasks(hourly_tasks)

    weekly_tasks = BackgroundTasks()
    forecast_alerts_route._schedule_recheck(
        weekly_tasks,
        "daily",
        trigger_source="manual_replay",
        service_category="Waste",
    )
    _run_background_tasks(weekly_tasks)

    hourly_run = next(item for kind, item in events if kind == "run" and item["forecast_product"] == "daily")
    weekly_run = next(item for kind, item in events if kind == "run" and item["forecast_product"] == "weekly")

    assert hourly_run["forecast_reference_id"] == "daily-version"
    assert hourly_run["service_category"] == "Roads"
    assert weekly_run["forecast_reference_id"] == "weekly-version"
    assert weekly_run["service_category"] == "Waste"
    assert ("commit", None) in events
    assert ("rollback", None) in events
    assert warnings == ["threshold alert recheck failed for forecast_window_type=daily: boom"]


@pytest.mark.unit
def test_weather_overlay_render_event_route_returns_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def record_render_event(self, overlay_request_id: str, payload) -> None:
            assert overlay_request_id == "overlay-1"
            assert payload.render_status == "rendered"

    monkeypatch.setattr(weather_overlay_route, "build_weather_overlay_service", lambda: FakeService())

    response = weather_overlay_route.record_weather_overlay_render_event(
        "overlay-1",
        payload=SimpleNamespace(render_status="rendered"),
        _claims={"roles": ["OperationalManager"]},
    )

    assert isinstance(response, Response)
    assert response.status_code == 202
