from __future__ import annotations

from datetime import datetime, timedelta, timezone
from time import perf_counter
import pytest

from app.clients.geomet_client import GeoMetClient
from app.clients.nager_date_client import NagerDateClient
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.repositories.weekly_forecast_run_repository import WeeklyForecastRunRepository
from app.services.weekly_forecast_scheduler import build_weekly_forecast_job, build_weekly_regeneration_job
from app.services.weekly_forecast_service import WeeklyForecastService
from app.core.config import get_settings
from app.core.db import get_session_factory


def _seed_cleaned_dataset(session, *, with_geography: bool) -> str:
    now = datetime.now(timezone.utc)
    base = now - timedelta(days=21)
    records = []
    for day_offset in range(14):
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


def _build_service(session) -> WeeklyForecastService:
    return WeeklyForecastService(
        cleaned_dataset_repository=CleanedDatasetRepository(session),
        weekly_forecast_run_repository=WeeklyForecastRunRepository(session),
        weekly_forecast_repository=WeeklyForecastRepository(session),
        settings=get_settings(),
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
    )


@pytest.mark.integration
def test_on_demand_generation_creates_current_weekly_forecast(session) -> None:
    _seed_cleaned_dataset(session, with_geography=True)
    service = _build_service(session)

    started = perf_counter()
    run, created = service.start_run("on_demand", now=datetime.now(timezone.utc))
    session.commit()
    completed = service.execute_run(run.weekly_forecast_run_id)
    session.commit()
    current = service.get_current_forecast()
    elapsed = perf_counter() - started

    assert created is True
    assert completed.status == "success"
    assert completed.result_type == "generated_new"
    assert current.weekly_forecast_version_id == completed.generated_forecast_version_id
    assert current.geography_scope == "category_and_geography"
    assert current.bucket_count_days == 7
    assert elapsed < 120


@pytest.mark.integration
def test_scheduled_and_daily_regeneration_jobs_share_same_workflow(session, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_cleaned_dataset(session, with_geography=False)

    class _FakeGeoMetClient:
        def fetch_forecast_hourly_conditions(self, horizon_start, horizon_end):
            return []

    class _FakeNagerDateClient:
        def fetch_holidays(self, year, country_code="CA"):
            return []

    monkeypatch.setattr("app.services.weekly_forecast_scheduler.GeoMetClient", lambda: _FakeGeoMetClient())
    monkeypatch.setattr("app.services.weekly_forecast_scheduler.NagerDateClient", lambda: _FakeNagerDateClient())
    weekly_job = build_weekly_forecast_job(get_session_factory())
    regeneration_job = build_weekly_regeneration_job(get_session_factory())

    weekly_run_id = weekly_job()
    regeneration_run_id = regeneration_job()

    refreshed_session = get_session_factory()()
    try:
        repository = WeeklyForecastRunRepository(refreshed_session)
        weekly_run = repository.get_run(str(weekly_run_id))
        regeneration_run = repository.get_run(str(regeneration_run_id))
        assert weekly_run is not None
        assert regeneration_run is not None
        assert weekly_run.status == "success"
        assert regeneration_run.status == "success"
        assert regeneration_run.result_type in {"generated_new", "served_current"}
    finally:
        refreshed_session.close()
