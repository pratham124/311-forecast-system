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
from app.services.weekly_forecast_activation_service import WeeklyForecastStorageError
from app.services.weekly_forecast_service import WeeklyForecastService


def _seed_cleaned_dataset(session, *, with_geography: bool) -> None:
    now = datetime.now(timezone.utc)
    base = now - timedelta(days=21)
    records = []
    for day_offset in range(10):
        record = {
            "service_request_id": f"seed-{day_offset}",
            "requested_at": (base + timedelta(days=day_offset)).isoformat().replace("+00:00", "Z"),
            "category": "Roads",
        }
        if with_geography:
            record["ward"] = "Ward 1"
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
def test_missing_input_data_fails_and_preserves_no_marker(session) -> None:
    service = _build_service(session)
    run, _ = service.start_run("on_demand", now=datetime.now(timezone.utc))
    session.commit()
    result = service.execute_run(run.weekly_forecast_run_id)
    session.commit()

    assert result.status == "failed"
    assert result.result_type == "missing_input_data"
    with pytest.raises(Exception):
        service.get_current_forecast()


@pytest.mark.integration
def test_category_only_fallback_succeeds_when_geography_incomplete(session) -> None:
    _seed_cleaned_dataset(session, with_geography=False)
    service = _build_service(session)

    run, _ = service.start_run("on_demand", now=datetime.now(timezone.utc))
    session.commit()
    result = service.execute_run(run.weekly_forecast_run_id)
    session.commit()
    current = service.get_current_forecast()

    assert result.status == "success"
    assert current.geography_scope == "category_only"
    assert all(bucket.geography_key is None for bucket in current.buckets)


@pytest.mark.integration
def test_engine_and_storage_failures_preserve_prior_current_forecast(session, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_cleaned_dataset(session, with_geography=True)
    service = _build_service(session)
    now = datetime.now(timezone.utc)

    success_run, _ = service.start_run("on_demand", now=now)
    session.commit()
    success_result = service.execute_run(success_run.weekly_forecast_run_id)
    session.commit()
    current_before = service.get_current_forecast()

    def raise_engine_failure(_prepared):
        raise RuntimeError("pipeline exploded")

    monkeypatch.setattr(service.pipeline, "run", raise_engine_failure)
    engine_run, _ = service.start_run("on_demand", now=now + timedelta(days=7))
    session.commit()
    engine_result = service.execute_run(engine_run.weekly_forecast_run_id)
    session.commit()

    monkeypatch.setattr(service.pipeline, "run", lambda prepared: {"geography_scope": "category_and_geography", "baseline_method": "historical_daily_mean", "buckets": [{"forecast_date_local": (now + timedelta(days=7)).date(), "service_category": "Roads", "geography_key": "Ward 1", "point_forecast": 1.0, "quantile_p10": 0.5, "quantile_p50": 1.0, "quantile_p90": 1.5, "baseline_value": 1.0}]})
    monkeypatch.setattr(service.activation_service, "store_and_activate", lambda **kwargs: (_ for _ in ()).throw(WeeklyForecastStorageError("db failed")))
    storage_run, _ = service.start_run("on_demand", now=now + timedelta(days=14))
    session.commit()
    storage_result = service.execute_run(storage_run.weekly_forecast_run_id)
    session.commit()
    current_after = service.get_current_forecast()

    assert success_result.status == "success"
    assert engine_result.result_type == "engine_failure"
    assert storage_result.result_type == "storage_failure"
    assert current_after.weekly_forecast_version_id == current_before.weekly_forecast_version_id
