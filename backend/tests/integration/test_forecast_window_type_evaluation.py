from __future__ import annotations

from app.repositories.notification_event_repository import NotificationEventRepository
from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository
from tests.evaluation_helpers import seed_daily_evaluation_inputs, seed_weekly_evaluation_inputs


def test_daily_and_weekly_forecast_products_preserve_window_type(app_client, operational_manager_headers, session) -> None:
    _, daily_forecast_version_id = seed_daily_evaluation_inputs(session, seed_tag="window-daily")
    _, weekly_forecast_version_id = seed_weekly_evaluation_inputs(session, seed_tag="window-weekly")
    repository = ThresholdConfigurationRepository(session)
    repository.create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=1,
        notification_channels=["email"],
        operational_manager_id="manager-1",
    )
    repository.create_configuration(
        service_category="Roads",
        forecast_window_type="daily",
        threshold_value=1,
        notification_channels=["email"],
        operational_manager_id="manager-1",
    )
    session.commit()

    daily_response = app_client.post(
        "/api/v1/forecast-alerts/evaluations",
        json={"forecastReferenceId": daily_forecast_version_id, "forecastProduct": "daily", "triggerSource": "manual_replay"},
        headers=operational_manager_headers,
    )
    weekly_response = app_client.post(
        "/api/v1/forecast-alerts/evaluations",
        json={"forecastReferenceId": weekly_forecast_version_id, "forecastProduct": "weekly", "triggerSource": "manual_replay"},
        headers=operational_manager_headers,
    )
    assert daily_response.status_code == 202
    assert weekly_response.status_code == 202

    events = NotificationEventRepository(session).list_events(service_category="Roads")
    assert any(event.forecast_window_type == "hourly" for event in events)
    assert any(event.forecast_window_type == "daily" for event in events)
