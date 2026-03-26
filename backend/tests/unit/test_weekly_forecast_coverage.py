from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from fastapi import BackgroundTasks, FastAPI, HTTPException
import pytest

from app.api.routes import weekly_forecasts as weekly_routes
from app.main import lifespan
from app.models import CurrentForecastModelMarker
from app.pipelines.forecasting.weekly_feature_preparation import prepare_weekly_forecast_features
from app.pipelines.forecasting.weekly_demand_pipeline import _quantile
from app.clients.geomet_client import GeoMetClient, GeoMetClientError
from app.clients.nager_date_client import NagerDateClient
from app.pipelines.ingestion.approved_pipeline import ApprovedPipeline
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.forecast_model_repository import ForecastModelRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.repositories.weekly_forecast_run_repository import WeeklyForecastRunRepository
from app.schemas.weekly_forecast import WeeklyForecastTriggerRequest
from app.services import weekly_forecast_scheduler as scheduler_module
from app.services.forecast_training_service import ForecastModelStorageError
from app.services.week_window_service import WeekWindowService
from app.services.weekly_forecast_activation_service import WeeklyForecastActivationService, WeeklyForecastStorageError
from app.services.weekly_forecast_service import WeeklyForecastService
from app.services.weekly_forecast_training_service import WeeklyForecastTrainingService, _fetch_historical_weather


def _seed_dataset_version(session) -> str:
    repository = DatasetRepository(session)
    version = repository.create_dataset_version(
        source_name="edmonton_311",
        run_id="seed-run",
        candidate_id=None,
        record_count=1,
        records=[
            {
                "service_request_id": "seed-1",
                "requested_at": "2026-03-15T00:00:00Z",
                "category": "Roads",
            }
        ],
        validation_status="approved",
        dataset_kind="cleaned",
        approved_by_validation_run_id="validation-1",
    )
    session.commit()
    return version.dataset_version_id


@pytest.mark.unit
def test_weekly_route_dependency_factories_return_clients() -> None:
    assert isinstance(weekly_routes.get_geomet_client(), GeoMetClient)
    assert isinstance(weekly_routes.get_nager_date_client(), NagerDateClient)


@pytest.mark.unit
def test_prepare_weekly_forecast_features_ignores_invalid_weather_rows() -> None:
    week_start = datetime(2026, 3, 23, tzinfo=timezone.utc)
    prepared = prepare_weekly_forecast_features(
        dataset_records=[{"requested_at": "2026-03-18T10:00:00Z", "category": "Roads"}],
        week_start_local=week_start,
        week_end_local=week_start + timedelta(days=6, hours=23, minutes=59, seconds=59),
        timezone_name="America/Edmonton",
        weather_rows=[
            "bad-row",
            {"temperature_c": 2.0, "precipitation_mm": 1.0},
            {"timestamp": datetime(2026, 3, 23, 12, tzinfo=timezone.utc), "temperature_c": 3.0, "precipitation_mm": 0.5},
        ],
    )

    monday_context = prepared["target_context"][week_start.date()]
    assert monday_context["has_weather"] is True
    assert monday_context["avg_temperature_c"] == 3.0
    assert monday_context["total_precipitation_mm"] == 0.5


@pytest.mark.unit
def test_weekly_forecast_service_maps_geomet_enrichment_failures() -> None:
    settings = SimpleNamespace(
        source_name="edmonton_311",
        weekly_forecast_product_name="weekly_7_day_demand",
        weekly_forecast_timezone="America/Edmonton",
        weekly_forecast_history_days=56,
    )
    run = SimpleNamespace(
        weekly_forecast_run_id="run-1",
        status="running",
        source_cleaned_dataset_version_id="dataset-1",
        week_start_local=datetime(2026, 3, 23, tzinfo=timezone.utc),
        week_end_local=datetime(2026, 3, 29, 23, 59, 59, tzinfo=timezone.utc),
    )
    failed_calls: list[dict[str, object]] = []
    run_repo = SimpleNamespace(
        get_run=lambda _run_id: run,
        find_in_progress_run=lambda **kwargs: None,
        create_run=lambda **kwargs: run,
        finalize_failed=lambda run_id, **kwargs: failed_calls.append({"run_id": run_id, **kwargs}) or SimpleNamespace(status="failed", result_type=kwargs["result_type"]),
        finalize_reused=lambda *args, **kwargs: None,
        finalize_generated=lambda *args, **kwargs: None,
    )
    service = WeeklyForecastService(
        cleaned_dataset_repository=SimpleNamespace(
            get_current_approved_dataset=lambda _source_name: SimpleNamespace(dataset_version_id="dataset-1"),
            list_current_cleaned_records=lambda *args, **kwargs: [{"requested_at": "2026-03-20T10:00:00Z", "category": "Roads"}],
        ),
        weekly_forecast_run_repository=run_repo,
        weekly_forecast_repository=SimpleNamespace(find_current_for_week=lambda **kwargs: None),
        settings=settings,
        geomet_client=SimpleNamespace(fetch_forecast_hourly_conditions=lambda start, end: (_ for _ in ()).throw(GeoMetClientError("weather unavailable"))),
        nager_date_client=SimpleNamespace(fetch_holidays=lambda year: []),
    )

    failed = service.execute_run("run-1")

    assert failed.result_type == "engine_failure"
    assert failed_calls == [{
        "run_id": "run-1",
        "result_type": "engine_failure",
        "failure_reason": "weather unavailable",
        "summary": "weekly forecast enrichment failed",
    }]


@pytest.mark.unit
def test_trigger_weekly_forecast_rejects_invalid_payload(session) -> None:
    with pytest.raises(HTTPException) as exc:
        weekly_routes.trigger_weekly_forecast(
            background_tasks=BackgroundTasks(),
            payload=SimpleNamespace(trigger_type="scheduled"),
            session=session,
            geomet_client=GeoMetClient(object()),
            nager_date_client=NagerDateClient(object()),
            _claims={"roles": ["OperationalManager"]},
        )
    assert exc.value.status_code == 422


