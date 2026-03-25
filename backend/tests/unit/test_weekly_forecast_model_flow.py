from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.forecast_model_repository import ForecastModelRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.repositories.weekly_forecast_run_repository import WeeklyForecastRunRepository
from app.services.weekly_forecast_service import WeeklyForecastService
from app.services.weekly_forecast_training_service import WeeklyForecastTrainingService


class _HistoricalGeoMetClient:
    def __init__(self, weather_rows: list[dict[str, object]] | None = None) -> None:
        self.weather_rows = weather_rows or []

    def fetch_historical_hourly_conditions(self, start, end):
        return list(self.weather_rows)

    def fetch_forecast_hourly_conditions(self, start, end):
        return list(self.weather_rows)


class _NagerClient:
    def __init__(self, holidays: list[dict[str, object]] | None = None) -> None:
        self.holidays = holidays or []

    def fetch_holidays(self, year):
        return list(self.holidays)


def _seed_cleaned_dataset(session, *, with_geography: bool = True) -> str:
    records = []
    base = datetime(2026, 2, 1, tzinfo=timezone.utc)
    for day_offset in range(49):
        for seq in range(2):
            record = {
                "service_request_id": f"seed-{day_offset}-{seq}",
                "requested_at": (base + timedelta(days=day_offset, hours=seq)).isoformat().replace("+00:00", "Z"),
                "category": "Roads" if seq == 0 else "Waste",
            }
            if with_geography:
                record["ward"] = "Ward 1" if seq == 0 else "Ward 2"
            records.append(record)
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
    return version.dataset_version_id


@pytest.mark.unit
def test_weekly_forecast_training_service_trains_and_loads_current_artifact(session, tmp_path: Path) -> None:
    _seed_cleaned_dataset(session, with_geography=True)
    settings = SimpleNamespace(
        source_name="edmonton_311",
        weekly_forecast_product_name="weekly_7_day_demand",
        weekly_forecast_timezone="America/Edmonton",
        weekly_forecast_history_days=56,
        weekly_forecast_model_artifact_dir=str(tmp_path / "weekly_models"),
    )
    service = WeeklyForecastTrainingService(
        cleaned_dataset_repository=CleanedDatasetRepository(session),
        forecast_model_repository=ForecastModelRepository(session),
        geomet_client=_HistoricalGeoMetClient(),
        nager_date_client=_NagerClient(),
        settings=settings,
    )

    run = service.start_run("scheduled", now=datetime(2026, 3, 24, tzinfo=timezone.utc))
    session.commit()
    result = service.execute_run(run.forecast_model_run_id)
    session.commit()

    current_artifact = ForecastModelRepository(session).find_current_model("weekly_7_day_demand")
    assert result.result_type == "trained_new"
    assert current_artifact is not None
    assert Path(current_artifact.artifact_path).exists()
    loaded = service.load_current_artifact()
    assert loaded is not None
    assert loaded.model_family == "historical_weekday_global"


@pytest.mark.unit
def test_weekly_forecast_service_uses_trained_model_predict_path(session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_cleaned_dataset(session, with_geography=False)
    settings = SimpleNamespace(
        source_name="edmonton_311",
        weekly_forecast_product_name="weekly_7_day_demand",
        weekly_forecast_timezone="America/Edmonton",
        weekly_forecast_history_days=56,
        weekly_forecast_model_artifact_dir=str(tmp_path / "weekly_models"),
    )
    model_repository = ForecastModelRepository(session)
    training_service = WeeklyForecastTrainingService(
        cleaned_dataset_repository=CleanedDatasetRepository(session),
        forecast_model_repository=model_repository,
        geomet_client=_HistoricalGeoMetClient(),
        nager_date_client=_NagerClient(),
        settings=settings,
    )
    model_run = training_service.start_run("scheduled", now=datetime(2026, 3, 24, tzinfo=timezone.utc))
    session.commit()
    training_service.execute_run(model_run.forecast_model_run_id)
    session.commit()

    service = WeeklyForecastService(
        cleaned_dataset_repository=CleanedDatasetRepository(session),
        weekly_forecast_run_repository=WeeklyForecastRunRepository(session),
        weekly_forecast_repository=WeeklyForecastRepository(session),
        forecast_model_repository=model_repository,
        geomet_client=_HistoricalGeoMetClient(),
        nager_date_client=_NagerClient(),
        settings=settings,
    )
    monkeypatch.setattr(service.pipeline, "run", lambda prepared: (_ for _ in ()).throw(AssertionError("run should not be used")))

    run, created = service.start_run("on_demand", now=datetime(2026, 3, 24, tzinfo=timezone.utc))
    session.commit()
    result = service.execute_run(run.weekly_forecast_run_id)
    session.commit()
    current = service.get_current_forecast()

    assert created is True
    assert result.result_type == "generated_new"
    assert current.weekly_forecast_version_id == result.generated_forecast_version_id
    assert current.bucket_count_days == 7
