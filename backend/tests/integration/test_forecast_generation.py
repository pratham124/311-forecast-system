from __future__ import annotations

from datetime import datetime, timezone
from fastapi import BackgroundTasks
from time import perf_counter
import pytest

from app.api.routes.forecasts import get_current_forecast, get_forecast_run, trigger_daily_forecast
from app.clients.geomet_client import GeoMetClient
from app.clients.nager_date_client import NagerDateClient
from app.core.config import get_settings
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.forecast_model_repository import ForecastModelRepository
from app.services.forecast_training_service import ForecastTrainingService


def _run_background_tasks(tasks: BackgroundTasks) -> None:
    for task in tasks.tasks:
        task.func(*task.args, **task.kwargs)


def _seed_cleaned_dataset(session, *, with_geography: bool) -> str:
    repository = DatasetRepository(session)
    cleaned_repository = CleanedDatasetRepository(session)
    records = [
        {
            "service_request_id": "seed-1",
            "requested_at": "2026-03-18T09:00:00Z",
            "category": "Roads",
        },
        {
            "service_request_id": "seed-2",
            "requested_at": "2026-03-18T10:00:00Z",
            "category": "Roads",
        },
    ]
    if with_geography:
        for record in records:
            record["ward"] = "Ward 1"
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
    version.record_count = cleaned_repository.count_current_cleaned_records("edmonton_311")
    repository.activate_dataset("edmonton_311", version.dataset_version_id, "validation-1")
    session.commit()
    return version.dataset_version_id


def _train_model(session) -> None:
    service = ForecastTrainingService(
        cleaned_dataset_repository=CleanedDatasetRepository(session),
        forecast_model_repository=ForecastModelRepository(session),
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        settings=get_settings(),
    )
    run = service.start_run("on_demand", now=datetime(2026, 3, 22, 12, tzinfo=timezone.utc))
    session.commit()
    service.execute_run(run.forecast_model_run_id)
    session.commit()


@pytest.mark.integration
def test_on_demand_generation_creates_current_forecast(session) -> None:
    _seed_cleaned_dataset(session, with_geography=True)
    _train_model(session)
    background_tasks = BackgroundTasks()

    started = perf_counter()
    accepted = trigger_daily_forecast(
        background_tasks=background_tasks,
        payload=None,
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["OperationalManager"]},
    )
    _run_background_tasks(background_tasks)
    elapsed = perf_counter() - started
    session.expire_all()

    run = get_forecast_run(
        accepted.forecast_run_id,
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["OperationalManager"]},
    )
    current = get_current_forecast(
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["OperationalManager"]},
    )

    assert run.status == "success"
    assert run.result_type == "generated_new"
    assert current.forecast_version_id == run.forecast_version_id
    assert current.geography_scope == "category_and_geography"
    assert elapsed < 120


@pytest.mark.integration
def test_scheduled_style_generation_uses_same_workflow(session) -> None:
    _seed_cleaned_dataset(session, with_geography=False)
    _train_model(session)
    background_tasks = BackgroundTasks()

    started = perf_counter()
    accepted = trigger_daily_forecast(
        background_tasks=background_tasks,
        payload=None,
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["OperationalManager"]},
    )
    _run_background_tasks(background_tasks)
    elapsed = perf_counter() - started
    session.expire_all()

    current = get_current_forecast(
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["OperationalManager"]},
    )

    assert accepted.forecast_run_id
    assert current.bucket_count == 24
    assert elapsed < 120
