from __future__ import annotations

from datetime import datetime, timedelta, timezone
from fastapi import BackgroundTasks, HTTPException
import pytest

from app.api.routes.weekly_forecasts import get_current_weekly_forecast, get_weekly_forecast_run, trigger_weekly_forecast
from app.clients.geomet_client import GeoMetClient
from app.clients.nager_date_client import NagerDateClient
from app.core.auth import get_current_claims, require_operational_manager, require_planner_or_manager
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.weekly_forecast_run_repository import WeeklyForecastRunRepository
from tests.conftest import build_token


class Creds:
    def __init__(self, token: str) -> None:
        self.credentials = token


def _run_background_tasks(tasks: BackgroundTasks) -> None:
    for task in tasks.tasks:
        task.func(*task.args, **task.kwargs)


def _seed_cleaned_dataset(session, *, with_geography: bool = True) -> str:
    now = datetime.now(timezone.utc)
    base = now - timedelta(days=14)
    records = []
    for day_offset in range(10):
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


@pytest.mark.contract
def test_weekly_trigger_requires_operational_manager_role() -> None:
    claims = get_current_claims(Creds(build_token(["Viewer"])))
    with pytest.raises(HTTPException) as exc:
        require_operational_manager(claims)
    assert exc.value.status_code == 403


@pytest.mark.contract
def test_weekly_forecast_routes_generate_and_read_current_forecast(session) -> None:
    _seed_cleaned_dataset(session)
    background_tasks = BackgroundTasks()

    accepted = trigger_weekly_forecast(
        background_tasks=background_tasks,
        payload=None,
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["OperationalManager"]},
    )
    _run_background_tasks(background_tasks)
    session.expire_all()

    run_status = get_weekly_forecast_run(
        accepted.weekly_forecast_run_id,
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["CityPlanner"]},
    )
    current = get_current_weekly_forecast(
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["CityPlanner"]},
    )

    assert accepted.status == "running"
    assert run_status.result_type == "generated_new"
    assert current.weekly_forecast_version_id == run_status.generated_forecast_version_id
    assert current.bucket_count_days == 7
    assert len(current.buckets) == 14


@pytest.mark.contract
def test_weekly_run_status_route_binds_path_parameter_over_http(app_client, session, planner_headers) -> None:
    run = WeeklyForecastRunRepository(session).create_run(
        trigger_type="on_demand",
        source_cleaned_dataset_version_id="dataset-1",
        week_start_local=datetime(2026, 3, 23, tzinfo=timezone.utc),
        week_end_local=datetime(2026, 3, 29, 23, 59, 59, tzinfo=timezone.utc),
    )
    session.commit()

    response = app_client.get(f"/api/v1/forecast-runs/7-day/{run.weekly_forecast_run_id}", headers=planner_headers)

    assert response.status_code == 200
    assert response.json()["weeklyForecastRunId"] == run.weekly_forecast_run_id


@pytest.mark.contract
def test_weekly_run_status_and_current_forecast_require_reader_role(session) -> None:
    _seed_cleaned_dataset(session)
    claims = get_current_claims(Creds(build_token(["CityPlanner"])))
    resolved = require_planner_or_manager(claims)

    accepted = trigger_weekly_forecast(
        background_tasks=BackgroundTasks(),
        payload=None,
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["OperationalManager"]},
    )

    assert "CityPlanner" in resolved["roles"]
    assert accepted.weekly_forecast_run_id


@pytest.mark.contract
def test_weekly_route_returns_not_found_when_no_current_forecast(session) -> None:
    with pytest.raises(HTTPException) as exc:
        get_current_weekly_forecast(session=session, geomet_client=GeoMetClient(object()), nager_date_client=NagerDateClient(object()), _claims={"roles": ["CityPlanner"]})
    assert exc.value.status_code == 404
