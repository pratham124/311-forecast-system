from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import app.main as main_module
from app.api.routes.ingestion import get_client
from app.clients.edmonton_311 import Edmonton311Client, Edmonton311FetchResult
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.failure_notification_repository import FailureNotificationRepository
from app.repositories.run_repository import RunRepository
from app.pipelines.ingestion.run_ingestion import IngestionPipeline
from app.services.activation_guard_service import ActivationGuardService
from app.services.dataset_validation_service import DatasetValidationService
from app.services.ingestion_follow_on_jobs import launch_ingestion_follow_on_jobs
from app.services.ingestion_logging_service import IngestionLoggingService
from app.services.ingestion_query_service import IngestionQueryService
from app.services.scheduler_service import SchedulerService, build_ingestion_job


@pytest.mark.unit
def test_activation_guard_rejects_current_candidate() -> None:
    candidate = SimpleNamespace(is_current=True)
    with pytest.raises(AssertionError):
        ActivationGuardService().assert_not_current(candidate, None)


@pytest.mark.unit
def test_activation_guard_rejects_current_dataset_version() -> None:
    dataset_version = SimpleNamespace(is_current=True)
    with pytest.raises(AssertionError):
        ActivationGuardService().assert_not_current(None, dataset_version)


@pytest.mark.unit
def test_query_service_raises_for_missing_run(session) -> None:
    service = IngestionQueryService(
        RunRepository(session),
        DatasetRepository(session),
        CleanedDatasetRepository(session),
        FailureNotificationRepository(session),
    )
    with pytest.raises(HTTPException) as exc:
        service.get_run_status("missing")
    assert exc.value.status_code == 404


@pytest.mark.unit
def test_query_service_raises_for_missing_current_dataset(session) -> None:
    service = IngestionQueryService(
        RunRepository(session),
        DatasetRepository(session),
        CleanedDatasetRepository(session),
        FailureNotificationRepository(session),
    )
    with pytest.raises(HTTPException) as exc:
        service.get_current_dataset("edmonton_311")
    assert exc.value.status_code == 404


@pytest.mark.unit
def test_dataset_validation_covers_empty_and_missing_fields() -> None:
    service = DatasetValidationService()
    assert service.validate([]).passed is False
    result = service.validate([{"service_request_id": "1", "category": "Roads"}])
    assert result.passed is False
    assert "missing fields" in result.reason


@pytest.mark.unit
def test_scheduler_service_registers_and_triggers_job() -> None:
    scheduler = SchedulerService()
    scheduler.register_job("job-1", lambda: "ok")
    assert scheduler.trigger_job("job-1") == "ok"


@pytest.mark.unit
def test_scheduler_service_raises_for_missing_job() -> None:
    scheduler = SchedulerService()
    with pytest.raises(KeyError):
        scheduler.trigger_job("missing")


class FakeSchedulerEngine:
    def __init__(self) -> None:
        self.running = False
        self.added_jobs: list[tuple] = []

    def add_job(self, callback, trigger, id, replace_existing):
        self.added_jobs.append((callback, trigger, id, replace_existing))

    def start(self) -> None:
        self.running = True

    def shutdown(self, wait: bool = False) -> None:
        self.running = False


