from __future__ import annotations

from datetime import datetime, timezone

from app.models.threshold_alert_models import NotificationEvent, ThresholdConfiguration, ThresholdEvaluationRun


def _seed_alert_event(session) -> str:
    cfg = ThresholdConfiguration(
        service_category="Roads",
        geography_type=None,
        geography_value=None,
        forecast_window_type="hourly",
        threshold_value=20,
        notification_channels_json='["email"]',
        operational_manager_id="mgr-1",
        status="active",
        effective_from=datetime.now(timezone.utc),
    )
    session.add(cfg)
    session.flush()

    run = ThresholdEvaluationRun(
        forecast_version_reference="forecast-version-1",
        forecast_product="daily",
        trigger_source="manual_replay",
        status="completed",
    )
    session.add(run)
    session.flush()

    event = NotificationEvent(
        threshold_evaluation_run_id=run.threshold_evaluation_run_id,
        threshold_configuration_id=cfg.threshold_configuration_id,
        service_category="Roads",
        geography_type=None,
        geography_value=None,
        forecast_window_start=datetime(2026, 4, 7, 10, tzinfo=timezone.utc),
        forecast_window_end=datetime(2026, 4, 7, 11, tzinfo=timezone.utc),
        forecast_window_type="hourly",
        forecast_value=42,
        threshold_value=20,
        overall_delivery_status="delivered",
    )
    session.add(event)
    session.commit()
    return event.notification_event_id


def test_list_alert_events_endpoint(app_client, session, planner_headers) -> None:
    event_id = _seed_alert_event(session)

    response = app_client.get("/api/v1/forecast-alerts/events", headers=planner_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"]
    assert payload["items"][0]["notificationEventId"] == event_id


def test_get_alert_event_endpoint(app_client, session, planner_headers) -> None:
    event_id = _seed_alert_event(session)

    response = app_client.get(f"/api/v1/forecast-alerts/events/{event_id}", headers=planner_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["notificationEventId"] == event_id
    assert payload["serviceCategory"] == "Roads"