@pytest.mark.unit
def test_trigger_weekly_forecast_skips_background_task_for_deduplicated_run(session, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_run = SimpleNamespace(weekly_forecast_run_id="run-1")
    fake_service = SimpleNamespace(start_run=lambda trigger_type: (fake_run, False))
    monkeypatch.setattr(weekly_routes, "build_weekly_forecast_service", lambda _session, _geomet_client, _nager_date_client: fake_service)

    tasks = BackgroundTasks()
    accepted = weekly_routes.trigger_weekly_forecast(
        background_tasks=tasks,
        payload=None,
        session=session,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        _claims={"roles": ["OperationalManager"]},
    )

    assert accepted.weekly_forecast_run_id == "run-1"
    assert tasks.tasks == []


@pytest.mark.anyio
async def test_lifespan_registers_weekly_scheduler_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[tuple[str, object, object]] = []

    class FakeScheduler:
        def register_cron_job(self, name, job, cron):
            events.append((name, job, cron))

        def start(self):
            events.append(("start", None, None))

        def shutdown(self):
            events.append(("shutdown", None, None))

    settings = SimpleNamespace(
        scheduler_enabled=False,
        scheduler_cron="0 0 * * 0",
        forecast_model_scheduler_enabled=False,
        forecast_model_scheduler_cron="15 0 * * *",
        forecast_scheduler_enabled=False,
        forecast_scheduler_cron="0 * * * *",
        weekly_forecast_scheduler_enabled=True,
        weekly_forecast_scheduler_cron="0 1 * * 1",
        weekly_forecast_daily_regeneration_enabled=True,
        weekly_forecast_daily_regeneration_cron="0 2 * * *",
    )

    monkeypatch.setattr("app.main.get_settings", lambda: settings)
    monkeypatch.setattr("app.main.SchedulerService", FakeScheduler)
    monkeypatch.setattr("app.main.build_weekly_forecast_job", lambda _factory: "weekly-job")
    monkeypatch.setattr("app.main.build_weekly_regeneration_job", lambda _factory: "regen-job")

    app = FastAPI()
    app.state.session_factory = lambda: None
    async with lifespan(app):
        assert hasattr(app.state, "scheduler_service")

    assert ("weekly_demand_forecast", "weekly-job", "0 1 * * 1") in events
    assert ("weekly_demand_forecast_daily_regeneration", "regen-job", "0 2 * * *") in events
    assert ("start", None, None) in events
    assert ("shutdown", None, None) in events


@pytest.mark.unit
def test_prepare_weekly_forecast_features_skips_invalid_rows() -> None:
    week_start = datetime(2026, 3, 23, tzinfo=timezone.utc)
    prepared = prepare_weekly_forecast_features(
        dataset_records=[
            {"requested_at": None, "category": "Roads"},
            {"requested_at": "bad-timestamp", "category": "Roads"},
            {"requested_at": "2026-03-18T10:00:00Z", "category": ""},
        ],
        week_start_local=week_start,
        week_end_local=week_start + timedelta(days=6, hours=23, minutes=59, seconds=59),
        timezone_name="America/Edmonton",
    )

    assert prepared["scopes"] == []
    assert prepared["category_counts"] == {}


@pytest.mark.unit
def test_weekly_trigger_request_validator_rejects_invalid_trigger_type() -> None:
    with pytest.raises(ValueError):
        WeeklyForecastTriggerRequest(triggerType="scheduled")


@pytest.mark.unit
def test_week_window_service_accepts_naive_datetime() -> None:
    window = WeekWindowService("America/Edmonton").get_week_window(datetime(2026, 3, 25, 10, 0))
    assert window.week_start_local.tzinfo is not None


@pytest.mark.unit
def test_activation_service_rejects_empty_buckets() -> None:
    service = WeeklyForecastActivationService(repository=SimpleNamespace())
    with pytest.raises(WeeklyForecastStorageError):
        service.store_and_activate(
            forecast_product_name="weekly_7_day_demand",
            weekly_forecast_run_id="run-1",
            source_cleaned_dataset_version_id="dataset-1",
            week_start_local=datetime(2026, 3, 23, tzinfo=timezone.utc),
            week_end_local=datetime(2026, 3, 29, 23, 59, 59, tzinfo=timezone.utc),
            geography_scope="category_only",
            baseline_method="historical_daily_mean",
            summary="none",
            buckets=[],
        )


@pytest.mark.unit
def test_scheduler_job_skips_execute_when_run_already_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    class FakeSession:
        def commit(self):
            events.append("commit")

        def close(self):
            events.append("close")

    class FakeService:
        def __init__(self, **kwargs):
            pass

        def start_run(self, trigger_type: str):
            return SimpleNamespace(weekly_forecast_run_id="run-1"), False

        def execute_run(self, weekly_forecast_run_id: str):
            events.append(f"execute:{weekly_forecast_run_id}")

    monkeypatch.setattr(scheduler_module, "WeeklyForecastService", FakeService)
    monkeypatch.setattr(scheduler_module, "get_settings", lambda: SimpleNamespace())

    job = scheduler_module.build_weekly_forecast_job(lambda: FakeSession())
    run_id = job()

    assert run_id == "run-1"
    assert "execute:run-1" not in events
    assert events == ["commit", "close"]


@pytest.mark.unit
def test_weekly_forecast_repository_updates_marker_and_guards_missing_versions(session) -> None:
    dataset_version_id = _seed_dataset_version(session)
    run_repository = WeeklyForecastRunRepository(session)
    repository = WeeklyForecastRepository(session)
    week_start = datetime(2026, 3, 23, tzinfo=timezone.utc)
    week_end = datetime(2026, 3, 29, 23, 59, 59, tzinfo=timezone.utc)

    first_run = run_repository.create_run(
        trigger_type="on_demand",
        source_cleaned_dataset_version_id=dataset_version_id,
        week_start_local=week_start,
        week_end_local=week_end,
    )
    second_run = run_repository.create_run(
        trigger_type="on_demand",
        source_cleaned_dataset_version_id=dataset_version_id,
        week_start_local=week_start,
        week_end_local=week_end,
    )
    first_version = repository.create_forecast_version(
        weekly_forecast_run_id=first_run.weekly_forecast_run_id,
        source_cleaned_dataset_version_id=dataset_version_id,
        week_start_local=week_start,
        week_end_local=week_end,
        geography_scope="category_only",
        baseline_method="historical_daily_mean",
        summary="first",
    )
    repository.mark_version_stored(first_version.weekly_forecast_version_id)
    repository.activate_forecast(
        forecast_product_name="weekly_7_day_demand",
        weekly_forecast_version_id=first_version.weekly_forecast_version_id,
        source_cleaned_dataset_version_id=dataset_version_id,
        week_start_local=week_start,
        week_end_local=week_end,
        updated_by_run_id=first_run.weekly_forecast_run_id,
        geography_scope="category_only",
    )

    second_version = repository.create_forecast_version(
        weekly_forecast_run_id=second_run.weekly_forecast_run_id,
        source_cleaned_dataset_version_id=dataset_version_id,
        week_start_local=week_start,
        week_end_local=week_end,
        geography_scope="category_only",
        baseline_method="historical_daily_mean",
        summary="second",
    )
    repository.activate_forecast(
        forecast_product_name="weekly_7_day_demand",
        weekly_forecast_version_id=second_version.weekly_forecast_version_id,
        source_cleaned_dataset_version_id=dataset_version_id,
        week_start_local=week_start,
        week_end_local=week_end,
        updated_by_run_id=second_run.weekly_forecast_run_id,
        geography_scope="category_only",
    )

    marker = repository.get_current_marker("weekly_7_day_demand")
    session.expire_all()
    refreshed_first = repository.get_forecast_version(first_version.weekly_forecast_version_id)
    assert marker is not None
    assert marker.weekly_forecast_version_id == second_version.weekly_forecast_version_id
    assert marker.updated_by_run_id == second_run.weekly_forecast_run_id
    assert refreshed_first is not None
    assert refreshed_first.is_current is False
    assert repository.find_current_for_week(
        forecast_product_name="weekly_7_day_demand",
        week_start_local=week_start,
        week_end_local=week_end,
    ) is None
    with pytest.raises(ValueError):
        repository._require_version("missing")


@pytest.mark.unit
def test_weekly_forecast_run_repository_raises_for_missing_run(session) -> None:
    repository = WeeklyForecastRunRepository(session)
    with pytest.raises(ValueError):
        repository.finalize_failed(
            "missing",
            result_type="engine_failure",
            failure_reason="boom",
            summary="failed",
        )


@pytest.mark.unit
def test_weekly_forecast_service_handles_uncovered_guard_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(
        source_name="edmonton_311",
        weekly_forecast_product_name="weekly_7_day_demand",
        weekly_forecast_timezone="America/Edmonton",
        weekly_forecast_history_days=56,
    )
    failed_calls: list[tuple[str, str]] = []

    run_repo = SimpleNamespace(
        get_run=lambda run_id: None,
        find_in_progress_run=lambda **kwargs: None,
        create_run=lambda **kwargs: SimpleNamespace(weekly_forecast_run_id="run-1", status="running", source_cleaned_dataset_version_id="dataset-1", week_start_local=datetime(2026, 3, 23, tzinfo=timezone.utc), week_end_local=datetime(2026, 3, 29, 23, 59, 59, tzinfo=timezone.utc)),
        finalize_failed=lambda run_id, **kwargs: failed_calls.append((run_id, kwargs["failure_reason"])) or SimpleNamespace(status="failed", result_type=kwargs["result_type"]),
        finalize_reused=lambda *args, **kwargs: None,
        finalize_generated=lambda *args, **kwargs: None,
    )
    forecast_repo = SimpleNamespace(
        find_current_for_week=lambda **kwargs: None,
        get_current_marker=lambda _name: SimpleNamespace(weekly_forecast_version_id="version-1", source_cleaned_dataset_version_id="dataset-1", week_start_local=datetime(2026, 3, 23, tzinfo=timezone.utc), week_end_local=datetime(2026, 3, 29, 23, 59, 59, tzinfo=timezone.utc), geography_scope="category_only", updated_at=datetime(2026, 3, 23, tzinfo=timezone.utc), updated_by_run_id="run-1"),
        get_forecast_version=lambda _version_id: None,
        list_buckets=lambda _version_id: [],
    )
    cleaned_repo = SimpleNamespace(
        get_current_approved_dataset=lambda _source_name: SimpleNamespace(dataset_version_id="dataset-1"),
        list_current_cleaned_records=lambda *args, **kwargs: [],
    )
    service = WeeklyForecastService(
        cleaned_dataset_repository=cleaned_repo,
        weekly_forecast_run_repository=run_repo,
        weekly_forecast_repository=forecast_repo,
        settings=settings,
        geomet_client=SimpleNamespace(fetch_forecast_hourly_conditions=lambda start, end: []),
        nager_date_client=SimpleNamespace(fetch_holidays=lambda year: []),
    )

    with pytest.raises(ValueError):
        service.execute_run("missing")

    completed_run = SimpleNamespace(status="success")
    run_repo.get_run = lambda _run_id: completed_run
    assert service.execute_run("done") is completed_run

    pending_run = SimpleNamespace(
        weekly_forecast_run_id="run-1",
        status="running",
        source_cleaned_dataset_version_id="dataset-1",
        week_start_local=datetime(2026, 3, 23, tzinfo=timezone.utc),
        week_end_local=datetime(2026, 3, 29, 23, 59, 59, tzinfo=timezone.utc),
    )
    run_repo.get_run = lambda _run_id: pending_run
    failed = service.execute_run("run-1")
    assert failed.result_type == "missing_input_data"

    cleaned_repo.list_current_cleaned_records = lambda *args, **kwargs: [{"requested_at": "2026-03-20T10:00:00Z", "category": "Roads"}]
    monkeypatch.setattr("app.services.weekly_forecast_service.prepare_weekly_forecast_features", lambda **kwargs: {"scopes": []})
    failed_again = service.execute_run("run-1")
    assert failed_again.result_type == "missing_input_data"

    run_repo.get_run = lambda _run_id: None
    with pytest.raises(HTTPException) as exc:
        service.get_run_status("missing")
    assert exc.value.status_code == 404

    with pytest.raises(HTTPException) as exc:
        service.get_current_forecast()
    assert exc.value.status_code == 404


@pytest.mark.unit
def test_weekly_trigger_request_validator_accepts_on_demand() -> None:
    payload = WeeklyForecastTriggerRequest(triggerType="on_demand")
    assert payload.trigger_type == "on_demand"


@pytest.mark.unit
def test_weekly_forecast_repository_returns_none_when_marker_version_missing(session, monkeypatch: pytest.MonkeyPatch) -> None:
    dataset_version_id = _seed_dataset_version(session)
    run_repository = WeeklyForecastRunRepository(session)
    repository = WeeklyForecastRepository(session)
    week_start = datetime(2026, 3, 23, tzinfo=timezone.utc)
    week_end = datetime(2026, 3, 29, 23, 59, 59, tzinfo=timezone.utc)
    run = run_repository.create_run(
        trigger_type="on_demand",
        source_cleaned_dataset_version_id=dataset_version_id,
        week_start_local=week_start,
        week_end_local=week_end,
    )
    version = repository.create_forecast_version(
        weekly_forecast_run_id=run.weekly_forecast_run_id,
        source_cleaned_dataset_version_id=dataset_version_id,
        week_start_local=week_start,
        week_end_local=week_end,
        geography_scope="category_only",
        baseline_method="historical_daily_mean",
        summary="seed",
    )
    repository.mark_version_stored(version.weekly_forecast_version_id)
    repository.activate_forecast(
        forecast_product_name="weekly_7_day_demand",
        weekly_forecast_version_id=version.weekly_forecast_version_id,
        source_cleaned_dataset_version_id=dataset_version_id,
        week_start_local=week_start,
        week_end_local=week_end,
        updated_by_run_id=run.weekly_forecast_run_id,
        geography_scope="category_only",
    )
    monkeypatch.setattr(repository, "get_forecast_version", lambda _version_id: None)

    assert repository.find_current_for_week(
        forecast_product_name="weekly_7_day_demand",
        week_start_local=week_start,
        week_end_local=week_end,
    ) is None


@pytest.mark.unit
def test_weekly_forecast_repository_directly_handles_missing_current_version(session, monkeypatch: pytest.MonkeyPatch) -> None:
    repository = WeeklyForecastRepository(session)
    week_start = datetime(2026, 3, 23, tzinfo=timezone.utc)
    week_end = datetime(2026, 3, 29, 23, 59, 59, tzinfo=timezone.utc)
    marker = SimpleNamespace(
        week_start_local=week_start,
        week_end_local=week_end,
        weekly_forecast_version_id="missing-version",
    )
    monkeypatch.setattr(repository, "get_current_marker", lambda _name: marker)
    monkeypatch.setattr(repository, "get_forecast_version", lambda _version_id: None)

    assert repository.find_current_for_week(
        forecast_product_name="weekly_7_day_demand",
        week_start_local=week_start,
        week_end_local=week_end,
    ) is None


@pytest.mark.anyio
async def test_lifespan_registers_weekly_model_scheduler_job(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[tuple[str, object, object]] = []

    class FakeScheduler:
        def register_cron_job(self, name, job, cron):
            events.append((name, job, cron))

        def start(self):
            events.append(("start", None, None))

        def shutdown(self):
            events.append(("shutdown", None, None))

    settings = SimpleNamespace(
        scheduler_enabled=False,
        scheduler_cron="0 0 * * 0",
        forecast_model_scheduler_enabled=False,
        forecast_model_scheduler_cron="15 0 * * *",
        forecast_scheduler_enabled=False,
        forecast_scheduler_cron="0 * * * *",
        weekly_forecast_scheduler_enabled=False,
        weekly_forecast_scheduler_cron="0 1 * * 1",
        weekly_forecast_model_scheduler_enabled=True,
        weekly_forecast_model_scheduler_cron="30 0 * * 0",
        weekly_forecast_daily_regeneration_enabled=False,
        weekly_forecast_daily_regeneration_cron="0 2 * * *",
    )

    monkeypatch.setattr("app.main.get_settings", lambda: settings)
    monkeypatch.setattr("app.main.SchedulerService", FakeScheduler)
    monkeypatch.setattr("app.main.build_weekly_forecast_training_job", lambda _factory: "weekly-model-job")

    app = FastAPI()
    app.state.session_factory = lambda: None
    async with lifespan(app):
        assert hasattr(app.state, "scheduler_service")

    assert ("weekly_demand_forecast_model_training", "weekly-model-job", "30 0 * * 0") in events
    assert ("start", None, None) in events
    assert ("shutdown", None, None) in events


@pytest.mark.unit
def test_quantile_returns_zero_for_empty_values() -> None:
    assert _quantile([], 0.5) == 0.0


@pytest.mark.unit
def test_find_current_model_returns_none_for_product_mismatch(session, tmp_path) -> None:
    repository = ForecastModelRepository(session)
    run = repository.create_run(
        forecast_product_name="weekly_7_day_demand",
        trigger_type="scheduled",
        source_cleaned_dataset_version_id="dataset-1",
        training_window_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        training_window_end=datetime(2026, 3, 23, tzinfo=timezone.utc),
    )
    artifact = repository.create_artifact(
        forecast_product_name="weekly_7_day_demand",
        forecast_model_run_id=run.forecast_model_run_id,
        source_cleaned_dataset_version_id="dataset-1",
        geography_scope="category_only",
        model_family="historical_weekday_global",
        baseline_method="weekday_mean",
        feature_schema_version="weekly-v1",
        artifact_path=str(tmp_path / "weekly.pkl"),
        summary="stored",
    )
    session.add(CurrentForecastModelMarker(
        forecast_product_name="daily_1_day_demand",
        forecast_model_artifact_id=artifact.forecast_model_artifact_id,
        source_cleaned_dataset_version_id="dataset-1",
        training_window_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        training_window_end=datetime(2026, 3, 23, tzinfo=timezone.utc),
        updated_by_run_id=run.forecast_model_run_id,
        geography_scope="category_only",
    ))
    session.commit()

    assert repository.find_current_model("daily_1_day_demand") is None


@pytest.mark.unit
def test_approved_pipeline_logs_weekly_training_failure() -> None:
    logger = logging.getLogger("test.approved.weekly")
    captured: list[str] = []

    class Handler(logging.Handler):
        def emit(self, record):
            captured.append(record.getMessage())

    handler = Handler()
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)
    logger.propagate = False
    try:
        service = SimpleNamespace(
            store_and_approve_cleaned_dataset=lambda **kwargs: SimpleNamespace(dataset_version_id="dataset-1")
        )
        validation_repo = SimpleNamespace(finalize_run=lambda *args, **kwargs: None)
        hourly_training = SimpleNamespace(start_run=lambda trigger_type: SimpleNamespace(forecast_model_run_id="hourly-run"), execute_run=lambda run_id: None)
        weekly_training = SimpleNamespace(
            start_run=lambda trigger_type: SimpleNamespace(forecast_model_run_id="weekly-run"),
            execute_run=lambda run_id: (_ for _ in ()).throw(RuntimeError("weekly boom")),
        )
        hourly_forecast = SimpleNamespace(start_run=lambda trigger_type: SimpleNamespace(forecast_run_id="forecast-run"), execute_run=lambda run_id: None)
        weekly_forecast = SimpleNamespace(start_run=lambda trigger_type: (SimpleNamespace(weekly_forecast_run_id="weekly-forecast-run"), True), execute_run=lambda run_id: None)
        pipeline = ApprovedPipeline(service, validation_repo, hourly_training, weekly_training, hourly_forecast, weekly_forecast, logger)

        result = pipeline.approve(
            source_name="edmonton_311",
            ingestion_run_id="ingestion-1",
            source_dataset_version_id="source-1",
            validation_run_id="validation-1",
            cleaned_records=[{"category": "Roads"}],
            duplicate_group_count=0,
        )

        assert result == "dataset-1"
        assert any("weekly forecast model training trigger failed after approval" in message for message in captured)
    finally:
        logger.removeHandler(handler)


@pytest.mark.unit
def test_weekly_scheduler_training_job_executes_and_commits(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[tuple[str, object]] = []

    class FakeSession:
        def commit(self):
            events.append(("commit", None))

        def close(self):
            events.append(("close", None))

    class FakeTrainingService:
        def __init__(self, **kwargs):
            events.append(("init", kwargs["logger"].name))

        def start_run(self, trigger_type: str):
            events.append(("start_run", trigger_type))
            return SimpleNamespace(forecast_model_run_id="model-run-1")

        def execute_run(self, run_id: str):
            events.append(("execute_run", run_id))

    monkeypatch.setattr(scheduler_module, "WeeklyForecastTrainingService", FakeTrainingService)
    monkeypatch.setattr(scheduler_module, "get_settings", lambda: SimpleNamespace())

    job = scheduler_module.build_weekly_forecast_training_job(lambda: FakeSession())
    result = job()

    assert result == "model-run-1"
    assert ("start_run", "scheduled") in events
    assert ("execute_run", "model-run-1") in events
    assert events.count(("commit", None)) == 2
    assert ("close", None) in events


@pytest.mark.unit
def test_weekly_forecast_service_fails_when_current_model_is_stale() -> None:
    settings = SimpleNamespace(
        source_name="edmonton_311",
        weekly_forecast_product_name="weekly_7_day_demand",
        weekly_forecast_timezone="America/Edmonton",
        weekly_forecast_history_days=56,
    )
    run = SimpleNamespace(
        weekly_forecast_run_id="run-1",
        status="running",
        source_cleaned_dataset_version_id="dataset-1",
        week_start_local=datetime(2026, 3, 23, tzinfo=timezone.utc),
        week_end_local=datetime(2026, 3, 29, 23, 59, 59, tzinfo=timezone.utc),
    )
    failed_calls: list[dict[str, object]] = []
    run_repo = SimpleNamespace(
        get_run=lambda _run_id: run,
        find_in_progress_run=lambda **kwargs: None,
        create_run=lambda **kwargs: run,
        finalize_failed=lambda run_id, **kwargs: failed_calls.append({"run_id": run_id, **kwargs}) or SimpleNamespace(status="failed", result_type=kwargs["result_type"], failure_reason=kwargs["failure_reason"]),
        finalize_reused=lambda *args, **kwargs: None,
        finalize_generated=lambda *args, **kwargs: None,
    )
    service = WeeklyForecastService(
        cleaned_dataset_repository=SimpleNamespace(
            get_current_approved_dataset=lambda _source_name: SimpleNamespace(dataset_version_id="dataset-1"),
            list_current_cleaned_records=lambda *args, **kwargs: [{"requested_at": "2026-03-20T10:00:00Z", "category": "Roads"}],
        ),
        weekly_forecast_run_repository=run_repo,
        weekly_forecast_repository=SimpleNamespace(find_current_for_week=lambda **kwargs: None),
        forecast_model_repository=SimpleNamespace(find_current_model=lambda _product: SimpleNamespace(source_cleaned_dataset_version_id="dataset-2", artifact_path="unused.pkl")),
        geomet_client=SimpleNamespace(fetch_forecast_hourly_conditions=lambda start, end: []),
        nager_date_client=SimpleNamespace(fetch_holidays=lambda year: []),
        settings=settings,
    )

    failed = service.execute_run("run-1")

    assert failed.result_type == "engine_failure"
    assert failed_calls == [{
        "run_id": "run-1",
        "result_type": "engine_failure",
        "failure_reason": "Current trained weekly forecast model is stale for the approved dataset",
        "summary": "weekly forecast model unavailable",
    }]


@pytest.mark.unit
def test_fetch_historical_weather_falls_back_and_returns_empty() -> None:
    class HourlyOnly:
        def fetch_hourly_conditions(self, start, end):
            return [{"timestamp": start}]

    assert _fetch_historical_weather(HourlyOnly(), datetime(2026, 3, 1, tzinfo=timezone.utc), datetime(2026, 3, 2, tzinfo=timezone.utc)) == [{"timestamp": datetime(2026, 3, 1, tzinfo=timezone.utc)}]
    assert _fetch_historical_weather(object(), datetime(2026, 3, 1, tzinfo=timezone.utc), datetime(2026, 3, 2, tzinfo=timezone.utc)) == []


@pytest.mark.unit
def test_weekly_training_service_handles_missing_run_and_missing_records(tmp_path) -> None:
    settings = SimpleNamespace(
        source_name="edmonton_311",
        weekly_forecast_product_name="weekly_7_day_demand",
        weekly_forecast_timezone="America/Edmonton",
        weekly_forecast_history_days=56,
        weekly_forecast_model_artifact_dir=str(tmp_path / "weekly_models"),
    )
    missing_run_service = WeeklyForecastTrainingService(
        cleaned_dataset_repository=SimpleNamespace(get_current_approved_dataset=lambda source_name: None),
        forecast_model_repository=SimpleNamespace(get_run=lambda run_id: None),
        geomet_client=SimpleNamespace(),
        nager_date_client=SimpleNamespace(fetch_holidays=lambda year: []),
        settings=settings,
    )
    with pytest.raises(ValueError, match="Weekly forecast model run not found"):
        missing_run_service.execute_run("missing")

    failed_calls: list[dict[str, object]] = []
    run = SimpleNamespace(
        forecast_model_run_id="run-1",
        source_cleaned_dataset_version_id="dataset-1",
        training_window_start=datetime(2026, 1, 27, tzinfo=timezone.utc),
        training_window_end=datetime(2026, 3, 23, tzinfo=timezone.utc),
    )
    missing_records_service = WeeklyForecastTrainingService(
        cleaned_dataset_repository=SimpleNamespace(
            get_current_approved_dataset=lambda source_name: SimpleNamespace(dataset_version_id="dataset-1"),
            list_current_cleaned_records=lambda *args, **kwargs: [],
        ),
        forecast_model_repository=SimpleNamespace(
            get_run=lambda run_id: run,
            finalize_failed=lambda run_id, **kwargs: failed_calls.append({"run_id": run_id, **kwargs}) or SimpleNamespace(result_type=kwargs["result_type"]),
        ),
        geomet_client=SimpleNamespace(),
        nager_date_client=SimpleNamespace(fetch_holidays=lambda year: []),
        settings=settings,
    )

    failed = missing_records_service.execute_run("run-1")

    assert failed.result_type == "missing_input_data"
    assert failed_calls[0]["summary"] == "approved cleaned dataset contains no records"


@pytest.mark.unit
def test_weekly_training_service_maps_storage_and_model_lookup_failures(tmp_path) -> None:
    settings = SimpleNamespace(
        source_name="edmonton_311",
        weekly_forecast_product_name="weekly_7_day_demand",
        weekly_forecast_timezone="America/Edmonton",
        weekly_forecast_history_days=56,
        weekly_forecast_model_artifact_dir=str(tmp_path / "weekly_models"),
    )
    run = SimpleNamespace(
        forecast_model_run_id="run-1",
        source_cleaned_dataset_version_id="dataset-1",
        training_window_start=datetime(2026, 1, 27, tzinfo=timezone.utc),
        training_window_end=datetime(2026, 3, 23, tzinfo=timezone.utc),
    )
    failed_calls: list[dict[str, object]] = []
    service = WeeklyForecastTrainingService(
        cleaned_dataset_repository=SimpleNamespace(
            get_current_approved_dataset=lambda source_name: SimpleNamespace(dataset_version_id="dataset-1"),
            list_current_cleaned_records=lambda *args, **kwargs: [{"requested_at": "2026-03-20T10:00:00Z", "category": "Roads"}],
        ),
        forecast_model_repository=SimpleNamespace(
            get_run=lambda run_id: run,
            finalize_failed=lambda run_id, **kwargs: failed_calls.append({"run_id": run_id, **kwargs}) or SimpleNamespace(result_type=kwargs["result_type"]),
        ),
        geomet_client=SimpleNamespace(fetch_historical_hourly_conditions=lambda start, end: []),
        nager_date_client=SimpleNamespace(fetch_holidays=lambda year: []),
        settings=settings,
    )
    service._store_artifact = lambda artifact, path: (_ for _ in ()).throw(ForecastModelStorageError("disk full"))

    failed = service.execute_run("run-1")

    assert failed.result_type == "storage_failure"
    assert failed_calls[0]["failure_reason"] == "disk full"

    missing_model_service = WeeklyForecastTrainingService(
        cleaned_dataset_repository=SimpleNamespace(get_current_approved_dataset=lambda source_name: None),
        forecast_model_repository=SimpleNamespace(
            get_current_marker=lambda product: SimpleNamespace(forecast_model_artifact_id="artifact-1"),
            get_artifact=lambda artifact_id: SimpleNamespace(forecast_product_name="daily_1_day_demand"),
            find_current_model=lambda product: None,
        ),
        geomet_client=SimpleNamespace(),
        nager_date_client=SimpleNamespace(fetch_holidays=lambda year: []),
        settings=settings,
    )

    with pytest.raises(HTTPException, match="Current weekly forecast model not found"):
        missing_model_service.get_current_model()

    assert missing_model_service.load_current_artifact() is None
    with pytest.raises(ForecastModelStorageError, match="Weekly forecast model artifact file not found"):
        missing_model_service.load_artifact_bundle(str(tmp_path / "missing.pkl"))


@pytest.mark.unit
def test_approved_pipeline_skips_and_logs_hourly_training_paths() -> None:
    logger = logging.getLogger("test.approved.hourly")
    captured: list[str] = []

    class Handler(logging.Handler):
        def emit(self, record):
            captured.append(record.getMessage())

    handler = Handler()
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)
    logger.propagate = False
    try:
        service = SimpleNamespace(store_and_approve_cleaned_dataset=lambda **kwargs: SimpleNamespace(dataset_version_id="dataset-1"))
        validation_repo = SimpleNamespace(finalize_run=lambda *args, **kwargs: None)

        pipeline = ApprovedPipeline(service, validation_repo, None, None, None, None, logger)
        assert pipeline.approve(
            source_name="edmonton_311",
            ingestion_run_id="ingestion-1",
            source_dataset_version_id="source-1",
            validation_run_id="validation-1",
            cleaned_records=[{"category": "Roads"}],
            duplicate_group_count=0,
        ) == "dataset-1"
        assert captured == []

        hourly_training = SimpleNamespace(
            start_run=lambda trigger_type: SimpleNamespace(forecast_model_run_id="hourly-run"),
            execute_run=lambda run_id: (_ for _ in ()).throw(RuntimeError("hourly boom")),
        )
        pipeline = ApprovedPipeline(service, validation_repo, hourly_training, None, None, None, logger)
        assert pipeline.approve(
            source_name="edmonton_311",
            ingestion_run_id="ingestion-2",
            source_dataset_version_id="source-2",
            validation_run_id="validation-2",
            cleaned_records=[{"category": "Roads"}],
            duplicate_group_count=0,
        ) == "dataset-1"
        assert any("forecast model training trigger failed after approval" in message for message in captured)
    finally:
        logger.removeHandler(handler)


@pytest.mark.unit
def test_weekly_training_service_handles_missing_dataset_run_and_engine_failure(tmp_path) -> None:
    settings = SimpleNamespace(
        source_name="edmonton_311",
        weekly_forecast_product_name="weekly_7_day_demand",
        weekly_forecast_timezone="America/Edmonton",
        weekly_forecast_history_days=56,
        weekly_forecast_model_artifact_dir=str(tmp_path / "weekly_models"),
    )

    failed_calls: list[dict[str, object]] = []
    missing_dataset_run = SimpleNamespace(
        forecast_model_run_id="run-missing",
        source_cleaned_dataset_version_id=None,
        training_window_start=datetime(2026, 1, 27, tzinfo=timezone.utc),
        training_window_end=datetime(2026, 3, 23, tzinfo=timezone.utc),
    )
    missing_dataset_service = WeeklyForecastTrainingService(
        cleaned_dataset_repository=SimpleNamespace(get_current_approved_dataset=lambda source_name: None),
        forecast_model_repository=SimpleNamespace(
            get_run=lambda run_id: missing_dataset_run,
            finalize_failed=lambda run_id, **kwargs: failed_calls.append({"run_id": run_id, **kwargs}) or SimpleNamespace(result_type=kwargs["result_type"]),
        ),
        geomet_client=SimpleNamespace(),
        nager_date_client=SimpleNamespace(fetch_holidays=lambda year: []),
        settings=settings,
    )

    failed = missing_dataset_service.execute_run("run-missing")

    assert failed.result_type == "missing_input_data"
    assert failed_calls[0]["summary"] == "approved cleaned dataset missing"

    failed_calls.clear()
    failing_run = SimpleNamespace(
        forecast_model_run_id="run-engine",
        source_cleaned_dataset_version_id="dataset-1",
        training_window_start=datetime(2026, 1, 27, tzinfo=timezone.utc),
        training_window_end=datetime(2026, 3, 23, tzinfo=timezone.utc),
    )
    engine_failure_service = WeeklyForecastTrainingService(
        cleaned_dataset_repository=SimpleNamespace(
            get_current_approved_dataset=lambda source_name: SimpleNamespace(dataset_version_id="dataset-1"),
            list_current_cleaned_records=lambda *args, **kwargs: [{"requested_at": "2026-03-20T10:00:00Z", "category": "Roads"}],
        ),
        forecast_model_repository=SimpleNamespace(
            get_run=lambda run_id: failing_run,
            finalize_failed=lambda run_id, **kwargs: failed_calls.append({"run_id": run_id, **kwargs}) or SimpleNamespace(result_type=kwargs["result_type"]),
        ),
        geomet_client=SimpleNamespace(fetch_historical_hourly_conditions=lambda start, end: (_ for _ in ()).throw(GeoMetClientError("weather boom"))),
        nager_date_client=SimpleNamespace(fetch_holidays=lambda year: []),
        settings=settings,
    )

    failed = engine_failure_service.execute_run("run-engine")

    assert failed.result_type == "engine_failure"
    assert failed_calls[0]["failure_reason"] == "weather boom"


@pytest.mark.unit
def test_weekly_training_service_handles_generic_failure_and_store_artifact_oserror(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(
        source_name="edmonton_311",
        weekly_forecast_product_name="weekly_7_day_demand",
        weekly_forecast_timezone="America/Edmonton",
        weekly_forecast_history_days=56,
        weekly_forecast_model_artifact_dir=str(tmp_path / "weekly_models"),
    )
    run = SimpleNamespace(
        forecast_model_run_id="run-1",
        source_cleaned_dataset_version_id="dataset-1",
        training_window_start=datetime(2026, 1, 27, tzinfo=timezone.utc),
        training_window_end=datetime(2026, 3, 23, tzinfo=timezone.utc),
    )
    failed_calls: list[dict[str, object]] = []
    generic_failure_service = WeeklyForecastTrainingService(
        cleaned_dataset_repository=SimpleNamespace(
            get_current_approved_dataset=lambda source_name: SimpleNamespace(dataset_version_id="dataset-1"),
            list_current_cleaned_records=lambda *args, **kwargs: [{"requested_at": "2026-03-20T10:00:00Z", "category": "Roads"}],
        ),
        forecast_model_repository=SimpleNamespace(
            get_run=lambda run_id: run,
            finalize_failed=lambda run_id, **kwargs: failed_calls.append({"run_id": run_id, **kwargs}) or SimpleNamespace(result_type=kwargs["result_type"]),
        ),
        geomet_client=SimpleNamespace(fetch_historical_hourly_conditions=lambda start, end: []),
        nager_date_client=SimpleNamespace(fetch_holidays=lambda year: []),
        settings=settings,
    )
    monkeypatch.setattr(generic_failure_service.pipeline, "fit", lambda prepared: (_ for _ in ()).throw(RuntimeError("fit boom")))

    failed = generic_failure_service.execute_run("run-1")

    assert failed.result_type == "engine_failure"
    assert failed_calls[0]["failure_reason"] == "fit boom"

    storage_service = WeeklyForecastTrainingService(
        cleaned_dataset_repository=SimpleNamespace(get_current_approved_dataset=lambda source_name: None),
        forecast_model_repository=SimpleNamespace(find_current_model=lambda product: None),
        geomet_client=SimpleNamespace(),
        nager_date_client=SimpleNamespace(fetch_holidays=lambda year: []),
        settings=settings,
    )

    class BrokenPath:
        def open(self, *args, **kwargs):
            raise OSError("cannot open")

    artifact = SimpleNamespace()
    with pytest.raises(ForecastModelStorageError, match="Unable to persist weekly forecast model artifact"):
        storage_service._store_artifact(artifact, BrokenPath())


@pytest.mark.unit
def test_approved_pipeline_logs_forecast_generation_failure_and_skips_weekly_execute() -> None:
    logger = logging.getLogger("test.approved.forecast_generation")
    captured: list[str] = []
    weekly_execute_calls: list[str] = []

    class Handler(logging.Handler):
        def emit(self, record):
            captured.append(record.getMessage())

    handler = Handler()
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)
    logger.propagate = False
    try:
        service = SimpleNamespace(store_and_approve_cleaned_dataset=lambda **kwargs: SimpleNamespace(dataset_version_id="dataset-1"))
        validation_repo = SimpleNamespace(finalize_run=lambda *args, **kwargs: None)
        hourly_forecast = SimpleNamespace(
            start_run=lambda trigger_type: SimpleNamespace(forecast_run_id="forecast-run"),
            execute_run=lambda run_id: (_ for _ in ()).throw(RuntimeError("forecast boom")),
        )
        weekly_forecast = SimpleNamespace(
            start_run=lambda trigger_type: (SimpleNamespace(weekly_forecast_run_id="weekly-forecast-run"), False),
            execute_run=lambda run_id: weekly_execute_calls.append(run_id),
        )
        pipeline = ApprovedPipeline(service, validation_repo, None, None, hourly_forecast, weekly_forecast, logger)

        assert pipeline.approve(
            source_name="edmonton_311",
            ingestion_run_id="ingestion-1",
            source_dataset_version_id="source-1",
            validation_run_id="validation-1",
            cleaned_records=[{"category": "Roads"}],
            duplicate_group_count=0,
        ) == "dataset-1"

        assert weekly_execute_calls == []
        assert any("forecast generation trigger failed after approval" in message for message in captured)
    finally:
        logger.removeHandler(handler)


@pytest.mark.unit
def test_approved_pipeline_logs_weekly_forecast_generation_failure() -> None:
    logger = logging.getLogger("test.approved.weekly_generation")
    captured: list[str] = []

    class Handler(logging.Handler):
        def emit(self, record):
            captured.append(record.getMessage())

    handler = Handler()
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)
    logger.propagate = False
    try:
        service = SimpleNamespace(store_and_approve_cleaned_dataset=lambda **kwargs: SimpleNamespace(dataset_version_id="dataset-1"))
        validation_repo = SimpleNamespace(finalize_run=lambda *args, **kwargs: None)
        weekly_forecast = SimpleNamespace(
            start_run=lambda trigger_type: (_ for _ in ()).throw(RuntimeError("weekly forecast boom")),
            execute_run=lambda run_id: None,
        )
        pipeline = ApprovedPipeline(service, validation_repo, None, None, None, weekly_forecast, logger)

        assert pipeline.approve(
            source_name="edmonton_311",
            ingestion_run_id="ingestion-2",
            source_dataset_version_id="source-2",
            validation_run_id="validation-2",
            cleaned_records=[{"category": "Roads"}],
            duplicate_group_count=0,
        ) == "dataset-1"

        assert any("weekly forecast generation trigger failed after approval" in message for message in captured)
    finally:
        logger.removeHandler(handler)
