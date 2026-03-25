from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.forecast_model_repository import ForecastModelRepository
from app.services.weekly_forecast_training_service import WeeklyForecastTrainingService


class _HistoricalGeoMetClient:
    def fetch_historical_hourly_conditions(self, start, end):
        return []


class _NagerClient:
    def fetch_holidays(self, year):
        return []


def _seed_cleaned_dataset(session) -> None:
    records = []
    base = datetime(2026, 2, 1, tzinfo=timezone.utc)
    for day_offset in range(49):
        records.append(
            {
                "service_request_id": f"seed-{day_offset}",
                "requested_at": (base + timedelta(days=day_offset)).isoformat().replace("+00:00", "Z"),
                "category": "Roads",
            }
        )
    repository = DatasetRepository(session)
    cleaned_repository = CleanedDatasetRepository(session)
    version = repository.create_dataset_version(
        source_name="edmonton_311",
        run_id="seed-validation-run",
        candidate_id=None,
        record_count=len(records),
        records=records,
        validation_status="approved",
        dataset_kind="cleaned",
        approved_by_validation_run_id="validation-1",
    )
    cleaned_repository.upsert_current_cleaned_records(
        source_name="edmonton_311",
        ingestion_run_id="seed-validation-run",
        source_dataset_version_id=version.dataset_version_id,
        approved_dataset_version_id=version.dataset_version_id,
        approved_by_validation_run_id="validation-1",
        cleaned_records=records,
    )
    repository.activate_dataset("edmonton_311", version.dataset_version_id, "validation-1")
    session.commit()


@pytest.mark.contract
def test_weekly_forecast_model_routes_return_status_and_current_model(app_client, planner_headers, session, tmp_path) -> None:
    _seed_cleaned_dataset(session)
    service = WeeklyForecastTrainingService(
        cleaned_dataset_repository=CleanedDatasetRepository(session),
        forecast_model_repository=ForecastModelRepository(session),
        geomet_client=_HistoricalGeoMetClient(),
        nager_date_client=_NagerClient(),
        settings=type("S", (), {
            "source_name": "edmonton_311",
            "weekly_forecast_product_name": "weekly_7_day_demand",
            "weekly_forecast_timezone": "America/Edmonton",
            "weekly_forecast_history_days": 56,
            "weekly_forecast_model_artifact_dir": str(tmp_path / "weekly_models"),
        })(),
    )
    run = service.start_run("scheduled", now=datetime(2026, 3, 24, tzinfo=timezone.utc))
    session.commit()
    service.execute_run(run.forecast_model_run_id)
    session.commit()

    status_response = app_client.get(f"/api/v1/forecast-model-runs/7-day/{run.forecast_model_run_id}", headers=planner_headers)
    current_response = app_client.get("/api/v1/forecast-models/current-weekly", headers=planner_headers)

    assert status_response.status_code == 200
    assert status_response.json()["forecastModelRunId"] == run.forecast_model_run_id
    assert status_response.json()["forecastProductName"] == "weekly_7_day_demand"
    assert current_response.status_code == 200
    assert current_response.json()["forecastProductName"] == "weekly_7_day_demand"
    assert current_response.json()["artifactPath"].endswith(".pkl")


@pytest.mark.contract
def test_weekly_forecast_model_routes_return_not_found_without_current_model(app_client, planner_headers) -> None:
    status_response = app_client.get("/api/v1/forecast-model-runs/7-day/missing", headers=planner_headers)
    current_response = app_client.get("/api/v1/forecast-models/current-weekly", headers=planner_headers)

    assert status_response.status_code == 404
    assert current_response.status_code == 404
