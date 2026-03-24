from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from fastapi import BackgroundTasks
import pytest

from app.api.routes.forecasts import get_current_forecast, get_forecast_run, trigger_daily_forecast
from app.clients.geomet_client import GeoMetClient, GeoMetClientError
from app.clients.nager_date_client import NagerDateClient
from app.core.config import get_settings
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.forecast_model_repository import ForecastModelRepository
from app.services.forecast_training_service import ForecastTrainingService


def _run_background_tasks(tasks: BackgroundTasks) -> None:
    for task in tasks.tasks:
        task.func(*task.args, **task.kwargs)


def _seed_cleaned_dataset(session, *, with_geography: bool = False) -> None:
    repository = DatasetRepository(session)
    record = {
        "service_request_id": "seed-1",
        "requested_at": "2026-03-18T09:00:00Z",
        "category": "Roads",
    }
    if with_geography:
        record["ward"] = "Ward 1"
    version = repository.create_dataset_version(
        source_name="edmonton_311",
        run_id="seed-validation-run",
        candidate_id=None,
        record_count=1,
        records=[record],
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


@dataclass
class FailingGeoMetTransport:
    def fetch_hourly_conditions(self, horizon_start, horizon_end):
        raise GeoMetClientError("weather unavailable")


@pytest.mark.integration
def test_missing_approved_input_data_fails_without_current_marker(session) -> None:
    background_tasks = BackgroundTasks()
    accepted = trigger_daily_forecast(
        background_tasks=background_tasks,
        payload=None,
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["OperationalManager"]},
    )
    _run_background_tasks(background_tasks)
    session.expire_all()

    run = get_forecast_run(
        accepted.forecast_run_id,
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["OperationalManager"]},
    )

    assert run.status == "failed"
    assert run.result_type == "missing_input_data"


@pytest.mark.integration
def test_category_only_success_when_geography_unavailable(session) -> None:
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
    run = get_forecast_run(
        accepted.forecast_run_id,
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["OperationalManager"]},
    )

    assert run.status == "success"
    assert current.geography_scope == "category_only"
    assert elapsed < 120
