from __future__ import annotations

from datetime import datetime, timezone
from fastapi import BackgroundTasks, HTTPException
from fastapi.testclient import TestClient
import pytest

from app.api.routes.forecasts import get_current_forecast, get_forecast_run, trigger_daily_forecast
from app.clients.geomet_client import GeoMetClient
from app.clients.nager_date_client import NagerDateClient
from app.main import create_app
from app.core.auth import get_current_claims, require_operational_manager, require_planner_or_manager
from app.core.config import get_settings
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_model_repository import ForecastModelRepository
from app.services.forecast_training_service import ForecastTrainingService
from tests.conftest import build_token


class Creds:
    def __init__(self, token: str) -> None:
        self.credentials = token


def _run_background_tasks(tasks: BackgroundTasks) -> None:
    for task in tasks.tasks:
        task.func(*task.args, **task.kwargs)


def _seed_approved_cleaned_dataset(session) -> str:
    repository = DatasetRepository(session)
    version = repository.create_dataset_version(
        source_name="edmonton_311",
        run_id="seed-validation-run",
        candidate_id=None,
        record_count=2,
        records=[
            {
                "service_request_id": "seed-1",
                "requested_at": "2026-03-18T09:00:00Z",
                "category": "Roads",
            },
            {
                "service_request_id": "seed-2",
                "requested_at": "2026-03-18T10:00:00Z",
                "category": "Waste",
            },
        ],
        validation_status="approved",
        dataset_kind="cleaned",
        approved_by_validation_run_id="validation-1",
    )
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


@pytest.mark.contract
def test_trigger_requires_operational_manager_role() -> None:
    claims = get_current_claims(Creds(build_token(["Viewer"])))
    with pytest.raises(HTTPException) as exc:
        require_operational_manager(claims)
    assert exc.value.status_code == 403


@pytest.mark.contract
def test_forecast_routes_generate_and_read_current_forecast(session) -> None:
    _seed_approved_cleaned_dataset(session)
    _train_model(session)
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

    run_status = get_forecast_run(
        accepted.forecast_run_id,
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["CityPlanner"]},
    )
    current = get_current_forecast(
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["CityPlanner"]},
    )

    assert accepted.status == "running"
    assert run_status.result_type in {"generated_new", "served_current"}
    assert current.bucket_count == 24


@pytest.mark.contract
def test_http_get_forecast_run_status_binds_path_parameter(session) -> None:
    _seed_approved_cleaned_dataset(session)
    _train_model(session)
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

    app = create_app()
    client = TestClient(app)
    response = client.get(
        f"/api/v1/forecast-runs/{accepted.forecast_run_id}",
        headers={"Authorization": f"Bearer {build_token(['CityPlanner'])}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["forecastRunId"] == accepted.forecast_run_id
    assert payload["status"] in {"success", "running"}


@pytest.mark.contract
def test_run_status_and_current_forecast_require_reader_role(session) -> None:
    _seed_approved_cleaned_dataset(session)
    _train_model(session)
    claims = get_current_claims(Creds(build_token(["CityPlanner"])))
    resolved = require_planner_or_manager(claims)

    accepted = trigger_daily_forecast(
        background_tasks=BackgroundTasks(),
        payload=None,
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["OperationalManager"]},
    )

    assert "CityPlanner" in resolved["roles"]
    assert accepted.forecast_run_id
