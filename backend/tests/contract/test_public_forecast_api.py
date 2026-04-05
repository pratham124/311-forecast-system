from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.forecast_run_repository import ForecastRunRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.repositories.weekly_forecast_run_repository import WeeklyForecastRunRepository


def _seed_daily_public_forecast(session, *, include_restricted_bucket: bool = False) -> None:
    dataset_repository = DatasetRepository(session)
    version = dataset_repository.create_dataset_version(
        source_name="edmonton_311",
        run_id="public-forecast-run",
        candidate_id=None,
        record_count=4,
        records=[
            {"service_request_id": "roads-1", "requested_at": "2026-03-10T00:00:00Z", "category": "Roads"},
            {"service_request_id": "waste-1", "requested_at": "2026-03-10T01:00:00Z", "category": "Waste"},
        ],
    )
    dataset_repository.activate_dataset("edmonton_311", version.dataset_version_id, "public-forecast-run")
    cleaned_repository = CleanedDatasetRepository(session)
    cleaned_repository.upsert_current_cleaned_records(
        source_name="edmonton_311",
        ingestion_run_id="public-forecast-run",
        source_dataset_version_id=version.dataset_version_id,
        approved_dataset_version_id=version.dataset_version_id,
        approved_by_validation_run_id="validation-1",
        cleaned_records=[
            {"service_request_id": "roads-1", "requested_at": "2026-03-10T00:00:00Z", "category": "Roads"},
            {"service_request_id": "waste-1", "requested_at": "2026-03-10T01:00:00Z", "category": "Waste"},
        ],
    )
    run = ForecastRunRepository(session).create_run(
        trigger_type="scheduled",
        source_cleaned_dataset_version_id=version.dataset_version_id,
        requested_horizon_start=datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
        requested_horizon_end=datetime(2026, 3, 21, 0, tzinfo=timezone.utc),
    )
    repository = ForecastRepository(session)
    forecast_version = repository.create_forecast_version(
        forecast_run_id=run.forecast_run_id,
        source_cleaned_dataset_version_id=version.dataset_version_id,
        horizon_start=datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
        horizon_end=datetime(2026, 3, 21, 0, tzinfo=timezone.utc),
        geography_scope="citywide",
        baseline_method="seasonal_naive",
        summary="Public daily forecast",
    )
    buckets = [
        {
            "bucket_start": datetime(2026, 3, 20, hour, tzinfo=timezone.utc),
            "bucket_end": datetime(2026, 3, 20, hour, tzinfo=timezone.utc) + timedelta(hours=1),
            "service_category": "Roads",
            "geography_key": None,
            "point_forecast": 10 + hour,
            "quantile_p10": 8 + hour,
            "quantile_p50": 10 + hour,
            "quantile_p90": 12 + hour,
            "baseline_value": 9 + hour,
        }
        for hour in range(2)
    ] + [
        {
            "bucket_start": datetime(2026, 3, 20, hour, tzinfo=timezone.utc),
            "bucket_end": datetime(2026, 3, 20, hour, tzinfo=timezone.utc) + timedelta(hours=1),
            "service_category": "Waste",
            "geography_key": None,
            "point_forecast": 20 + hour,
            "quantile_p10": 18 + hour,
            "quantile_p50": 20 + hour,
            "quantile_p90": 22 + hour,
            "baseline_value": 19 + hour,
        }
        for hour in range(2)
    ]
    if include_restricted_bucket:
        buckets.append(
            {
                "bucket_start": datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
                "bucket_end": datetime(2026, 3, 20, 1, tzinfo=timezone.utc),
                "service_category": "Transit",
                "geography_key": "Ward 1",
                "point_forecast": 40,
                "quantile_p10": 36,
                "quantile_p50": 40,
                "quantile_p90": 44,
                "baseline_value": 38,
            }
        )
    repository.store_buckets(forecast_version.forecast_version_id, buckets)
    repository.mark_version_stored(forecast_version.forecast_version_id, bucket_count=len(buckets))
    repository.activate_forecast(
        forecast_product_name="daily_1_day_demand",
        forecast_version_id=forecast_version.forecast_version_id,
        source_cleaned_dataset_version_id=version.dataset_version_id,
        horizon_start=datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
        horizon_end=datetime(2026, 3, 21, 0, tzinfo=timezone.utc),
        updated_by_run_id=run.forecast_run_id,
        geography_scope="citywide",
    )
    session.commit()


