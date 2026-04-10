from __future__ import annotations

from datetime import datetime

from app.repositories.notification_event_repository import NotificationEventRepository
from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository
from tests.evaluation_helpers import seed_daily_evaluation_inputs


def test_alert_delivery_completes_within_five_minutes(app_client, operational_manager_headers, session) -> None:
    _, forecast_version_id = seed_daily_evaluation_inputs(session, seed_tag="threshold-latency")
    ThresholdConfigurationRepository(session).create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=1,
        notification_channels=["email"],
        operational_manager_id="manager-1",
    )
    session.commit()

    response = app_client.post(
        "/api/v1/forecast-alerts/evaluations",
        json={"forecastReferenceId": forecast_version_id, "forecastProduct": "daily", "triggerSource": "manual_replay"},
        headers=operational_manager_headers,
    )
    assert response.status_code == 202

    event = NotificationEventRepository(session).list_events(service_category="Roads")[0]
    elapsed = datetime.fromisoformat(event.created_at.isoformat()) - datetime.fromisoformat(response.json()["acceptedAt"].replace("Z", "+00:00"))
    assert elapsed.total_seconds() < 300
