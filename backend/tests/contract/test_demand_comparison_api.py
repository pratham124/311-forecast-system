from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models import ForecastRun
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.forecast_repository import ForecastRepository


def seed_contract_data(session) -> None:
    dataset_repository = DatasetRepository(session)
    version = dataset_repository.create_dataset_version(
        source_name="edmonton_311",
        run_id="clean-run",
        candidate_id=None,
        record_count=2,
        records=[
            {"service_request_id": "hist-1", "requested_at": "2026-03-01T00:15:00Z", "category": "Roads", "ward": "Ward 1"},
            {"service_request_id": "hist-2", "requested_at": "2026-03-01T01:15:00Z", "category": "Waste", "ward": "Ward 1"},
        ],
        validation_status="approved",
        dataset_kind="cleaned",
    )
    dataset_repository.activate_dataset("edmonton_311", version.dataset_version_id, "clean-run")

    forecast_repository = ForecastRepository(session)
    run = ForecastRun(
        trigger_type="manual",
        source_cleaned_dataset_version_id=version.dataset_version_id,
        requested_horizon_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        requested_horizon_end=datetime(2026, 3, 3, tzinfo=timezone.utc),
        geography_scope="ward",
        status="success",
    )
    session.add(run)
    session.flush()
    forecast_version = forecast_repository.create_forecast_version(
        forecast_run_id=run.forecast_run_id,
        source_cleaned_dataset_version_id=version.dataset_version_id,
        horizon_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        horizon_end=datetime(2026, 3, 3, tzinfo=timezone.utc),
        geography_scope="ward",
        baseline_method="naive",
        summary="daily forecast",
    )
    forecast_repository.store_buckets(
        forecast_version.forecast_version_id,
        [
            {
                "bucket_start": datetime(2026, 3, 1, 0, tzinfo=timezone.utc),
                "bucket_end": datetime(2026, 3, 1, 1, tzinfo=timezone.utc),
                "service_category": "Roads",
                "geography_key": "Ward 1",
                "point_forecast": 4.0,
                "quantile_p10": 2.0,
                "quantile_p50": 4.0,
                "quantile_p90": 6.0,
                "baseline_value": 3.0,
            }
        ],
    )
    forecast_repository.mark_version_stored(forecast_version.forecast_version_id, 1)
    forecast_repository.activate_forecast(
        forecast_product_name="daily_1_day_demand",
        forecast_version_id=forecast_version.forecast_version_id,
        source_cleaned_dataset_version_id=version.dataset_version_id,
        horizon_start=forecast_version.horizon_start,
        horizon_end=forecast_version.horizon_end,
        updated_by_run_id=run.forecast_run_id,
        geography_scope="ward",
    )
    session.commit()


@pytest.mark.contract
def test_demand_comparison_availability_endpoint(app_client, planner_headers, session) -> None:
    seed_contract_data(session)

    response = app_client.get("/api/v1/demand-comparisons/availability", headers=planner_headers)
    assert response.status_code == 200
    payload = response.json()

    # Top-level keys present
    assert "serviceCategories" in payload
    assert "byCategoryGeography" in payload
    assert "dateConstraints" in payload
    assert "presets" in payload

    # Categories match what was seeded
    assert "Roads" in payload["serviceCategories"]

    # Date constraints reflect real data
    constraints = payload["dateConstraints"]
    assert constraints["historicalMin"] is not None
    assert constraints["historicalMax"] is not None
    assert constraints["forecastMin"] is not None
    assert constraints["forecastMax"] is not None
    # Overlap exists because history and forecast overlap
    assert constraints["overlapStart"] is not None
    assert constraints["overlapEnd"] is not None

    # Per-category geography present for Roads
    assert "Roads" in payload["byCategoryGeography"]
    roads_geo = payload["byCategoryGeography"]["Roads"]
    assert "geographyLevels" in roads_geo
    assert "geographyOptions" in roads_geo
    assert "ward" in roads_geo["geographyLevels"]
    assert "Ward 1" in roads_geo["geographyOptions"]["ward"]

    # At least one preset (active forecast window)
    assert len(payload["presets"]) >= 1
    preset = payload["presets"][0]
    assert "label" in preset
    assert "timeRangeStart" in preset
    assert "timeRangeEnd" in preset

    # Forecast product identified
    assert payload["forecastProduct"] == "daily_1_day"


@pytest.mark.contract
def test_demand_comparison_context_and_query_endpoints(app_client, planner_headers, session) -> None:
    seed_contract_data(session)

    context_response = app_client.get("/api/v1/demand-comparisons/context", headers=planner_headers)
    assert context_response.status_code == 200
    assert "Roads" in context_response.json()["serviceCategories"]

    response = app_client.post(
        "/api/v1/demand-comparisons/queries",
        json={
            "serviceCategories": ["Roads"],
            "geographyLevel": "ward",
            "geographyValues": ["Ward 1"],
            "timeRangeStart": "2026-03-01T00:00:00Z",
            "timeRangeEnd": "2026-03-02T00:00:00Z",
        },
        headers=planner_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["outcomeStatus"] == "success"
    assert payload["comparisonGranularity"] == "hourly"

    render_response = app_client.post(
        f"/api/v1/demand-comparisons/{payload['comparisonRequestId']}/render-events",
        json={"renderStatus": "rendered"},
        headers=planner_headers,
    )
    assert render_response.status_code == 202
    assert render_response.json()["recordedOutcomeStatus"] == "rendered"


@pytest.mark.contract
def test_demand_comparison_warning_invalid_request_and_missing_render(app_client, planner_headers, session) -> None:
    seed_contract_data(session)

    warning_response = app_client.post(
        "/api/v1/demand-comparisons/queries",
        json={
            "serviceCategories": ["Roads", "Waste"],
            "timeRangeStart": "2026-01-01T00:00:00Z",
            "timeRangeEnd": "2027-03-01T00:00:00Z",
        },
        headers=planner_headers,
    )
    assert warning_response.status_code == 200
    assert warning_response.json()["outcomeStatus"] == "warning_required"

    invalid_response = app_client.post(
        "/api/v1/demand-comparisons/queries",
        json={
            "serviceCategories": ["Unknown"],
            "timeRangeStart": "2026-03-01T00:00:00Z",
            "timeRangeEnd": "2026-03-02T00:00:00Z",
        },
        headers=planner_headers,
    )
    assert invalid_response.status_code == 422

    invalid_schema_response = app_client.post(
        "/api/v1/demand-comparisons/queries",
        json={
            "serviceCategories": ["Roads"],
            "geographyValues": ["Ward 1"],
            "timeRangeStart": "2026-03-02T00:00:00Z",
            "timeRangeEnd": "2026-03-01T00:00:00Z",
        },
        headers=planner_headers,
    )
    assert invalid_schema_response.status_code == 422

    missing_render = app_client.post(
        "/api/v1/demand-comparisons/not-found/render-events",
        json={"renderStatus": "rendered"},
        headers=planner_headers,
    )
    assert missing_render.status_code == 404
