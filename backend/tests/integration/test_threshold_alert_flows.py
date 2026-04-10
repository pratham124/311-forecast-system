from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.repositories.forecast_repository import ForecastRepository
from app.repositories.forecast_run_repository import ForecastRunRepository
from app.repositories.notification_event_repository import NotificationEventRepository
from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository
from tests.evaluation_helpers import seed_daily_evaluation_inputs


def test_threshold_crossing_creates_one_alert_and_suppresses_duplicate(app_client, operational_manager_headers, session) -> None:
    _, forecast_version_id = seed_daily_evaluation_inputs(session, seed_tag="threshold-integration")
    ThresholdConfigurationRepository(session).create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=1,
        notification_channels=["email"],
        operational_manager_id="manager-1",
    )
    session.commit()

    first = app_client.post(
        "/api/v1/forecast-alerts/evaluations",
        json={"forecastReferenceId": forecast_version_id, "forecastProduct": "daily", "triggerSource": "forecast_publish"},
        headers=operational_manager_headers,
    )
    assert first.status_code == 202

    second = app_client.post(
        "/api/v1/forecast-alerts/evaluations",
        json={"forecastReferenceId": forecast_version_id, "forecastProduct": "daily", "triggerSource": "forecast_refresh"},
        headers=operational_manager_headers,
    )
    assert second.status_code == 202

    events = NotificationEventRepository(session).list_events(service_category="Roads")
    assert len(events) == 3

def test_category_threshold_ignores_forecast_geography_keys(app_client, operational_manager_headers, session, seed_current_dataset) -> None:
    horizon_start = datetime(2026, 3, 20, tzinfo=timezone.utc)
    horizon_end = horizon_start + timedelta(hours=2)
    run = ForecastRunRepository(session).create_run(
        trigger_type="scheduled",
        source_cleaned_dataset_version_id=seed_current_dataset,
        requested_horizon_start=horizon_start,
        requested_horizon_end=horizon_end,
    )
    repository = ForecastRepository(session)
    version = repository.create_forecast_version(
        forecast_run_id=run.forecast_run_id,
        source_cleaned_dataset_version_id=seed_current_dataset,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        geography_scope="regional",
        baseline_method="historical_hourly_mean",
        summary="Regional forecast",
    )
    repository.store_buckets(
        version.forecast_version_id,
        [
            {
                "bucket_start": horizon_start,
                "bucket_end": horizon_start + timedelta(hours=1),
                "service_category": "Roads",
                "geography_key": "Ward 1",
                "point_forecast": 9,
                "quantile_p10": 8,
                "quantile_p50": 9,
                "quantile_p90": 10,
                "baseline_value": 7,
            },
            {
                "bucket_start": horizon_start,
                "bucket_end": horizon_start + timedelta(hours=1),
                "service_category": "Roads",
                "geography_key": "Ward 2",
                "point_forecast": 6,
                "quantile_p10": 5,
                "quantile_p50": 6,
                "quantile_p90": 7,
                "baseline_value": 4,
            },
        ],
    )
    repository.mark_version_stored(version.forecast_version_id, bucket_count=2)
    ThresholdConfigurationRepository(session).create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=8,
        notification_channels=["email"],
        operational_manager_id="manager-1",
    )
    session.commit()

    response = app_client.post(
        "/api/v1/forecast-alerts/evaluations",
        json={"forecastReferenceId": version.forecast_version_id, "forecastProduct": "daily", "triggerSource": "manual_replay"},
        headers=operational_manager_headers,
    )
    assert response.status_code == 202

    events = NotificationEventRepository(session).list_events(service_category="Roads")
    assert len(events) == 1
    assert events[0].service_category == "Roads"
    assert events[0].geography_value is None
