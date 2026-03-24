from __future__ import annotations

from datetime import datetime, timezone
from fastapi import BackgroundTasks
from time import perf_counter
import pytest

from app.api.routes.forecasts import get_forecast_run, trigger_daily_forecast
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


def _seed_cleaned_dataset(session) -> None:
    repository = DatasetRepository(session)
    version = repository.create_dataset_version(
        source_name="edmonton_311",
        run_id="seed-validation-run",
        candidate_id=None,
        record_count=1,
        records=[
            {
                "service_request_id": "seed-1",
                "requested_at": "2026-03-18T09:00:00Z",
                "category": "Roads",
            }
        ],
        validation_status="approved",
        dataset_kind="cleaned",
        approved_by_validation_run_id="validation-1",
    )
    repository.activate_dataset("edmonton_311", version.dataset_version_id, "validation-1")
    session.commit()


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
def test_trigger_reuses_existing_current_forecast(session) -> None:
    _seed_cleaned_dataset(session)
    _train_model(session)

    first_tasks = BackgroundTasks()
    first = trigger_daily_forecast(
        background_tasks=first_tasks,
        payload=None,
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["OperationalManager"]},
    )
    _run_background_tasks(first_tasks)
    session.expire_all()
    first_run = get_forecast_run(
        first.forecast_run_id,
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["OperationalManager"]},
    )

    second_tasks = BackgroundTasks()
    started = perf_counter()
    second = trigger_daily_forecast(
        background_tasks=second_tasks,
        payload=None,
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["OperationalManager"]},
    )
    _run_background_tasks(second_tasks)
    elapsed = perf_counter() - started
    session.expire_all()
    second_run = get_forecast_run(
        second.forecast_run_id,
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["OperationalManager"]},
    )

    assert first_run.result_type == "generated_new"
    assert second_run.result_type == "served_current"
    assert second_run.served_forecast_version_id == first_run.forecast_version_id
    assert elapsed < 30