@pytest.mark.unit
def test_scheduler_service_registers_cron_job(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_scheduler = FakeSchedulerEngine()
    monkeypatch.setattr("app.services.scheduler_service.CronTrigger.from_crontab", lambda expr: f"cron:{expr}")
    service = SchedulerService(scheduler=fake_scheduler)

    service.register_cron_job("job-1", lambda: "ok", "*/5 * * * *")

    assert "job-1" in service.jobs
    assert fake_scheduler.added_jobs[0][1] == "cron:*/5 * * * *"


@pytest.mark.unit
def test_scheduler_service_start_and_shutdown() -> None:
    fake_scheduler = FakeSchedulerEngine()
    service = SchedulerService(scheduler=fake_scheduler)

    service.start()
    assert fake_scheduler.running is True
    service.shutdown()
    assert fake_scheduler.running is False


@pytest.mark.unit
def test_scheduler_service_start_and_shutdown_noop_paths() -> None:
    fake_scheduler = FakeSchedulerEngine()
    fake_scheduler.running = True
    service = SchedulerService(scheduler=fake_scheduler)

    service.start()
    assert fake_scheduler.running is True

    fake_scheduler.running = False
    service.shutdown()
    assert fake_scheduler.running is False


@pytest.mark.unit
def test_build_ingestion_job_runs_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    class FakeSession:
        def commit(self) -> None:
            calls.append("committed")

        def close(self) -> None:
            calls.append("closed")

    class FakePipeline:
        def __init__(self, session, client, logging_service) -> None:
            calls.append("created")

        def run(self, trigger_type: str, run_follow_on_jobs: bool = True):
            calls.append(trigger_type)
            calls.append(f"follow_on:{run_follow_on_jobs}")
            return SimpleNamespace(status="success", result_type="no_new_data")

    monkeypatch.setattr("app.services.scheduler_service.IngestionPipeline", FakePipeline)
    job = build_ingestion_job(lambda: FakeSession())

    result = job()

    assert result.status == "success"
    assert calls == ["created", "scheduled", "follow_on:False", "committed", "closed"]


@pytest.mark.unit
def test_launch_ingestion_follow_on_jobs_runs_sequentially(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr("app.services.ingestion_follow_on_jobs.get_session_factory", lambda: "session-factory")
    monkeypatch.setattr(
        "app.services.ingestion_follow_on_jobs.build_forecast_training_job",
        lambda session_factory: lambda: calls.append("forecast-model-training"),
    )
    monkeypatch.setattr(
        "app.services.ingestion_follow_on_jobs.build_forecast_job",
        lambda session_factory: lambda: calls.append("forecast-generation"),
    )
    monkeypatch.setattr(
        "app.services.ingestion_follow_on_jobs.build_weekly_forecast_training_job",
        lambda session_factory: lambda: calls.append("weekly-forecast-model-training"),
    )
    monkeypatch.setattr(
        "app.services.ingestion_follow_on_jobs.build_weekly_forecast_job",
        lambda session_factory: lambda: calls.append("weekly-forecast-generation"),
    )

    launch_ingestion_follow_on_jobs()

    assert calls == [
        "forecast-model-training",
        "forecast-generation",
        "weekly-forecast-model-training",
        "weekly-forecast-generation",
    ]


class NoCursorClient(Edmonton311Client):
    def __init__(self) -> None:
        pass

    def fetch_records(self, cursor: str | None) -> Edmonton311FetchResult:
        return Edmonton311FetchResult(
            result_type="new_data",
            records=[{"service_request_id": "1", "requested_at": "2026-03-02T00:00:00Z", "category": "Roads"}],
            cursor_value=None,
        )


@pytest.mark.unit
def test_get_client_returns_default_client() -> None:
    assert isinstance(get_client(), Edmonton311Client)


@pytest.mark.unit
def test_pipeline_can_succeed_without_cursor_advance(session) -> None:
    pipeline = IngestionPipeline(
        session,
        NoCursorClient(),
        IngestionLoggingService(__import__("logging").getLogger("test")),
    )

    result = pipeline.run()

    assert result.status == "success"
    assert result.cursor_advanced is False


@pytest.mark.unit
@pytest.mark.anyio
async def test_app_lifespan_registers_scheduler_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    class FakeSchedulerService:
        def register_cron_job(self, job_id, callback, cron_expression):
            events.append(f"register:{job_id}:{cron_expression}")

        def start(self):
            events.append("start")

        def shutdown(self):
            events.append("shutdown")

    monkeypatch.setenv("SCHEDULER_ENABLED", "true")
    monkeypatch.setenv("SCHEDULER_CRON", "*/10 * * * *")
    main_module.get_settings.cache_clear()
    monkeypatch.setattr(main_module, "SchedulerService", FakeSchedulerService)
    monkeypatch.setattr(main_module, "build_ingestion_job", lambda factory: lambda: None)

    app = main_module.create_app()
    async with app.router.lifespan_context(app):
        assert "start" in events

    assert "register:edmonton_311_ingestion:*/10 * * * *" in events
    assert "shutdown" in events
    main_module.get_settings.cache_clear()


@pytest.mark.unit
@pytest.mark.anyio
async def test_app_lifespan_skips_scheduler_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    class FakeSchedulerService:
        def register_cron_job(self, job_id, callback, cron_expression):
            events.append("register")

        def start(self):
            events.append("start")

        def shutdown(self):
            events.append("shutdown")

    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    main_module.get_settings.cache_clear()
    monkeypatch.setattr(main_module, "SchedulerService", FakeSchedulerService)

    app = main_module.create_app()
    async with app.router.lifespan_context(app):
        pass

    assert events == ["shutdown"]
    scheduler = FakeSchedulerService()
    scheduler.register_cron_job("job", lambda: None, "* * * * *")
    scheduler.start()
    assert events[-2:] == ["register", "start"]
    main_module.get_settings.cache_clear()