def _seed_weekly_public_forecast(session) -> None:
    dataset_repository = DatasetRepository(session)
    version = dataset_repository.create_dataset_version(
        source_name="edmonton_311",
        run_id="public-weekly-run",
        candidate_id=None,
        record_count=2,
        records=[
            {"service_request_id": "roads-weekly", "requested_at": "2026-03-10T00:00:00Z", "category": "Roads"},
            {"service_request_id": "waste-weekly", "requested_at": "2026-03-10T01:00:00Z", "category": "Waste"},
        ],
    )
    dataset_repository.activate_dataset("edmonton_311", version.dataset_version_id, "public-weekly-run")
    cleaned_repository = CleanedDatasetRepository(session)
    cleaned_repository.upsert_current_cleaned_records(
        source_name="edmonton_311",
        ingestion_run_id="public-weekly-run",
        source_dataset_version_id=version.dataset_version_id,
        approved_dataset_version_id=version.dataset_version_id,
        approved_by_validation_run_id="validation-weekly-1",
        cleaned_records=[
            {"service_request_id": "roads-weekly", "requested_at": "2026-03-10T00:00:00Z", "category": "Roads"},
            {"service_request_id": "waste-weekly", "requested_at": "2026-03-10T01:00:00Z", "category": "Waste"},
        ],
    )
    run = WeeklyForecastRunRepository(session).create_run(
        trigger_type="scheduled",
        source_cleaned_dataset_version_id=version.dataset_version_id,
        week_start_local=datetime(2026, 3, 23, 0, tzinfo=timezone.utc),
        week_end_local=datetime(2026, 3, 30, 0, tzinfo=timezone.utc),
    )
    repository = WeeklyForecastRepository(session)
    forecast_version = repository.create_forecast_version(
        weekly_forecast_run_id=run.weekly_forecast_run_id,
        source_cleaned_dataset_version_id=version.dataset_version_id,
        week_start_local=datetime(2026, 3, 23, 0, tzinfo=timezone.utc),
        week_end_local=datetime(2026, 3, 30, 0, tzinfo=timezone.utc),
        geography_scope="citywide",
        baseline_method="seasonal_naive",
        summary="Public weekly forecast",
    )
    repository.store_buckets(
        forecast_version.weekly_forecast_version_id,
        [
            {
                "forecast_date_local": date(2026, 3, 23),
                "service_category": "Roads",
                "geography_key": None,
                "point_forecast": 70,
                "quantile_p10": 60,
                "quantile_p50": 70,
                "quantile_p90": 80,
                "baseline_value": 65,
            },
            {
                "forecast_date_local": date(2026, 3, 24),
                "service_category": "Waste",
                "geography_key": None,
                "point_forecast": 90,
                "quantile_p10": 80,
                "quantile_p50": 90,
                "quantile_p90": 100,
                "baseline_value": 85,
            },
        ],
    )
    repository.mark_version_stored(forecast_version.weekly_forecast_version_id)
    repository.activate_forecast(
        forecast_product_name="weekly_7_day_demand",
        weekly_forecast_version_id=forecast_version.weekly_forecast_version_id,
        source_cleaned_dataset_version_id=version.dataset_version_id,
        week_start_local=datetime(2026, 3, 23, 0, tzinfo=timezone.utc),
        week_end_local=datetime(2026, 3, 30, 0, tzinfo=timezone.utc),
        updated_by_run_id=run.weekly_forecast_run_id,
        geography_scope="citywide",
    )
    session.commit()


def test_get_public_forecast_available_response(app_client, session):
    _seed_daily_public_forecast(session)
    response = app_client.get("/api/v1/public/forecast-categories/current?forecastProduct=daily", headers={"X-Client-Correlation-Id": "public-1"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"
    assert body["clientCorrelationId"] == "public-1"
    assert body["coverageStatus"] == "complete"
    assert body["sanitizationStatus"] == "passed_as_is"
    assert {item["serviceCategory"] for item in body["categorySummaries"]} == {"Roads", "Waste"}


def test_get_public_weekly_forecast_available_response(app_client, session):
    _seed_weekly_public_forecast(session)
    response = app_client.get("/api/v1/public/forecast-categories/current?forecastProduct=weekly")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"
    assert body["forecastWindowLabel"].startswith("2026-03-23")


def test_get_public_forecast_sanitized_response(app_client, session):
    _seed_daily_public_forecast(session, include_restricted_bucket=True)
    response = app_client.get("/api/v1/public/forecast-categories/current")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"
    assert body["coverageStatus"] == "incomplete"
    assert body["sanitizationStatus"] == "sanitized"
    assert "Transit" in body["coverageMessage"]


def test_get_public_forecast_unavailable_response(app_client):
    response = app_client.get("/api/v1/public/forecast-categories/current?forecastProduct=daily")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unavailable"
    assert "No approved daily public forecast" in body["statusMessage"]


def test_get_public_forecast_validates_query(app_client):
    response = app_client.get("/api/v1/public/forecast-categories/current?forecastProduct=monthly")
    assert response.status_code == 422


def test_post_public_forecast_display_event(app_client, session):
    _seed_daily_public_forecast(session)
    load_response = app_client.get("/api/v1/public/forecast-categories/current")
    request_id = load_response.json()["publicForecastRequestId"]
    response = app_client.post(
        f"/api/v1/public/forecast-categories/{request_id}/display-events",
        json={"displayOutcome": "rendered"},
    )
    assert response.status_code == 202


def test_post_public_forecast_display_event_404(app_client):
    response = app_client.post(
        "/api/v1/public/forecast-categories/missing-request/display-events",
        json={"displayOutcome": "rendered"},
    )
    assert response.status_code == 404


def test_post_public_forecast_display_event_422(app_client):
    response = app_client.post(
        "/api/v1/public/forecast-categories/missing-request/display-events",
        json={"displayOutcome": "render_failed"},
    )
    assert response.status_code == 422
