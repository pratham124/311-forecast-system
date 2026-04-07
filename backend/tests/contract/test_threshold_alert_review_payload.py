from __future__ import annotations

from datetime import datetime, timezone

from app.models.threshold_alert_models import NotificationChannelAttempt, NotificationEvent, ThresholdConfiguration, ThresholdEvaluationRun


def test_alert_review_payload_contains_required_fields(app_client, session, planner_headers) -> None:
    cfg = ThresholdConfiguration(
        service_category="Roads",
        geography_type="ward",
        geography_value="Ward 1",
        forecast_window_type="hourly",
        threshold_value=15,
        notification_channels_json='["email","dashboard"]',
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
        geography_type="ward",
        geography_value="Ward 1",
        forecast_window_start=datetime(2026, 4, 7, 10, tzinfo=timezone.utc),
        forecast_window_end=datetime(2026, 4, 7, 11, tzinfo=timezone.utc),
        forecast_window_type="hourly",
        forecast_value=25,
        threshold_value=15,
        overall_delivery_status="partial_delivery",
    )
    session.add(event)
    session.flush()

    session.add(
        NotificationChannelAttempt(
            notification_event_id=event.notification_event_id,
            channel_type="email",
            attempt_number=1,
            status="failed",
            failure_reason="smtp timeout",
        )
    )
    session.add(
        NotificationChannelAttempt(
            notification_event_id=event.notification_event_id,
            channel_type="dashboard",
            attempt_number=2,
            status="succeeded",
            provider_reference="local",
        )
    )
    session.commit()

    response = app_client.get(f"/api/v1/forecast-alerts/events/{event.notification_event_id}", headers=planner_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["serviceCategory"] == "Roads"
    assert payload["geographyValue"] == "Ward 1"
    assert payload["forecastWindowType"] == "hourly"
    assert payload["overallDeliveryStatus"] == "partial_delivery"
    assert payload["failedChannelCount"] == 1
    assert len(payload["channelAttempts"]) == 2
