from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.forecast_run_repository import ForecastRunRepository


def _seed_daily_visualization(session) -> None:
    dataset_repository = DatasetRepository(session)
    version = dataset_repository.create_dataset_version(
        source_name="edmonton_311",
        run_id="run-1",
        candidate_id=None,
        record_count=6,
        records=[
            {"service_request_id": f"roads-{idx}", "requested_at": f"2026-03-1{idx}T0{idx}:00:00Z", "category": "Roads"}
            for idx in range(1, 4)
        ] + [
            {"service_request_id": f"waste-{idx}", "requested_at": f"2026-03-1{idx}T1{idx}:00:00Z", "category": "Waste"}
            for idx in range(1, 4)
        ],
    )
    dataset_repository.activate_dataset("edmonton_311", version.dataset_version_id, "run-1")
    cleaned_repository = CleanedDatasetRepository(session)
    cleaned_repository.upsert_current_cleaned_records(
        source_name="edmonton_311",
        ingestion_run_id="run-1",
        source_dataset_version_id=version.dataset_version_id,
        approved_dataset_version_id=version.dataset_version_id,
        approved_by_validation_run_id="validation-1",
        cleaned_records=[
            {"service_request_id": f"roads-{idx}", "requested_at": f"2026-03-1{idx}T0{idx}:00:00Z", "category": "Roads"}
            for idx in range(1, 4)
        ] + [
            {"service_request_id": f"waste-{idx}", "requested_at": f"2026-03-1{idx}T1{idx}:00:00Z", "category": "Waste"}
            for idx in range(1, 4)
        ],
    )
    run_repository = ForecastRunRepository(session)
    run = run_repository.create_run(
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
        summary="Daily forecast",
    )
    repository.store_buckets(
        forecast_version.forecast_version_id,
        [
            {
                "bucket_start": datetime(2026, 3, 20, hour, tzinfo=timezone.utc),
                "bucket_end": datetime(2026, 3, 20, hour, tzinfo=timezone.utc) + timedelta(hours=1),
                "service_category": category,
                "geography_key": None,
                "point_forecast": 10 + hour,
                "quantile_p10": 8 + hour,
                "quantile_p50": 10 + hour,
                "quantile_p90": 12 + hour,
                "baseline_value": 9 + hour,
            }
            for category in ["Roads", "Waste"]
            for hour in range(3)
        ],
    )
    repository.mark_version_stored(forecast_version.forecast_version_id, bucket_count=6)
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


def test_get_current_visualization_success(app_client, operational_manager_headers, session):
    _seed_daily_visualization(session)
    response = app_client.get("/api/v1/forecast-visualizations/current", params={"forecastProduct": "daily_1_day"}, headers=operational_manager_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["forecastProduct"] == "daily_1_day"
    assert body["viewStatus"] == "success"
    assert len(body["forecastSeries"]) == 3
    assert body["forecastSeries"][0]["pointForecast"] == 20.0
    assert body["uncertaintyBands"]["labels"] == ["P10", "P50", "P90"]


def test_get_current_visualization_supports_multiple_categories(app_client, operational_manager_headers, session):
    _seed_daily_visualization(session)
    response = app_client.get(
        "/api/v1/forecast-visualizations/current",
        params=[('forecastProduct', 'daily_1_day'), ('serviceCategory', 'Roads'), ('serviceCategory', 'Waste')],
        headers=operational_manager_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body['categoryFilter']['selectedCategories'] == ['Roads', 'Waste']
    assert len(body['forecastSeries']) == 3
    assert body['forecastSeries'][0]['pointForecast'] == 20.0


def test_get_current_visualization_supports_excluded_categories(app_client, operational_manager_headers, session):
    _seed_daily_visualization(session)
    response = app_client.get(
        '/api/v1/forecast-visualizations/current',
        params=[('forecastProduct', 'daily_1_day'), ('excludeServiceCategory', 'Waste')],
        headers=operational_manager_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body['categoryFilter']['selectedCategories'] == ['Roads']
    assert len(body['forecastSeries']) == 3


def test_list_visualization_service_categories(app_client, operational_manager_headers, session):
    _seed_daily_visualization(session)
    response = app_client.get('/api/v1/forecast-visualizations/service-categories', params={'forecastProduct': 'daily_1_day'}, headers=operational_manager_headers)
    assert response.status_code == 200
    assert response.json()['categories'] == ['Roads', 'Waste']


def test_get_current_visualization_requires_auth(app_client):
    response = app_client.get("/api/v1/forecast-visualizations/current", params={"forecastProduct": "daily_1_day"})
    assert response.status_code == 401


def test_get_current_visualization_forbidden_for_viewer(app_client, viewer_headers):
    response = app_client.get("/api/v1/forecast-visualizations/current", params={"forecastProduct": "daily_1_day"}, headers=viewer_headers)
    assert response.status_code == 403


def test_get_current_visualization_validates_query(app_client, operational_manager_headers):
    response = app_client.get("/api/v1/forecast-visualizations/current", params={"forecastProduct": "monthly"}, headers=operational_manager_headers)
    assert response.status_code == 422
