from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pytest

from app.clients.geomet_client import GeoMetClient
from app.clients.nager_date_client import NagerDateClient
from app.core.config import get_settings
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.repositories.weekly_forecast_run_repository import WeeklyForecastRunRepository
from app.services.weekly_forecast_service import WeeklyForecastService


def _seed_cleaned_dataset(session) -> None:
    now = datetime.now(timezone.utc)
    base = now - timedelta(days=21)
    records = []
    for day_offset in range(10):
        record = {
            "service_request_id": f"seed-{day_offset}",
            "requested_at": (base + timedelta(days=day_offset)).isoformat().replace("+00:00", "Z"),
            "category": "Roads",
            "ward": "Ward 1",
        }
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
def test_current_week_reuse_serves_existing_forecast(session) -> None:
    _seed_cleaned_dataset(session)
    service = _build_service(session)
    now = datetime.now(timezone.utc)

    first_run, _ = service.start_run("on_demand", now=now)
    session.commit()
    first_result = service.execute_run(first_run.weekly_forecast_run_id)
    session.commit()

    second_run, _ = service.start_run("on_demand", now=now)
    session.commit()
    second_result = service.execute_run(second_run.weekly_forecast_run_id)
    session.commit()

    assert first_result.result_type == "generated_new"
    assert second_result.result_type == "served_current"
    assert second_result.served_forecast_version_id == first_result.generated_forecast_version_id


@pytest.mark.integration
def test_same_week_in_progress_deduplicates_to_existing_run(session) -> None:
    _seed_cleaned_dataset(session)
    service = _build_service(session)
    now = datetime.now(timezone.utc)

    first_run, first_created = service.start_run("on_demand", now=now)
    second_run, second_created = service.start_run("on_demand", now=now)

    assert first_created is True
    assert second_created is False
    assert second_run.weekly_forecast_run_id == first_run.weekly_forecast_run_id
