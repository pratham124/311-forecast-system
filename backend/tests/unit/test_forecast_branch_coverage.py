from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from fastapi import BackgroundTasks, HTTPException
import httpx
from pydantic import ValidationError
import numpy as np
import pytest

from app.api.routes import forecasts as forecast_routes
from app.clients.geomet_client import GeoMetClient, GeoMetClientError, GeoMetHttpTransport
from app.clients.nager_date_client import NagerDateClient, NagerDateClientError, NagerDateHttpTransport
from app.main import create_app
from app import main as main_module
from app.models import CleanedCurrentRecord, CurrentDatasetMarker, DatasetRecord, DatasetVersion, ForecastRun, ForecastVersion
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.forecast_run_repository import ForecastRunRepository
from app.repositories import models as repository_models
from app.schemas.forecast import ForecastTriggerRequest
from app.services import forecast_scheduler
from app.services.forecast_activation_service import ForecastActivationService, ForecastStorageError
from app.services.forecast_service import ForecastService


@pytest.mark.unit
def test_forecast_route_helpers_and_invalid_payload(session) -> None:
    assert isinstance(forecast_routes.get_geomet_client(), GeoMetClient)
    assert isinstance(forecast_routes.get_nager_date_client(), NagerDateClient)

    with pytest.raises(HTTPException) as exc:
        forecast_routes.trigger_daily_forecast(
            background_tasks=BackgroundTasks(),
            payload=SimpleNamespace(trigger_type="scheduled"),
            session=session,
            geomet_client=GeoMetClient(),
            nager_date_client=NagerDateClient(),
            _claims={"roles": ["OperationalManager"]},
        )
    assert exc.value.status_code == 422


@pytest.mark.unit
def test_clients_use_transport_specific_methods() -> None:
    class GeoTransport:
        def fetch_hourly_conditions(self, horizon_start, horizon_end):
            return [{"timestamp": horizon_start, "temperature_c": 1.0, "precipitation_mm": 2.0}]

    class GeoFallbackTransport:
        def fetch(self, horizon_start, horizon_end):
            return [{"timestamp": horizon_start, "temperature_c": 3.0, "precipitation_mm": 4.0}]

    class HolidayTransport:
        def fetch_holidays(self, year, country_code):
            return [{"date": f"{year}-07-01", "name": "Holiday", "countryCode": country_code}]

    class HolidayFallbackTransport:
        def fetch(self, year, country_code):
            return [{"date": f"{year}-12-25", "name": "Holiday", "countryCode": country_code}]

    start = datetime(2026, 3, 22, tzinfo=timezone.utc)
    end = start + timedelta(hours=1)

    assert GeoMetClient(GeoTransport()).fetch_hourly_conditions(start, end)[0]["temperature_c"] == 1.0
    assert GeoMetClient(GeoFallbackTransport()).fetch_hourly_conditions(start, end)[0]["temperature_c"] == 3.0
    assert NagerDateClient(HolidayTransport()).fetch_holidays(2026)[0]["date"] == "2026-07-01"
    assert NagerDateClient(HolidayFallbackTransport()).fetch_holidays(2026)[0]["date"] == "2026-12-25"


@pytest.mark.unit
def test_cleaned_dataset_repository_covers_missing_invalid_and_fallback_json(session) -> None:
    repository = CleanedDatasetRepository(session)

    assert repository.get_current_approved_dataset("missing-source") is None
    assert repository.list_current_cleaned_records("missing-source") == []

    session.add(CurrentDatasetMarker(source_name="edmonton_311", dataset_version_id="missing", updated_by_run_id="run-1", record_count=0))
    session.commit()
    assert repository.get_current_approved_dataset("edmonton_311") is None

    dataset = DatasetVersion(
        dataset_version_id="dataset-1",
        source_name="edmonton_311",
        ingestion_run_id="ingestion-1",
        candidate_dataset_id=None,
        source_dataset_version_id=None,
        record_count=1,
        validation_status="pending",
        storage_status="stored",
        dataset_kind="source",
        duplicate_group_count=0,
        approved_by_validation_run_id=None,
        is_current=False,
    )
    session.add(dataset)
    marker = session.get(CurrentDatasetMarker, "edmonton_311")
    marker.dataset_version_id = "dataset-1"
    session.add(
        DatasetRecord(
            dataset_version_id="dataset-1",
            source_record_id="record-1",
            requested_at="2026-03-18T09:00:00Z",
            category="Roads",
            record_payload="{not-json}",
        )
    )
    session.commit()

    assert repository.get_current_approved_dataset("edmonton_311") is None
    assert repository.list_dataset_records("dataset-1")[0]["service_request_id"] == "record-1"

    repository.upsert_current_cleaned_records(
        source_name="edmonton_311",
        ingestion_run_id="run-1",
        source_dataset_version_id="dataset-1",
        approved_dataset_version_id="dataset-1",
        approved_by_validation_run_id="validation-1",
        cleaned_records=[
            {
                "service_request_id": "record-1",
                "requested_at": "2026-03-18T09:00:00Z",
                "category": "Roads",
                "ward": "Ward 1",
            }
        ],
    )
    listed = repository.list_current_cleaned_records("edmonton_311")
    assert listed[0]["service_request_id"] == "record-1"
    assert repository.count_current_cleaned_records("edmonton_311") == 1

    repository.upsert_current_cleaned_records(
        source_name="edmonton_311",
        ingestion_run_id="run-2",
        source_dataset_version_id="dataset-2",
        approved_dataset_version_id="dataset-2",
        approved_by_validation_run_id="validation-2",
        cleaned_records=[
            {
                "service_request_id": "record-1",
                "requested_at": "2026-03-18T10:00:00Z",
                "category": "Transit",
                "district": "NW",
            }
        ],
    )
    updated_row = session.get(CleanedCurrentRecord, "record-1")
    assert updated_row is not None
    assert updated_row.category == "Transit"
    assert updated_row.geography_key == "NW"
    assert updated_row.last_updated_ingestion_run_id == "run-2"
    assert updated_row.last_approved_dataset_version_id == "dataset-2"

    repository.upsert_current_cleaned_records(
        source_name="edmonton_311",
        ingestion_run_id="run-3",
        source_dataset_version_id="dataset-3",
        approved_dataset_version_id="dataset-3",
        approved_by_validation_run_id="validation-3",
        cleaned_records=[{"service_request_id": "   ", "requested_at": "2026-03-18T10:00:00Z", "category": "Roads"}],
    )
    assert repository.count_current_cleaned_records("edmonton_311") == 1

    updated_row.record_payload = "{bad-json}"
    session.commit()
    malformed = repository.list_current_cleaned_records("edmonton_311")
    assert malformed[0]["service_request_id"] == "record-1"
    assert malformed[0]["geography_key"] == "NW"

    session.add(
        CleanedCurrentRecord(
            service_request_id="plain-1",
            source_name="plain-source",
            requested_at="2026-03-18T11:00:00Z",
            category="Roads",
            geography_key=None,
            record_payload="{still-bad-json}",
            first_seen_ingestion_run_id="run-plain",
            last_updated_ingestion_run_id="run-plain",
            source_dataset_version_id="dataset-plain",
            approved_by_validation_run_id="validation-plain",
            last_approved_dataset_version_id="dataset-plain",
        )
    )
    session.commit()
    assert repository.list_current_cleaned_records("plain-source") == [
        {
            "service_request_id": "plain-1",
            "requested_at": "2026-03-18T11:00:00Z",
            "category": "Roads",
        }
    ]

    cleaned_dataset = DatasetVersion(
        dataset_version_id="dataset-cleaned",
        source_name="legacy-source",
        ingestion_run_id="ingestion-legacy",
        candidate_dataset_id=None,
        source_dataset_version_id=None,
        record_count=1,
        validation_status="approved",
        storage_status="stored",
        dataset_kind="cleaned",
        duplicate_group_count=0,
        approved_by_validation_run_id="validation-legacy",
        is_current=True,
    )
    session.add_all(
        [
            cleaned_dataset,
            CurrentDatasetMarker(
                source_name="legacy-source",
                dataset_version_id="dataset-cleaned",
                updated_by_run_id="run-legacy",
                record_count=1,
            ),
            DatasetRecord(
                dataset_version_id="dataset-cleaned",
                source_record_id="legacy-1",
                requested_at="2026-03-18T08:00:00Z",
                category="Roads",
                record_payload='{"service_request_id":"legacy-1","requested_at":"2026-03-18T08:00:00Z","category":"Roads"}',
            ),
        ]
    )
    session.commit()

    legacy = repository.list_current_cleaned_records(
        "legacy-source",
        start_time=datetime(2026, 3, 18, 7, tzinfo=timezone.utc),
        end_time=datetime(2026, 3, 18, 9, tzinfo=timezone.utc),
    )
    assert legacy == [
        {
            "service_request_id": "legacy-1",
            "requested_at": "2026-03-18T08:00:00Z",
            "category": "Roads",
        }
    ]


@pytest.mark.unit
def test_ingestion_model_helper_and_factory_branches() -> None:
    from app.models import ingestion_models as module

    assert module._normalize_requested_at("") == ""
    assert module._normalize_requested_at("not-a-date") == "not-a-date"
    assert module._extract_geography_key({"district": "  NW  "}) == "NW"
    assert module._extract_geography_key({"category": "Roads"}) is None

    dataset_record = module.DatasetRecord.from_normalized_row(
        "dataset-1",
        {"service_request_id": "SR-0", "requested_at": "2026-03-18T09:00:00-06:00", "category": "Roads"},
    )
    assert dataset_record.requested_at == "2026-03-18T15:00:00Z"

    record = module.CleanedCurrentRecord.from_normalized_row(
        source_name="edmonton_311",
        ingestion_run_id="run-1",
        source_dataset_version_id="source-1",
        approved_dataset_version_id="approved-1",
        approved_by_validation_run_id="validation-1",
        record={
            "service_request_id": "SR-1",
            "requested_at": "2026-03-18T09:00:00-06:00",
            "category": "Roads",
            "neighbourhood": "Downtown",
        },
    )
    assert record.requested_at == "2026-03-18T15:00:00Z"
    assert record.geography_key == "Downtown"
    assert record.last_approved_dataset_version_id == "approved-1"

    from app.repositories import cleaned_dataset_repository as repository_module
    assert repository_module._to_requested_at_string(datetime(2026, 3, 18, 9)) == "2026-03-18T09:00:00Z"
    assert repository_module._extract_geography_key({"category": "Roads"}) is None


@pytest.mark.unit
def test_forecast_repository_update_and_error_paths(session) -> None:
    repository = ForecastRepository(session)
    now = datetime(2026, 3, 22, tzinfo=timezone.utc)

    current = ForecastVersion(
        forecast_version_id="forecast-current",
        forecast_run_id="run-current",
        source_cleaned_dataset_version_id="dataset-1",
        horizon_start=now,
        horizon_end=now + timedelta(hours=24),
        geography_scope="category_only",
        baseline_method="baseline",
        storage_status="stored",
        is_current=True,
    )
    next_version = ForecastVersion(
        forecast_version_id="forecast-next",
        forecast_run_id="run-next",
        source_cleaned_dataset_version_id="dataset-1",
        horizon_start=now,
        horizon_end=now + timedelta(hours=24),
        geography_scope="category_only",
        baseline_method="baseline",
        storage_status="stored",
        is_current=False,
    )
    marker = repository_models.CurrentForecastMarker(
        forecast_product_name="daily_1_day_demand",
        forecast_version_id="forecast-current",
        source_cleaned_dataset_version_id="dataset-1",
        horizon_start=now,
        horizon_end=now + timedelta(hours=24),
        updated_by_run_id="run-current",
        geography_scope="category_only",
    )
    session.add_all([current, next_version, marker])
    session.commit()

    repository.activate_forecast(
        forecast_product_name="daily_1_day_demand",
        forecast_version_id="forecast-next",
        source_cleaned_dataset_version_id="dataset-2",
        horizon_start=now + timedelta(hours=1),
        horizon_end=now + timedelta(hours=25),
        updated_by_run_id="run-next",
        geography_scope="category_and_geography",
    )
    session.commit()

    updated_marker = repository.get_current_marker("daily_1_day_demand")
    assert updated_marker.forecast_version_id == "forecast-next"
    assert repository.find_current_for_horizon(
        forecast_product_name="daily_1_day_demand",
        horizon_start=now,
        horizon_end=now + timedelta(hours=24),
    ) is None

    next_version.storage_status = "pending"
    session.commit()
    assert repository.find_current_for_horizon(
        forecast_product_name="daily_1_day_demand",
        horizon_start=now + timedelta(hours=1),
        horizon_end=now + timedelta(hours=25),
    ) is None

    with pytest.raises(ValueError):
        repository._require_version("missing")


@pytest.mark.unit
def test_forecast_run_repository_missing_run_raises(session) -> None:
    repository = ForecastRunRepository(session)
    with pytest.raises(ValueError):
        repository.finalize_failed(
            "missing",
            result_type="engine_failure",
            failure_reason="boom",
            summary="failed",
        )


@pytest.mark.unit
def test_forecast_schema_activation_and_models_export() -> None:
    with pytest.raises(ValidationError):
        ForecastTriggerRequest(triggerType="scheduled")

    with pytest.raises(ForecastStorageError):
        ForecastActivationService(repository=SimpleNamespace()).store_and_activate(
            forecast_product_name="daily_1_day_demand",
            forecast_run_id="run-1",
            source_cleaned_dataset_version_id="dataset-1",
            horizon_start=datetime(2026, 3, 22, tzinfo=timezone.utc),
            horizon_end=datetime(2026, 3, 23, tzinfo=timezone.utc),
            geography_scope="category_only",
            baseline_method="baseline",
            summary="summary",
            buckets=[{"bucket_start": datetime(2026, 3, 22, hour, tzinfo=timezone.utc)} for hour in range(23)],
        )

    assert repository_models.ForecastRun is ForecastRun


@pytest.mark.unit
def test_forecast_scheduler_job_runs_and_closes_session(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    class FakeSession:
        def commit(self):
            events.append("commit")

        def close(self):
            events.append("close")

    class FakeService:
        def __init__(self, **kwargs):
            events.append("service")

        def start_run(self, trigger_type: str):
            events.append(f"start:{trigger_type}")
            return SimpleNamespace(forecast_run_id="run-123")

        def execute_run(self, forecast_run_id: str):
            events.append(f"execute:{forecast_run_id}")

    monkeypatch.setattr(forecast_scheduler, "ForecastService", FakeService)
    monkeypatch.setattr(forecast_scheduler, "CleanedDatasetRepository", lambda session: "cleaned")
    monkeypatch.setattr(forecast_scheduler, "ForecastRunRepository", lambda session: "runs")
    monkeypatch.setattr(forecast_scheduler, "ForecastRepository", lambda session: "forecast")
    monkeypatch.setattr(forecast_scheduler, "get_settings", lambda: SimpleNamespace(source_name="edmonton_311"))

    job = forecast_scheduler.build_forecast_job(lambda: FakeSession())
    assert job() == "run-123"
    assert events == ["service", "start:scheduled", "commit", "execute:run-123", "commit", "close"]


@pytest.mark.unit
def test_forecast_service_failure_and_not_found_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(source_name="edmonton_311", forecast_product_name="daily_1_day_demand")

    class RunRepo:
        def __init__(self, run=None):
            self.run = run
            self.failed = None

        def get_run(self, forecast_run_id):
            return self.run

        def finalize_failed(self, forecast_run_id, **kwargs):
            self.failed = kwargs
            return kwargs

    missing_service = ForecastService(
        cleaned_dataset_repository=SimpleNamespace(get_current_approved_dataset=lambda source_name: None),
        forecast_run_repository=RunRepo(),
        forecast_repository=SimpleNamespace(),
        geomet_client=GeoMetClient(),
        nager_date_client=NagerDateClient(),
        settings=settings,
    )
    with pytest.raises(ValueError):
        missing_service.execute_run("missing")

    run = SimpleNamespace(
        forecast_run_id="run-1",
        source_cleaned_dataset_version_id="dataset-1",
        requested_horizon_start=datetime(2026, 3, 22, tzinfo=timezone.utc),
        requested_horizon_end=datetime(2026, 3, 23, tzinfo=timezone.utc),
    )
    run_repo = RunRepo(run)
    empty_service = ForecastService(
        cleaned_dataset_repository=SimpleNamespace(list_current_cleaned_records=lambda source_name, **kwargs: []),
        forecast_run_repository=run_repo,
        forecast_repository=SimpleNamespace(find_current_for_horizon=lambda **kwargs: None),
        geomet_client=GeoMetClient(),
        nager_date_client=NagerDateClient(),
        settings=settings,
    )
    assert empty_service.execute_run("run-1")["result_type"] == "missing_input_data"

    engine_run_repo = RunRepo(run)
    engine_service = ForecastService(
        cleaned_dataset_repository=SimpleNamespace(list_current_cleaned_records=lambda source_name, **kwargs: [{"category": "Roads"}]),
        forecast_run_repository=engine_run_repo,
        forecast_repository=SimpleNamespace(find_current_for_horizon=lambda **kwargs: None),
        geomet_client=SimpleNamespace(fetch_hourly_conditions=lambda start, end: (_ for _ in ()).throw(GeoMetClientError("boom"))),
        nager_date_client=NagerDateClient(),
        settings=settings,
    )
    assert engine_service.execute_run("run-1")["result_type"] == "engine_failure"

    storage_run_repo = RunRepo(run)
    storage_service = ForecastService(
        cleaned_dataset_repository=SimpleNamespace(list_current_cleaned_records=lambda source_name, **kwargs: [{"category": "Roads"}]),
        forecast_run_repository=storage_run_repo,
        forecast_repository=SimpleNamespace(find_current_for_horizon=lambda **kwargs: None),
        geomet_client=SimpleNamespace(
            fetch_historical_hourly_conditions=lambda start, end: [],
            fetch_forecast_hourly_conditions=lambda start, end: [],
        ),
        nager_date_client=NagerDateClient(),
        settings=settings,
    )
    storage_service.activation_service = SimpleNamespace(
        store_and_activate=lambda **kwargs: (_ for _ in ()).throw(ForecastStorageError("storage"))
    )
    assert storage_service.execute_run("run-1")["result_type"] == "storage_failure"

    generic_run_repo = RunRepo(run)
    generic_service = ForecastService(
        cleaned_dataset_repository=SimpleNamespace(list_current_cleaned_records=lambda source_name, **kwargs: [{"category": "Roads"}]),
        forecast_run_repository=generic_run_repo,
        forecast_repository=SimpleNamespace(find_current_for_horizon=lambda **kwargs: None),
        geomet_client=SimpleNamespace(
            fetch_historical_hourly_conditions=lambda start, end: [],
            fetch_forecast_hourly_conditions=lambda start, end: [],
        ),
        nager_date_client=NagerDateClient(),
        settings=settings,
    )
    monkeypatch.setattr(generic_service, "pipeline", SimpleNamespace(run=lambda prepared: (_ for _ in ()).throw(RuntimeError("unexpected"))))
    assert generic_service.execute_run("run-1")["result_type"] == "engine_failure"

    with pytest.raises(HTTPException):
        missing_service.get_run_status("missing")

    missing_current_service = ForecastService(
        cleaned_dataset_repository=SimpleNamespace(),
        forecast_run_repository=RunRepo(run),
        forecast_repository=SimpleNamespace(get_current_marker=lambda product: None),
        geomet_client=GeoMetClient(),
        nager_date_client=NagerDateClient(),
        settings=settings,
    )
    with pytest.raises(HTTPException):
        missing_current_service.get_current_forecast()

    marker = SimpleNamespace(
        forecast_version_id="forecast-1",
        source_cleaned_dataset_version_id="dataset-1",
        horizon_start=datetime(2026, 3, 22, tzinfo=timezone.utc),
        horizon_end=datetime(2026, 3, 23, tzinfo=timezone.utc),
        geography_scope="category_only",
        updated_at=datetime(2026, 3, 22, tzinfo=timezone.utc),
        updated_by_run_id="run-1",
    )
    missing_version_service = ForecastService(
        cleaned_dataset_repository=SimpleNamespace(),
        forecast_run_repository=RunRepo(run),
        forecast_repository=SimpleNamespace(
            get_current_marker=lambda product: marker,
            get_forecast_version=lambda forecast_version_id: None,
        ),
        geomet_client=GeoMetClient(),
        nager_date_client=NagerDateClient(),
        settings=settings,
    )
    with pytest.raises(HTTPException):
        missing_version_service.get_current_forecast()


@pytest.mark.unit
@pytest.mark.anyio
async def test_main_lifespan_covers_forecast_scheduler_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    class FakeScheduler:
        def register_cron_job(self, job_id, callback, cron_expression):
            events.append(f"register:{job_id}:{cron_expression}")

        def start(self):
            events.append("start")

        def shutdown(self):
            events.append("shutdown")

    monkeypatch.setattr(main_module, "SchedulerService", FakeScheduler)
    monkeypatch.setattr(main_module, "build_ingestion_job", lambda factory: lambda: None)
    monkeypatch.setattr(main_module, "build_forecast_job", lambda factory: lambda: None)
    monkeypatch.setattr(main_module, "run_migrations", lambda: None)
    monkeypatch.setattr(main_module, "get_session_factory", lambda: lambda: "session")
    monkeypatch.setattr(
        main_module,
        "get_settings",
        lambda: SimpleNamespace(
            scheduler_enabled=False,
            forecast_scheduler_enabled=True,
            forecast_scheduler_cron="0 * * * *",
        ),
    )

    app = create_app()
    async with app.router.lifespan_context(app):
        pass

    assert "register:daily_demand_forecast:0 * * * *" in events
    assert events[-2:] == ["start", "shutdown"]

@pytest.mark.unit
def test_clients_cover_non_matching_transport_fallback() -> None:
    start = datetime(2026, 3, 22, tzinfo=timezone.utc)
    end = start + timedelta(hours=2)

    weather = GeoMetClient(object()).fetch_hourly_conditions(start, end)
    holidays = NagerDateClient(object()).fetch_holidays(2026)

    assert len(weather) == 2
    assert holidays[0]["countryCode"] == "CA"


@pytest.mark.unit
def test_forecast_repository_missing_version_in_current_lookup(session) -> None:
    repository = ForecastRepository(session)
    now = datetime(2026, 3, 22, tzinfo=timezone.utc)
    marker = repository_models.CurrentForecastMarker(
        forecast_product_name="daily_1_day_demand",
        forecast_version_id="missing-version",
        source_cleaned_dataset_version_id="dataset-1",
        horizon_start=now,
        horizon_end=now + timedelta(hours=24),
        updated_by_run_id="run-1",
        geography_scope="category_only",
    )
    session.add(marker)
    session.commit()

    assert repository.find_current_for_horizon(
        forecast_product_name="daily_1_day_demand",
        horizon_start=now,
        horizon_end=now + timedelta(hours=24),
    ) is None


@pytest.mark.unit
def test_forecast_trigger_validator_raise_branch_direct() -> None:
    assert ForecastTriggerRequest.validate_trigger_type("on_demand") == "on_demand"
    with pytest.raises(ValueError):
        ForecastTriggerRequest.validate_trigger_type("scheduled")


@pytest.mark.unit
@pytest.mark.anyio
async def test_main_lifespan_covers_no_scheduler_start(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    class FakeScheduler:
        def register_cron_job(self, job_id, callback, cron_expression):
            events.append(f"register:{job_id}:{cron_expression}")

        def start(self):
            events.append("start")

        def shutdown(self):
            events.append("shutdown")

    monkeypatch.setattr(main_module, "SchedulerService", FakeScheduler)
    monkeypatch.setattr(main_module, "build_ingestion_job", lambda factory: lambda: None)
    monkeypatch.setattr(main_module, "build_forecast_job", lambda factory: lambda: None)
    monkeypatch.setattr(main_module, "run_migrations", lambda: None)
    monkeypatch.setattr(main_module, "get_session_factory", lambda: lambda: "session")
    monkeypatch.setattr(
        main_module,
        "get_settings",
        lambda: SimpleNamespace(
            scheduler_enabled=False,
            forecast_scheduler_enabled=False,
        ),
    )

    app = create_app()
    async with app.router.lifespan_context(app):
        pass

    assert events == ["shutdown"]


@pytest.mark.unit
def test_forecast_repository_current_lookup_covers_missing_and_pending_versions(session) -> None:
    repository = ForecastRepository(session)
    now = datetime(2026, 3, 22, tzinfo=timezone.utc)

    missing_marker = repository_models.CurrentForecastMarker(
        forecast_product_name="daily_missing_version",
        forecast_version_id="missing-version",
        source_cleaned_dataset_version_id="dataset-1",
        horizon_start=now,
        horizon_end=now + timedelta(hours=24),
        updated_by_run_id="run-1",
        geography_scope="category_only",
    )
    pending_version = ForecastVersion(
        forecast_version_id="pending-version",
        forecast_run_id="run-pending",
        source_cleaned_dataset_version_id="dataset-1",
        horizon_start=now,
        horizon_end=now + timedelta(hours=24),
        geography_scope="category_only",
        baseline_method="baseline",
        storage_status="pending",
        is_current=False,
    )
    pending_marker = repository_models.CurrentForecastMarker(
        forecast_product_name="daily_pending_version",
        forecast_version_id="pending-version",
        source_cleaned_dataset_version_id="dataset-1",
        horizon_start=now,
        horizon_end=now + timedelta(hours=24),
        updated_by_run_id="run-pending",
        geography_scope="category_only",
    )
    session.add_all([missing_marker, pending_version, pending_marker])
    session.commit()

    assert repository.find_current_for_horizon(
        forecast_product_name="daily_missing_version",
        horizon_start=now,
        horizon_end=now + timedelta(hours=24),
    ) is None
    assert repository.find_current_for_horizon(
        forecast_product_name="daily_pending_version",
        horizon_start=now,
        horizon_end=now + timedelta(hours=24),
    ) is None


@pytest.mark.unit
def test_forecast_repository_current_lookup_missing_version_guard(monkeypatch: pytest.MonkeyPatch, session) -> None:
    repository = ForecastRepository(session)
    now = datetime(2026, 3, 22, tzinfo=timezone.utc)
    marker = SimpleNamespace(
        forecast_version_id="missing-version",
        horizon_start=now,
        horizon_end=now + timedelta(hours=24),
    )
    monkeypatch.setattr(repository, "get_current_marker", lambda forecast_product_name: marker)
    monkeypatch.setattr(repository, "get_forecast_version", lambda forecast_version_id: None)

    assert repository.find_current_for_horizon(
        forecast_product_name="daily_1_day_demand",
        horizon_start=now,
        horizon_end=now + timedelta(hours=24),
    ) is None


class _Response:
    def __init__(self, status_code: int, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


@pytest.mark.unit
def test_geomet_http_transport_success_and_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    start = datetime(2026, 3, 22, tzinfo=timezone.utc)
    end = start + timedelta(hours=1)

    def fake_get(url, *, params=None, headers=None, timeout=None):
        return _Response(
            200,
            {
                "features": [
                    {
                        "properties": {
                            "UTC_DATE": "2026-03-22T00:00:00Z",
                            "TEMP": 2.5,
                            "PRECIP_AMOUNT": 1.0,
                        }
                    }
                ]
            },
        )

    monkeypatch.setattr('app.clients.geomet_client.httpx.get', fake_get)
    result = GeoMetHttpTransport(
        base_url='https://api.weather.gc.ca',
        station_identifier='30165',
        station_selector='fixed_climate_identifier',
    ).fetch_hourly_conditions(start, end)
    assert result[0]['temperature_c'] == 2.5

    monkeypatch.setattr('app.clients.geomet_client.httpx.get', lambda *args, **kwargs: _Response(503, {}))
    with pytest.raises(GeoMetClientError):
        GeoMetHttpTransport(
            base_url='https://api.weather.gc.ca',
            station_identifier='30165',
            station_selector='fixed_climate_identifier',
        ).fetch_hourly_conditions(start, end)


@pytest.mark.unit
def test_nager_http_transport_success_and_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        'app.clients.nager_date_client.httpx.get',
        lambda *args, **kwargs: _Response(
            200,
            [
                {"date": "2026-07-01", "localName": "Canada Day", "countryCode": "CA", "global": True},
                {"date": "2026-08-03", "name": "Heritage Day", "countryCode": "CA", "global": False, "counties": ["CA-AB"]},
                {"date": "2026-02-16", "name": "Family Day Ontario", "countryCode": "CA", "global": False, "counties": ["CA-ON"]},
            ],
        ),
    )
    result = NagerDateHttpTransport(base_url='https://date.nager.at').fetch_holidays(2026)
    assert [item['name'] for item in result] == ['Canada Day', 'Heritage Day']

    monkeypatch.setattr('app.clients.nager_date_client.httpx.get', lambda *args, **kwargs: _Response(500, {}))
    with pytest.raises(NagerDateClientError):
        NagerDateHttpTransport(base_url='https://date.nager.at').fetch_holidays(2026)


@pytest.mark.unit
def test_geomet_client_uses_configured_station_identifier(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeTransport:
        def __init__(self, *, base_url: str, station_identifier: str | None = None, station_selector: str = 'edmonton_hourly_station', timeout: float = 30.0) -> None:
            captured["base_url"] = base_url
            captured["station_identifier"] = station_identifier
            captured["station_selector"] = station_selector
            captured["timeout"] = timeout

        def fetch_hourly_conditions(self, horizon_start, horizon_end):
            return []

    monkeypatch.setattr('app.clients.geomet_client.GeoMetHttpTransport', FakeTransport)
    monkeypatch.setattr(
        'app.clients.geomet_client.get_settings',
        lambda: SimpleNamespace(geomet_base_url='https://api.weather.gc.ca', geomet_climate_identifier='98765'),
    )

    client = GeoMetClient()
    assert captured == {
        'base_url': 'https://api.weather.gc.ca',
        'station_identifier': '98765',
        'station_selector': 'edmonton_hourly_station',
        'timeout': 30.0,
    }
    assert client.fetch_hourly_conditions(
        datetime(2026, 3, 22, tzinfo=timezone.utc),
        datetime(2026, 3, 22, 1, tzinfo=timezone.utc),
    ) == []


@pytest.mark.unit
def test_geomet_client_uses_configured_timeout_and_selector(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeTransport:
        def __init__(self, *, base_url: str, station_identifier: str | None = None, station_selector: str = 'edmonton_hourly_station', timeout: float = 30.0) -> None:
            captured["base_url"] = base_url
            captured["station_identifier"] = station_identifier
            captured["station_selector"] = station_selector
            captured["timeout"] = timeout

        def fetch_hourly_conditions(self, horizon_start, horizon_end):
            return []

    monkeypatch.setattr('app.clients.geomet_client.GeoMetHttpTransport', FakeTransport)
    monkeypatch.setattr(
        'app.clients.geomet_client.get_settings',
        lambda: SimpleNamespace(
            geomet_base_url='https://api.weather.gc.ca',
            geomet_climate_identifier='98765',
            geomet_station_selector='edmonton_hourly_station',
            geomet_timeout_seconds=12.5,
        ),
    )

    client = GeoMetClient()
    assert captured == {
        'base_url': 'https://api.weather.gc.ca',
        'station_identifier': '98765',
        'station_selector': 'edmonton_hourly_station',
        'timeout': 12.5,
    }
    assert client.fetch_hourly_conditions(
        datetime(2026, 3, 22, tzinfo=timezone.utc),
        datetime(2026, 3, 22, 1, tzinfo=timezone.utc),
    ) == []


@pytest.mark.unit
def test_geomet_client_rejects_unknown_selector(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        'app.clients.geomet_client.get_settings',
        lambda: SimpleNamespace(
            geomet_base_url='https://api.weather.gc.ca',
            geomet_climate_identifier='98765',
            geomet_station_selector='nearest_station',
            geomet_timeout_seconds=12.5,
        ),
    )

    with pytest.raises(GeoMetClientError):
        GeoMetClient()


@pytest.mark.unit
def test_geomet_transport_discovers_edmonton_station_and_caches(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    start = datetime(2026, 3, 22, tzinfo=timezone.utc)
    end = start + timedelta(hours=1)

    def fake_get(url, *, params=None, headers=None, timeout=None):
        calls.append((url, dict(params or {})))
        if url.endswith('/collections/climate-stations/items'):
            return _Response(
                200,
                {
                    'features': [
                        {
                            'geometry': {'coordinates': [-113.52, 53.54]},
                            'properties': {
                                'STATION_NAME': 'EDMONTON STONY PLAIN',
                                'HAS_HOURLY_DATA': 'Y',
                                'CLIMATE_IDENTIFIER': '11111',
                                'HLY_LAST_DATE': '2024-01-01T00:00:00Z',
                            },
                        },
                        {
                            'geometry': {'coordinates': [-113.49, 53.55]},
                            'properties': {
                                'STATION_NAME': 'EDMONTON CITY CENTRE',
                                'HAS_HOURLY_DATA': 'Y',
                                'CLIMATE_IDENTIFIER': '22222',
                                'HLY_LAST_DATE': '2025-01-01T00:00:00Z',
                            },
                        },
                    ]
                },
            )
        return _Response(
            200,
            {
                'features': [
                    {
                        'properties': {
                            'UTC_DATE': '2026-03-22T00:00:00Z',
                            'TEMP': 2.5,
                            'PRECIP_AMOUNT': 1.0,
                        }
                    }
                ]
            },
        )

    monkeypatch.setattr('app.clients.geomet_client.httpx.get', fake_get)
    transport = GeoMetHttpTransport(base_url='https://api.weather.gc.ca', station_selector='edmonton_hourly_station')

    first = transport.fetch_hourly_conditions(start, end)
    second = transport.fetch_hourly_conditions(start, end)

    assert first[0]['temperature_c'] == 2.5
    assert second[0]['precipitation_mm'] == 1.0
    station_calls = [call for call in calls if call[0].endswith('/collections/climate-stations/items')]
    hourly_calls = [call for call in calls if call[0].endswith('/collections/climate-hourly/items')]
    assert len(station_calls) == 1
    assert len(hourly_calls) == 2
    assert hourly_calls[0][1]['CLIMATE_IDENTIFIER'] == '22222'


@pytest.mark.unit
def test_geomet_transport_pages_historical_weather(monkeypatch: pytest.MonkeyPatch) -> None:
    start = datetime(2026, 1, 27, 3, tzinfo=timezone.utc)
    end = datetime(2026, 3, 24, 3, tzinfo=timezone.utc)
    calls: list[tuple[str, dict[str, object]]] = []

    def hourly_batch(offset: int, size: int):
        base = offset
        return {
            'features': [
                {
                    'properties': {
                        'UTC_DATE': (start + timedelta(hours=base + idx)).isoformat().replace('+00:00', 'Z'),
                        'TEMP': float(idx),
                        'PRECIP_AMOUNT': 0.1,
                    }
                }
                for idx in range(size)
            ]
        }

    def fake_get(url, *, params=None, headers=None, timeout=None):
        calls.append((url, dict(params or {})))
        if url.endswith('/collections/climate-stations/items'):
            return _Response(
                200,
                {
                    'features': [
                        {
                            'geometry': {'coordinates': [-113.49, 53.55]},
                            'properties': {
                                'STATION_NAME': 'EDMONTON CITY CENTRE',
                                'HAS_HOURLY_DATA': 'Y',
                                'CLIMATE_IDENTIFIER': '22222',
                                'HLY_LAST_DATE': '2025-01-01T00:00:00Z',
                            },
                        }
                    ]
                },
            )
        if url.endswith('/collections/climate-hourly/items'):
            offset = int((params or {}).get('offset', 0))
            if offset == 0:
                return _Response(200, hourly_batch(0, 200))
            if offset == 200:
                return _Response(200, hourly_batch(200, 200))
            if offset == 400:
                return _Response(200, hourly_batch(400, 50))
        return _Response(200, {'features': []})

    monkeypatch.setattr('app.clients.geomet_client.httpx.get', fake_get)
    transport = GeoMetHttpTransport(base_url='https://api.weather.gc.ca', station_selector='edmonton_hourly_station')

    result = transport.fetch_historical_hourly_conditions(start, end)

    assert len(result) == 450
    hourly_calls = [call for call in calls if call[0].endswith('/collections/climate-hourly/items')]
    assert [call[1]['offset'] for call in hourly_calls] == [0, 200, 400]
    assert hourly_calls[0][1]['limit'] == 200



@pytest.mark.unit
def test_geomet_transport_discovery_requires_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        'app.clients.geomet_client.httpx.get',
        lambda *args, **kwargs: _Response(200, {'features': []}),
    )
    transport = GeoMetHttpTransport(base_url='https://api.weather.gc.ca', station_selector='edmonton_hourly_station')
    with pytest.raises(GeoMetClientError):
        transport.fetch_hourly_conditions(
            datetime(2026, 3, 22, tzinfo=timezone.utc),
            datetime(2026, 3, 22, 1, tzinfo=timezone.utc),
        )


@pytest.mark.unit
def test_geomet_transport_covers_guard_and_helper_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    start = datetime(2026, 3, 22, tzinfo=timezone.utc)
    end = start + timedelta(hours=1)

    monkeypatch.setattr(
        'app.clients.geomet_client.httpx.get',
        lambda *args, **kwargs: _Response(200, {'features': {}}),
    )
    with pytest.raises(GeoMetClientError):
        GeoMetHttpTransport(
            base_url='https://api.weather.gc.ca',
            station_identifier='30165',
            station_selector='fixed_climate_identifier',
        ).fetch_hourly_conditions(start, end)

    monkeypatch.setattr(
        'app.clients.geomet_client.httpx.get',
        lambda *args, **kwargs: _Response(
            200,
            {
                'features': [
                    'skip-me',
                    {'properties': 'bad'},
                    {'properties': {'UTC_DATE': 'not-a-date', 'TEMP': 1.0, 'PRECIP_AMOUNT': 0.0}},
                    {'properties': {'LOCAL_DATE': '2026-03-22T00:00:00Z'}},
                ]
            },
        ),
    )
    result = GeoMetHttpTransport(
        base_url='https://api.weather.gc.ca',
        station_identifier='30165',
        station_selector='fixed_climate_identifier',
    ).fetch_hourly_conditions(start, end)
    assert result == [
        {
            'timestamp': datetime(2026, 3, 22, 0, 0, tzinfo=timezone.utc),
            'temperature_c': 0.0,
            'precipitation_mm': 0.0,
        }
    ]

    with pytest.raises(GeoMetClientError):
        GeoMetHttpTransport(base_url='https://api.weather.gc.ca', station_selector='fixed_climate_identifier').fetch_hourly_conditions(start, end)

    with pytest.raises(GeoMetClientError):
        GeoMetHttpTransport(base_url='https://api.weather.gc.ca', station_selector='nearest_station').fetch_hourly_conditions(start, end)

    monkeypatch.setattr(
        'app.clients.geomet_client.httpx.get',
        lambda *args, **kwargs: _Response(200, {'features': {}}),
    )
    with pytest.raises(GeoMetClientError):
        GeoMetHttpTransport(base_url='https://api.weather.gc.ca', station_selector='edmonton_hourly_station').fetch_hourly_conditions(start, end)

    monkeypatch.setattr(
        'app.clients.geomet_client.httpx.get',
        lambda *args, **kwargs: _Response(
            200,
            {
                'features': [
                    'skip-me',
                    {'properties': 'bad'},
                    {'geometry': {'coordinates': [-113.5, 53.5]}, 'properties': {'HAS_HOURLY_DATA': 'N', 'CLIMATE_IDENTIFIER': '11111'}},
                    {'geometry': {'coordinates': [-113.5, 53.5]}, 'properties': {'HAS_HOURLY_DATA': 'Y', 'CLIMATE_IDENTIFIER': ''}},
                    {
                        'properties': {
                            'HAS_HOURLY_DATA': 'Y',
                            'CLIMATE_IDENTIFIER': '33333',
                            'STATION_NAME': 'ALBERTA SAMPLE',
                            'LONGITUDE': -113500000,
                            'LATITUDE': 53500000,
                            'LAST_DATE': 'invalid',
                        }
                    },
                ]
            },
        ),
    )
    discovered = GeoMetHttpTransport(base_url='https://api.weather.gc.ca', station_selector='edmonton_hourly_station')
    assert discovered._discover_edmonton_station_identifier() == '33333'


@pytest.mark.unit
def test_geomet_transport_request_and_client_fallback_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = GeoMetHttpTransport(base_url='https://api.weather.gc.ca', station_identifier='30165', station_selector='fixed_climate_identifier')

    def raise_timeout(*args, **kwargs):
        raise httpx.TimeoutException('slow')

    def raise_http_error(*args, **kwargs):
        raise httpx.HTTPError('boom')

    monkeypatch.setattr('app.clients.geomet_client.httpx.get', raise_timeout)
    with pytest.raises(GeoMetClientError):
        transport._request('https://api.weather.gc.ca/test', params={}, accept='application/json')

    monkeypatch.setattr('app.clients.geomet_client.httpx.get', raise_http_error)
    with pytest.raises(GeoMetClientError):
        transport._request('https://api.weather.gc.ca/test', params={}, accept='application/json')

    monkeypatch.setattr(
        'app.clients.geomet_client.get_settings',
        lambda: SimpleNamespace(
            geomet_base_url='https://api.weather.gc.ca',
            geomet_station_selector='fixed_climate_identifier',
            geomet_climate_identifier=None,
            geomet_timeout_seconds=12.5,
        ),
    )
    with pytest.raises(GeoMetClientError):
        GeoMetClient()

    client = object.__new__(GeoMetClient)
    client.transport = None
    start = datetime(2026, 3, 22, tzinfo=timezone.utc)
    end = start + timedelta(hours=3)
    assert len(client.fetch_hourly_conditions(start, end)) == 3


@pytest.mark.unit
def test_geomet_helper_functions_cover_remaining_branches() -> None:
    from app.clients import geomet_client as module

    assert module._parse_timestamp(None) is None
    assert module._parse_timestamp('not-a-date') is None
    assert module._extract_coordinates({}, {'coordinates': [-113.4, 53.6]}, {}) == (-113.4, 53.6)
    assert module._extract_coordinates({}, {'coordinates': ['bad']}, {'LONGITUDE': -113500000, 'LATITUDE': 53500000}) == (-113.5, 53.5)
    assert module._extract_coordinates({}, None, {'LONGITUDE': -113500000, 'LATITUDE': 53500000}) == (-113.5, 53.5)
    assert module._extract_coordinates({}, {}, {'LONGITUDE': -113500000, 'LATITUDE': 53500000}) == (-113.5, 53.5)
    assert module._extract_coordinates({}, {}, {}) == module.EDMONTON_CENTER
    assert module._recency_score(None) == float('inf')
    assert module._recency_score('bad') == float('inf')


@pytest.mark.unit
def test_nager_transport_covers_guard_error_and_fallback_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_timeout(*args, **kwargs):
        raise httpx.TimeoutException('slow')

    def raise_http_error(*args, **kwargs):
        raise httpx.HTTPError('boom')

    monkeypatch.setattr('app.clients.nager_date_client.httpx.get', raise_timeout)
    with pytest.raises(NagerDateClientError):
        NagerDateHttpTransport(base_url='https://date.nager.at').fetch_holidays(2026)

    monkeypatch.setattr('app.clients.nager_date_client.httpx.get', raise_http_error)
    with pytest.raises(NagerDateClientError):
        NagerDateHttpTransport(base_url='https://date.nager.at').fetch_holidays(2026)

    monkeypatch.setattr('app.clients.nager_date_client.httpx.get', lambda *args, **kwargs: _Response(200, {}))
    with pytest.raises(NagerDateClientError):
        NagerDateHttpTransport(base_url='https://date.nager.at').fetch_holidays(2026)

    monkeypatch.setattr(
        'app.clients.nager_date_client.httpx.get',
        lambda *args, **kwargs: _Response(
            200,
            [
                'skip-me',
                {'name': 'Missing date', 'global': True},
                {'date': '2026-12-25', 'name': None, 'countryCode': None, 'global': True},
                {'date': '2026-02-16', 'name': 'Ontario Only', 'countryCode': 'CA', 'global': False, 'counties': ['CA-ON']},
                {'date': '2026-08-03', 'name': 'Alberta Day', 'countryCode': 'CA', 'global': False, 'counties': ['CA-AB']},
            ],
        ),
    )
    result = NagerDateHttpTransport(base_url='https://date.nager.at').fetch_holidays(2026)
    assert result == [
        {'date': '2026-12-25', 'name': 'Holiday', 'countryCode': 'CA'},
        {'date': '2026-08-03', 'name': 'Alberta Day', 'countryCode': 'CA'},
    ]

    client = object.__new__(NagerDateClient)
    client.transport = None
    assert client.fetch_holidays(2026, 'CA')[0]['date'] == '2026-01-01'

    from app.clients import nager_date_client as nager_module
    assert nager_module._is_alberta_holiday({'counties': 'CA-AB'}) is False


@pytest.mark.unit
def test_feature_preparation_covers_invalid_requested_at_and_future_record_skip() -> None:
    from app.pipelines.forecasting import feature_preparation as module

    horizon_start = datetime(2026, 3, 22, 1, tzinfo=timezone.utc)
    horizon_end = horizon_start + timedelta(hours=2)

    assert module._parse_requested_at(None) is None
    assert module._parse_requested_at('not-a-date') is None

    prepared = module.prepare_forecast_features(
        dataset_records=[
            {'requested_at': 'not-a-date', 'category': 'Roads', 'ward': 'Ward 1'},
            {'requested_at': '2026-03-22T03:00:00Z', 'category': 'Roads', 'ward': 'Ward 1'},
        ],
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        weather_rows=[],
        holidays=[],
    )

    assert prepared['categories'] == ['Uncategorized']
    assert len(prepared['training_rows']) == 24 * 56
    assert all(row['historical_mean'] == 0.0 for row in prepared['rows'])


@pytest.mark.unit
def test_hourly_pipeline_covers_empty_quantile_and_alpha_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.pipelines.forecasting.hourly_demand_pipeline import HourlyDemandPipeline

    pipeline = HourlyDemandPipeline()
    empty = pipeline.run({'rows': [], 'training_rows': [], 'geography_scope': 'category_only'})
    assert empty['buckets'] == []

    captured: list[dict[str, object]] = []

    class FakeModel:
        def __init__(self, **kwargs):
            captured.append(kwargs)

        def fit(self, x_train, y_train):
            return self

        def predict(self, x_score):
            return np.full(len(x_score), 2.0, dtype=float)

    monkeypatch.setattr('app.pipelines.forecasting.hourly_demand_pipeline.lgb.LGBMRegressor', FakeModel)
    prepared = {
        'geography_scope': 'category_only',
        'training_rows': [
            {
                'service_category': 'Roads',
                'geography_key': None,
                'hour_of_day': index % 24,
                'day_of_week': index % 7,
                'day_of_year': 80 + index,
                'month': 3,
                'is_weekend': False,
                'is_holiday': False,
                'weather_temperature_c': 5.0,
                'weather_precipitation_mm': 0.0,
                'historical_mean': 1.5,
                'observed_count': float(index + 1),
                'bucket_start': datetime(2026, 3, 10, tzinfo=timezone.utc) + timedelta(hours=index),
                'bucket_end': datetime(2026, 3, 10, tzinfo=timezone.utc) + timedelta(hours=index + 1),
            }
            for index in range(5)
        ],
        'rows': [
            {
                'service_category': 'Roads',
                'geography_key': None,
                'hour_of_day': 1,
                'day_of_week': 6,
                'day_of_year': 90,
                'month': 3,
                'is_weekend': False,
                'is_holiday': False,
                'weather_temperature_c': 4.0,
                'weather_precipitation_mm': 0.1,
                'historical_mean': 1.5,
                'bucket_start': datetime(2026, 3, 20, 1, tzinfo=timezone.utc),
                'bucket_end': datetime(2026, 3, 20, 2, tzinfo=timezone.utc),
            }
        ],
    }

    generated = pipeline.run(prepared)
    bucket = generated['buckets'][0]

    assert bucket['quantile_p10'] <= bucket['quantile_p50']
    assert bucket['quantile_p50'] == 2.0
    assert bucket['quantile_p90'] >= bucket['quantile_p50']
    assert {'objective': 'regression', 'n_estimators': 80, 'learning_rate': 0.08, 'num_leaves': 15, 'min_child_samples': 8, 'subsample': 0.9, 'colsample_bytree': 0.9, 'random_state': 42, 'verbosity': -1} in captured


@pytest.mark.unit
def test_forecast_service_helper_branches_cover_invalid_and_aware_inputs() -> None:
    from app.services import forecast_service as module

    horizon_start = datetime(2026, 3, 22, 1, tzinfo=timezone.utc)
    fallback = module.compute_training_window_start(horizon_start)
    assert fallback == horizon_start - timedelta(hours=24 * 56)

    aware = datetime(2026, 3, 22, 1, tzinfo=timezone(timedelta(hours=-6)))
    assert module._ensure_utc(aware) == aware.astimezone(timezone.utc)
    assert module._parse_requested_at('') is None
    assert module._parse_requested_at('bad') is None


@pytest.mark.unit
def test_forecast_service_success_and_helper_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import forecast_service as module

    horizon_start = datetime(2026, 3, 22, 1, tzinfo=timezone.utc)
    horizon_end = horizon_start + timedelta(hours=24)
    assert module.compute_training_window_start(horizon_start) == datetime(2026, 1, 25, 1, tzinfo=timezone.utc)
    assert module.compute_training_window_start(horizon_start, lookback_days=7) == datetime(2026, 3, 15, 1, tzinfo=timezone.utc)
    assert module._ensure_utc(datetime(2026, 3, 22, 1)) == datetime(2026, 3, 22, 1, tzinfo=timezone.utc)

    created: dict[str, object] = {}

    class StartRepo:
        def create_run(self, **kwargs):
            created.update(kwargs)
            return SimpleNamespace(forecast_run_id='run-start', **kwargs)

    start_service = ForecastService(
        cleaned_dataset_repository=SimpleNamespace(get_current_approved_dataset=lambda source_name: SimpleNamespace(dataset_version_id='dataset-1')),
        forecast_run_repository=StartRepo(),
        forecast_repository=SimpleNamespace(),
        geomet_client=GeoMetClient(),
        nager_date_client=NagerDateClient(),
        settings=SimpleNamespace(source_name='edmonton_311', forecast_product_name='daily_1_day_demand', forecast_training_lookback_days=56),
    )
    started = start_service.start_run('scheduled', now=datetime(2026, 3, 22, 10, 23, tzinfo=timezone.utc))
    assert started.forecast_run_id == 'run-start'
    assert created['source_cleaned_dataset_version_id'] == 'dataset-1'
    assert created['requested_horizon_start'] == datetime(2026, 3, 22, 11, tzinfo=timezone.utc)

    run = SimpleNamespace(
        forecast_run_id='run-1',
        trigger_type='scheduled',
        status='pending',
        started_at=horizon_start,
        source_cleaned_dataset_version_id='dataset-1',
        requested_horizon_start=datetime(2026, 3, 22, 1),
        requested_horizon_end=datetime(2026, 3, 23, 1),
    )

    class SuccessRunRepo:
        def __init__(self):
            self.generated = None
            self.reused = None

        def get_run(self, forecast_run_id):
            return run

        def finalize_generated(self, forecast_run_id, **kwargs):
            self.generated = kwargs
            return SimpleNamespace(forecast_run_id=forecast_run_id, **kwargs)

        def finalize_reused(self, forecast_run_id, **kwargs):
            self.reused = kwargs
            return SimpleNamespace(forecast_run_id=forecast_run_id, **kwargs)

        def finalize_failed(self, forecast_run_id, **kwargs):
            return SimpleNamespace(forecast_run_id=forecast_run_id, **kwargs)

    run_repo = SuccessRunRepo()
    version = SimpleNamespace(forecast_version_id='forecast-1', geography_scope='category_only', bucket_granularity='hour', bucket_count=1, summary='stored')
    marker = SimpleNamespace(
        forecast_version_id='forecast-1',
        source_cleaned_dataset_version_id='dataset-1',
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        geography_scope='category_only',
        updated_at=horizon_start,
        updated_by_run_id='run-1',
    )
    bucket = SimpleNamespace(
        bucket_start=horizon_start,
        bucket_end=horizon_start + timedelta(hours=1),
        service_category='Roads',
        geography_key=None,
        point_forecast=2.0,
        quantile_p10=1.0,
        quantile_p50=2.0,
        quantile_p90=3.0,
        baseline_value=1.5,
    )
    forecast_repo = SimpleNamespace(
        find_current_for_horizon=lambda **kwargs: None,
        get_current_marker=lambda product: marker,
        get_forecast_version=lambda forecast_version_id: version,
        list_buckets=lambda forecast_version_id: [bucket],
    )
    service = ForecastService(
        cleaned_dataset_repository=SimpleNamespace(
            list_current_cleaned_records=lambda source_name, **kwargs: [{'requested_at': '2026-03-18T09:00:00Z', 'category': 'Roads'}]
        ),
        forecast_run_repository=run_repo,
        forecast_repository=forecast_repo,
        geomet_client=SimpleNamespace(fetch_hourly_conditions=lambda start, end: []),
        nager_date_client=SimpleNamespace(fetch_holidays=lambda year: []),
        settings=SimpleNamespace(source_name='edmonton_311', forecast_product_name='daily_1_day_demand', forecast_training_lookback_days=56),
    )
    service.pipeline = SimpleNamespace(run=lambda prepared: {'baseline_method': 'historical_hourly_mean', 'geography_scope': 'category_only', 'buckets': [bucket.__dict__]})
    service.bucket_service = SimpleNamespace(build_buckets=lambda generated: ([bucket.__dict__], 'category_only'))
    service.activation_service = SimpleNamespace(store_and_activate=lambda **kwargs: 'forecast-1')

    generated = service.execute_run('run-1')
    assert generated.forecast_version_id == 'forecast-1'
    current = service.get_current_forecast()
    assert current.forecast_version_id == 'forecast-1'
    assert current.buckets[0].service_category == 'Roads'
    assert service.get_run_status('run-1').forecast_run_id == 'run-1'

    reused_repo = SuccessRunRepo()
    reused_service = ForecastService(
        cleaned_dataset_repository=SimpleNamespace(),
        forecast_run_repository=reused_repo,
        forecast_repository=SimpleNamespace(find_current_for_horizon=lambda **kwargs: SimpleNamespace(forecast_version_id='forecast-existing', geography_scope='category_only')),
        geomet_client=GeoMetClient(),
        nager_date_client=NagerDateClient(),
        settings=SimpleNamespace(source_name='edmonton_311', forecast_product_name='daily_1_day_demand', forecast_training_lookback_days=56),
    )
    reused = reused_service.execute_run('run-1')
    assert reused.served_forecast_version_id == 'forecast-existing'

    missing_input_repo = SuccessRunRepo()
    missing_input_repo.get_run = lambda forecast_run_id: SimpleNamespace(
        forecast_run_id='run-2',
        trigger_type='scheduled',
        status='pending',
        started_at=horizon_start,
        source_cleaned_dataset_version_id=None,
        requested_horizon_start=datetime(2026, 3, 22, 1),
        requested_horizon_end=datetime(2026, 3, 23, 1),
    )
    missing_input_service = ForecastService(
        cleaned_dataset_repository=SimpleNamespace(),
        forecast_run_repository=missing_input_repo,
        forecast_repository=SimpleNamespace(find_current_for_horizon=lambda **kwargs: None),
        geomet_client=GeoMetClient(),
        nager_date_client=NagerDateClient(),
        settings=SimpleNamespace(source_name='edmonton_311', forecast_product_name='daily_1_day_demand', forecast_training_lookback_days=56),
    )
    failed = missing_input_service.execute_run('run-2')
    assert failed.result_type == 'missing_input_data'


@pytest.mark.unit
def test_forecast_model_repository_and_training_service_happy_path(session, tmp_path) -> None:
    from app.core.config import get_settings
    from app.repositories.dataset_repository import DatasetRepository
    from app.repositories.forecast_model_repository import ForecastModelRepository
    from app.services.forecast_training_service import ForecastTrainingService, ForecastModelStorageError

    dataset_repository = DatasetRepository(session)
    version = dataset_repository.create_dataset_version(
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
    dataset_repository.activate_dataset("edmonton_311", version.dataset_version_id, "validation-1")
    session.commit()

    settings = SimpleNamespace(
        source_name="edmonton_311",
        forecast_product_name="daily_1_day_demand",
        forecast_training_lookback_days=56,
        forecast_model_artifact_dir=str(tmp_path / "artifacts"),
    )
    repository = ForecastModelRepository(session)
    service = ForecastTrainingService(
        cleaned_dataset_repository=CleanedDatasetRepository(session),
        forecast_model_repository=repository,
        geomet_client=GeoMetClient(object()),
        nager_date_client=NagerDateClient(object()),
        settings=settings,
    )

    run = service.start_run("on_demand", now=datetime(2026, 3, 22, 12, tzinfo=timezone.utc))
    session.commit()
    result = service.execute_run(run.forecast_model_run_id)
    session.commit()

    current_artifact = repository.find_current_model("daily_1_day_demand")
    assert result.result_type == "trained_new"
    assert current_artifact is not None
    assert __import__("pathlib").Path(current_artifact.artifact_path).exists()
    loaded = service.load_current_artifact()
    assert loaded is not None
    assert loaded.model_family == "lightgbm_global"

    with pytest.raises(ForecastModelStorageError):
        service.load_artifact_bundle(str(tmp_path / "missing.pkl"))


@pytest.mark.unit
def test_forecast_model_repository_missing_paths(session) -> None:
    from app.repositories.forecast_model_repository import ForecastModelRepository

    repository = ForecastModelRepository(session)
    assert repository.find_current_model("missing") is None
    with pytest.raises(ValueError):
        repository._require_run("missing")
    with pytest.raises(ValueError):
        repository._require_artifact("missing")


@pytest.mark.unit
def test_forecast_training_scheduler_job_runs_and_closes_session(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    class FakeSession:
        def commit(self):
            events.append("commit")

        def close(self):
            events.append("close")

    class FakeTrainingService:
        def __init__(self, **kwargs):
            events.append("training-service")

        def start_run(self, trigger_type: str):
            events.append(f"start:{trigger_type}")
            return SimpleNamespace(forecast_model_run_id="model-run-123")

        def execute_run(self, forecast_model_run_id: str):
            events.append(f"execute:{forecast_model_run_id}")

    monkeypatch.setattr(forecast_scheduler, "ForecastTrainingService", FakeTrainingService)
    monkeypatch.setattr(forecast_scheduler, "CleanedDatasetRepository", lambda session: "cleaned")
    monkeypatch.setattr(forecast_scheduler, "ForecastModelRepository", lambda session: "model-repo")
    monkeypatch.setattr(forecast_scheduler, "get_settings", lambda: SimpleNamespace(source_name="edmonton_311"))

    job = forecast_scheduler.build_forecast_training_job(lambda: FakeSession())
    assert job() == "model-run-123"
    assert events == ["training-service", "start:scheduled", "commit", "execute:model-run-123", "commit", "close"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_main_lifespan_covers_forecast_model_scheduler_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    class FakeScheduler:
        def register_cron_job(self, job_id, callback, cron_expression):
            events.append(f"register:{job_id}:{cron_expression}")

        def start(self):
            events.append("start")

        def shutdown(self):
            events.append("shutdown")

    monkeypatch.setattr(main_module, "SchedulerService", FakeScheduler)
    monkeypatch.setattr(main_module, "build_ingestion_job", lambda factory: lambda: None)
    monkeypatch.setattr(main_module, "build_forecast_job", lambda factory: lambda: None)
    monkeypatch.setattr(main_module, "build_forecast_training_job", lambda factory: lambda: None)
    monkeypatch.setattr(main_module, "run_migrations", lambda: None)
    monkeypatch.setattr(main_module, "get_session_factory", lambda: lambda: "session")
    monkeypatch.setattr(
        main_module,
        "get_settings",
        lambda: SimpleNamespace(
            scheduler_enabled=False,
            forecast_model_scheduler_enabled=True,
            forecast_model_scheduler_cron="15 0 * * *",
            forecast_scheduler_enabled=False,
        ),
    )

    app = create_app()
    async with app.router.lifespan_context(app):
        pass

    assert "register:daily_demand_forecast_model_training:15 0 * * *" in events
    assert events[-2:] == ["start", "shutdown"]


@pytest.mark.unit
def test_forecast_service_uses_trained_model_predict_path(monkeypatch: pytest.MonkeyPatch) -> None:
    horizon_start = datetime(2026, 3, 22, 1, tzinfo=timezone.utc)
    bucket = {
        "bucket_start": horizon_start,
        "bucket_end": horizon_start + timedelta(hours=1),
        "service_category": "Roads",
        "geography_key": None,
        "point_forecast": 2.0,
        "quantile_p10": 1.0,
        "quantile_p50": 2.0,
        "quantile_p90": 3.0,
        "baseline_value": 1.5,
    }
    run = SimpleNamespace(
        forecast_run_id="run-1",
        source_cleaned_dataset_version_id="dataset-1",
        requested_horizon_start=horizon_start,
        requested_horizon_end=horizon_start + timedelta(hours=24),
    )

    class RunRepo:
        def get_run(self, forecast_run_id):
            return run

        def finalize_generated(self, forecast_run_id, **kwargs):
            return SimpleNamespace(forecast_run_id=forecast_run_id, **kwargs)

        def finalize_reused(self, forecast_run_id, **kwargs):
            return SimpleNamespace(forecast_run_id=forecast_run_id, **kwargs)

        def finalize_failed(self, forecast_run_id, **kwargs):
            return SimpleNamespace(forecast_run_id=forecast_run_id, **kwargs)

    service = ForecastService(
        cleaned_dataset_repository=SimpleNamespace(
            list_current_cleaned_records=lambda source_name, **kwargs: [{"requested_at": "2026-03-18T09:00:00Z", "category": "Roads"}]
        ),
        forecast_run_repository=RunRepo(),
        forecast_repository=SimpleNamespace(find_current_for_horizon=lambda **kwargs: None),
        geomet_client=SimpleNamespace(fetch_hourly_conditions=lambda start, end: []),
        nager_date_client=SimpleNamespace(fetch_holidays=lambda year: []),
        forecast_model_repository=SimpleNamespace(
            find_current_model=lambda product: SimpleNamespace(
                forecast_model_artifact_id="artifact-1",
                source_cleaned_dataset_version_id="dataset-1",
                artifact_path="/tmp/model.pkl",
            )
        ),
        settings=SimpleNamespace(source_name="edmonton_311", forecast_product_name="daily_1_day_demand", forecast_training_lookback_days=56),
    )
    monkeypatch.setattr(service.training_service, "load_artifact_bundle", lambda path: object())
    monkeypatch.setattr(service.pipeline, "run", lambda prepared: (_ for _ in ()).throw(AssertionError("run should not be used")))
    monkeypatch.setattr(service.pipeline, "predict", lambda artifact, prepared: {"baseline_method": "historical_hourly_mean", "geography_scope": "category_only", "buckets": [bucket]})
    monkeypatch.setattr(service.bucket_service, "build_buckets", lambda generated: ([bucket], "category_only"))
    monkeypatch.setattr(service.activation_service, "store_and_activate", lambda **kwargs: "forecast-1")

    generated = service.execute_run("run-1")
    assert generated.forecast_version_id == "forecast-1"


@pytest.mark.unit
def test_forecast_model_repository_activation_and_failure_paths(session) -> None:
    from app.repositories.forecast_model_repository import ForecastModelRepository

    repository = ForecastModelRepository(session)
    now = datetime(2026, 3, 22, tzinfo=timezone.utc)

    run_1 = repository.create_run(
        forecast_product_name="daily_1_day_demand",
        trigger_type="scheduled",
        source_cleaned_dataset_version_id="dataset-1",
        training_window_start=now - timedelta(days=7),
        training_window_end=now,
    )
    artifact_1 = repository.create_artifact(
        forecast_product_name="daily_1_day_demand",
        forecast_model_run_id=run_1.forecast_model_run_id,
        source_cleaned_dataset_version_id="dataset-1",
        geography_scope="category_only",
        model_family="lightgbm_global",
        baseline_method="historical_hourly_mean",
        feature_schema_version="v1",
        artifact_path="/tmp/model-1.pkl",
        summary="artifact 1",
    )
    repository.activate_artifact(
        forecast_product_name="daily_1_day_demand",
        forecast_model_artifact_id=artifact_1.forecast_model_artifact_id,
        source_cleaned_dataset_version_id="dataset-1",
        training_window_start=now - timedelta(days=7),
        training_window_end=now,
        updated_by_run_id=run_1.forecast_model_run_id,
        geography_scope="category_only",
    )

    run_2 = repository.create_run(
        forecast_product_name="daily_1_day_demand",
        trigger_type="scheduled",
        source_cleaned_dataset_version_id="dataset-2",
        training_window_start=now - timedelta(days=14),
        training_window_end=now,
    )
    artifact_2 = repository.create_artifact(
        forecast_product_name="daily_1_day_demand",
        forecast_model_run_id=run_2.forecast_model_run_id,
        source_cleaned_dataset_version_id="dataset-2",
        geography_scope="category_and_geography",
        model_family="lightgbm_global",
        baseline_method="historical_hourly_mean",
        feature_schema_version="v1",
        artifact_path="/tmp/model-2.pkl",
        summary="artifact 2",
    )
    marker = repository.activate_artifact(
        forecast_product_name="daily_1_day_demand",
        forecast_model_artifact_id=artifact_2.forecast_model_artifact_id,
        source_cleaned_dataset_version_id="dataset-2",
        training_window_start=now - timedelta(days=14),
        training_window_end=now,
        updated_by_run_id=run_2.forecast_model_run_id,
        geography_scope="category_and_geography",
    )
    failed = repository.finalize_failed(
        run_2.forecast_model_run_id,
        result_type="storage_failure",
        failure_reason="disk full",
        summary="failed",
    )
    session.commit()

    previous_artifact = repository.get_artifact(artifact_1.forecast_model_artifact_id)
    assert previous_artifact is not None
    assert previous_artifact.is_current is False
    assert marker.forecast_model_artifact_id == artifact_2.forecast_model_artifact_id
    assert marker.source_cleaned_dataset_version_id == "dataset-2"
    assert marker.geography_scope == "category_and_geography"
    assert failed.status == "failed"
    assert failed.result_type == "storage_failure"
    assert failed.failure_reason == "disk full"

    artifact_2.storage_status = "pending"
    session.add(
        repository_models.CurrentForecastModelMarker(
            forecast_product_name="missing-artifact-product",
            forecast_model_artifact_id="missing-artifact",
            source_cleaned_dataset_version_id="dataset-3",
            training_window_start=now - timedelta(days=1),
            training_window_end=now,
            updated_by_run_id="run-missing",
            geography_scope="category_only",
        )
    )
    session.commit()

    assert repository.find_current_model("daily_1_day_demand") is None
    assert repository.find_current_model("missing-artifact-product") is None


@pytest.mark.unit
def test_forecast_model_repository_scopes_current_artifacts_by_product(session) -> None:
    from app.repositories.forecast_model_repository import ForecastModelRepository

    repository = ForecastModelRepository(session)
    now = datetime(2026, 3, 22, tzinfo=timezone.utc)

    daily_run = repository.create_run(
        forecast_product_name="daily_1_day_demand",
        trigger_type="scheduled",
        source_cleaned_dataset_version_id="dataset-daily",
        training_window_start=now - timedelta(days=7),
        training_window_end=now,
    )
    daily_artifact = repository.create_artifact(
        forecast_product_name="daily_1_day_demand",
        forecast_model_run_id=daily_run.forecast_model_run_id,
        source_cleaned_dataset_version_id="dataset-daily",
        geography_scope="category_only",
        model_family="lightgbm_global",
        baseline_method="historical_hourly_mean",
        feature_schema_version="v1",
        artifact_path="/tmp/daily-model.pkl",
        summary="daily artifact",
    )
    repository.activate_artifact(
        forecast_product_name="daily_1_day_demand",
        forecast_model_artifact_id=daily_artifact.forecast_model_artifact_id,
        source_cleaned_dataset_version_id="dataset-daily",
        training_window_start=now - timedelta(days=7),
        training_window_end=now,
        updated_by_run_id=daily_run.forecast_model_run_id,
        geography_scope="category_only",
    )

    weekly_run = repository.create_run(
        forecast_product_name="weekly_7_day_demand",
        trigger_type="scheduled",
        source_cleaned_dataset_version_id="dataset-weekly",
        training_window_start=now - timedelta(days=28),
        training_window_end=now,
    )
    weekly_artifact = repository.create_artifact(
        forecast_product_name="weekly_7_day_demand",
        forecast_model_run_id=weekly_run.forecast_model_run_id,
        source_cleaned_dataset_version_id="dataset-weekly",
        geography_scope="category_only",
        model_family="lightgbm_global",
        baseline_method="historical_daily_mean",
        feature_schema_version="v1-weekly",
        artifact_path="/tmp/weekly-model.pkl",
        summary="weekly artifact",
    )
    repository.activate_artifact(
        forecast_product_name="weekly_7_day_demand",
        forecast_model_artifact_id=weekly_artifact.forecast_model_artifact_id,
        source_cleaned_dataset_version_id="dataset-weekly",
        training_window_start=now - timedelta(days=28),
        training_window_end=now,
        updated_by_run_id=weekly_run.forecast_model_run_id,
        geography_scope="category_only",
    )
    session.commit()

    refreshed_daily = repository.get_artifact(daily_artifact.forecast_model_artifact_id)
    refreshed_weekly = repository.get_artifact(weekly_artifact.forecast_model_artifact_id)
    assert refreshed_daily is not None and refreshed_daily.is_current is True
    assert refreshed_weekly is not None and refreshed_weekly.is_current is True
    assert repository.find_current_model("daily_1_day_demand").forecast_model_artifact_id == daily_artifact.forecast_model_artifact_id
    assert repository.find_current_model("weekly_7_day_demand").forecast_model_artifact_id == weekly_artifact.forecast_model_artifact_id


@pytest.mark.unit
def test_forecast_service_missing_model_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import forecast_service as module

    horizon_start = datetime(2026, 3, 22, 1, tzinfo=timezone.utc)
    assert module.compute_training_window_start(horizon_start, lookback_days=0) == horizon_start - timedelta(hours=1)

    run = SimpleNamespace(
        forecast_run_id="run-1",
        source_cleaned_dataset_version_id="dataset-1",
        requested_horizon_start=horizon_start,
        requested_horizon_end=horizon_start + timedelta(hours=24),
    )

    class RunRepo:
        def get_run(self, forecast_run_id):
            return run

        def finalize_generated(self, forecast_run_id, **kwargs):
            return SimpleNamespace(forecast_run_id=forecast_run_id, **kwargs)

        def finalize_reused(self, forecast_run_id, **kwargs):
            return SimpleNamespace(forecast_run_id=forecast_run_id, **kwargs)

        def finalize_failed(self, forecast_run_id, **kwargs):
            return SimpleNamespace(forecast_run_id=forecast_run_id, **kwargs)

    service = ForecastService(
        cleaned_dataset_repository=SimpleNamespace(
            list_current_cleaned_records=lambda source_name, **kwargs: [{"requested_at": "2026-03-18T09:00:00Z", "category": "Roads"}]
        ),
        forecast_run_repository=RunRepo(),
        forecast_repository=SimpleNamespace(find_current_for_horizon=lambda **kwargs: None),
        geomet_client=SimpleNamespace(fetch_hourly_conditions=lambda start, end: []),
        nager_date_client=SimpleNamespace(fetch_holidays=lambda year: []),
        forecast_model_repository=SimpleNamespace(
            find_current_model=lambda product: SimpleNamespace(
                source_cleaned_dataset_version_id="dataset-stale",
                artifact_path="/tmp/model.pkl",
            )
        ),
        settings=SimpleNamespace(source_name="edmonton_311", forecast_product_name="daily_1_day_demand", forecast_training_lookback_days=56),
    )
    monkeypatch.setattr(service.pipeline, "run", lambda prepared: (_ for _ in ()).throw(AssertionError("run should not be used")))

    failed = service.execute_run("run-1")
    assert failed.result_type == "missing_model"
    assert "stale" in failed.failure_reason


@pytest.mark.unit
def test_forecast_training_service_failure_and_helper_paths(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    from app.services import forecast_training_service as module

    window_end = datetime(2026, 3, 22, 12, tzinfo=timezone.utc)
    assert module.compute_training_window_start(window_end, lookback_days=0) == window_end - timedelta(hours=1)
    aware = datetime(2026, 3, 22, 12, tzinfo=timezone(timedelta(hours=-6)))
    assert module._ensure_utc(aware) == aware.astimezone(timezone.utc)

    settings = SimpleNamespace(
        source_name="edmonton_311",
        forecast_product_name="daily_1_day_demand",
        forecast_training_lookback_days=56,
        forecast_model_artifact_dir=str(tmp_path / "artifacts"),
    )

    class Repo:
        def __init__(self, run):
            self.run = run

        def get_run(self, forecast_model_run_id):
            return self.run

        def finalize_failed(self, forecast_model_run_id, **kwargs):
            return SimpleNamespace(forecast_model_run_id=forecast_model_run_id, **kwargs)

        def find_current_model(self, forecast_product_name):
            return None

    missing_run_service = module.ForecastTrainingService(
        cleaned_dataset_repository=SimpleNamespace(),
        forecast_model_repository=Repo(None),
        geomet_client=GeoMetClient(),
        nager_date_client=NagerDateClient(),
        settings=settings,
    )
    with pytest.raises(ValueError):
        missing_run_service.execute_run("missing")
    assert missing_run_service.load_current_artifact() is None

    missing_input_run = SimpleNamespace(
        forecast_model_run_id="model-run-missing",
        source_cleaned_dataset_version_id=None,
        training_window_start=window_end - timedelta(days=1),
        training_window_end=window_end,
    )
    missing_input_service = module.ForecastTrainingService(
        cleaned_dataset_repository=SimpleNamespace(),
        forecast_model_repository=Repo(missing_input_run),
        geomet_client=GeoMetClient(),
        nager_date_client=NagerDateClient(),
        settings=settings,
    )
    assert missing_input_service.execute_run("model-run-missing").result_type == "missing_input_data"

    empty_run = SimpleNamespace(
        forecast_model_run_id="model-run-empty",
        source_cleaned_dataset_version_id="dataset-1",
        training_window_start=window_end - timedelta(days=1),
        training_window_end=window_end,
    )
    empty_service = module.ForecastTrainingService(
        cleaned_dataset_repository=SimpleNamespace(list_current_cleaned_records=lambda source_name, **kwargs: []),
        forecast_model_repository=Repo(empty_run),
        geomet_client=GeoMetClient(),
        nager_date_client=NagerDateClient(),
        settings=settings,
    )
    assert empty_service.execute_run("model-run-empty").result_type == "missing_input_data"

    records_repo = SimpleNamespace(list_current_cleaned_records=lambda source_name, **kwargs: [{"requested_at": "2026-03-18T09:00:00Z", "category": "Roads"}])

    engine_service = module.ForecastTrainingService(
        cleaned_dataset_repository=records_repo,
        forecast_model_repository=Repo(empty_run),
        geomet_client=SimpleNamespace(fetch_hourly_conditions=lambda start, end: (_ for _ in ()).throw(GeoMetClientError("weather boom"))),
        nager_date_client=NagerDateClient(),
        settings=settings,
    )
    assert engine_service.execute_run("model-run-empty").result_type == "engine_failure"

    storage_service = module.ForecastTrainingService(
        cleaned_dataset_repository=records_repo,
        forecast_model_repository=Repo(empty_run),
        geomet_client=SimpleNamespace(fetch_hourly_conditions=lambda start, end: []),
        nager_date_client=SimpleNamespace(fetch_holidays=lambda year: []),
        settings=settings,
    )
    monkeypatch.setattr(storage_service.pipeline, "fit", lambda prepared: SimpleNamespace(geography_scope="category_only", model_family="lightgbm_global", baseline_method="historical_hourly_mean"))
    monkeypatch.setattr(storage_service, "_store_artifact", lambda artifact, artifact_path: (_ for _ in ()).throw(module.ForecastModelStorageError("store boom")))
    assert storage_service.execute_run("model-run-empty").result_type == "storage_failure"

    generic_service = module.ForecastTrainingService(
        cleaned_dataset_repository=records_repo,
        forecast_model_repository=Repo(empty_run),
        geomet_client=SimpleNamespace(fetch_hourly_conditions=lambda start, end: []),
        nager_date_client=SimpleNamespace(fetch_holidays=lambda year: []),
        settings=settings,
    )
    monkeypatch.setattr(generic_service.pipeline, "fit", lambda prepared: (_ for _ in ()).throw(RuntimeError("fit boom")))
    assert generic_service.execute_run("model-run-empty").result_type == "engine_failure"


@pytest.mark.unit
def test_geomet_forecast_transport_uses_forecast_collection_and_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    start = datetime(2026, 3, 22, tzinfo=timezone.utc)
    end = start + timedelta(hours=1)

    responses = {
        'forecast': _Response(
            200,
            {
                'type': 'Feature',
                'properties': {
                    'hourlyForecastGroup': {
                        'hourlyForecasts': [
                            {
                                'timestamp': '2026-03-22T00:00:00Z',
                                'temperature': {'value': {'en': -4.5}},
                                'lop': {'value': {'en': 30}},
                            }
                        ]
                    }
                },
            },
        ),
        'historical': _Response(
            200,
            {
                'features': [
                    {
                        'properties': {
                            'UTC_DATE': '2026-03-22T00:00:00Z',
                            'TEMP': 1.0,
                            'PRECIP_AMOUNT': 0.5,
                        }
                    }
                ]
            },
        ),
    }

    def fake_get(url, *, params=None, headers=None, timeout=None):
        if url.endswith('/collections/citypageweather-realtime/items/ab-50'):
            return responses['forecast']
        return responses['historical']

    monkeypatch.setattr('app.clients.geomet_client.httpx.get', fake_get)
    transport = GeoMetHttpTransport(
        base_url='https://api.weather.gc.ca',
        station_identifier='30165',
        station_selector='fixed_climate_identifier',
    )

    forecast = transport.fetch_forecast_hourly_conditions(start, end)
    assert forecast == [
        {
            'timestamp': datetime(2026, 3, 22, 0, 0, tzinfo=timezone.utc),
            'temperature_c': -4.5,
            'precipitation_mm': 0.3,
        }
    ]

    responses['forecast'] = _Response(200, {'properties': {'hourlyForecastGroup': {'hourlyForecasts': []}}})
    fallback = transport.fetch_forecast_hourly_conditions(start, end)
    assert fallback == [
        {
            'timestamp': datetime(2026, 3, 22, 0, 0, tzinfo=timezone.utc),
            'temperature_c': 1.0,
            'precipitation_mm': 0.5,
        }
    ]


@pytest.mark.unit
def test_forecast_service_merges_historical_and_forecast_weather_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import forecast_service as module

    horizon_start = datetime(2026, 3, 22, 1, tzinfo=timezone.utc)
    horizon_end = horizon_start + timedelta(hours=24)
    captured: dict[str, object] = {}

    def fake_prepare_forecast_features(**kwargs):
        captured['weather_rows'] = kwargs['weather_rows']
        return {
            'training_rows': [],
            'rows': [],
            'geography_scope': 'category_only',
        }

    monkeypatch.setattr(module, 'prepare_forecast_features', fake_prepare_forecast_features)

    run = SimpleNamespace(
        forecast_run_id='run-1',
        source_cleaned_dataset_version_id='dataset-1',
        requested_horizon_start=horizon_start,
        requested_horizon_end=horizon_end,
    )

    class RunRepo:
        def get_run(self, forecast_run_id):
            return run

        def finalize_generated(self, forecast_run_id, **kwargs):
            return SimpleNamespace(forecast_run_id=forecast_run_id, **kwargs)

        def finalize_failed(self, forecast_run_id, **kwargs):
            raise AssertionError(f'unexpected failure: {kwargs}')

        def finalize_reused(self, forecast_run_id, **kwargs):
            raise AssertionError('unexpected reuse')

    class GeoClient:
        def __init__(self):
            self.calls: list[tuple[str, datetime, datetime]] = []

        def fetch_historical_hourly_conditions(self, start, end):
            self.calls.append(('historical', start, end))
            return [
                {'timestamp': horizon_start - timedelta(hours=1), 'temperature_c': 2.0, 'precipitation_mm': 0.1},
            ]

        def fetch_forecast_hourly_conditions(self, start, end):
            self.calls.append(('forecast', start, end))
            return [
                {'timestamp': horizon_start, 'temperature_c': -3.0, 'precipitation_mm': 1.5},
            ]

    geomet_client = GeoClient()
    service = ForecastService(
        cleaned_dataset_repository=SimpleNamespace(
            list_current_cleaned_records=lambda source_name, **kwargs: [{'requested_at': '2026-03-21T23:00:00Z', 'category': 'Roads'}]
        ),
        forecast_run_repository=RunRepo(),
        forecast_repository=SimpleNamespace(find_current_for_horizon=lambda **kwargs: None),
        forecast_model_repository=SimpleNamespace(find_current_model=lambda product_name: None),
        geomet_client=geomet_client,
        nager_date_client=SimpleNamespace(fetch_holidays=lambda year: []),
        settings=SimpleNamespace(source_name='edmonton_311', forecast_product_name='daily_1_day_demand', forecast_training_lookback_days=56),
    )
    service.pipeline = SimpleNamespace(run=lambda prepared: {'baseline_method': 'baseline', 'geography_scope': 'category_only', 'buckets': []})
    service.bucket_service = SimpleNamespace(build_buckets=lambda generated: ([], 'category_only'))
    service.activation_service = SimpleNamespace(store_and_activate=lambda **kwargs: 'forecast-1')

    result = service.execute_run('run-1')

    assert result.forecast_version_id == 'forecast-1'
    assert [call[0] for call in geomet_client.calls] == ['historical', 'forecast']
    assert captured['weather_rows'] == [
        {'timestamp': horizon_start - timedelta(hours=1), 'temperature_c': 2.0, 'precipitation_mm': 0.1},
        {'timestamp': horizon_start, 'temperature_c': -3.0, 'precipitation_mm': 1.5},
    ]


@pytest.mark.unit
def test_geomet_forecast_payload_and_weather_helper_fallback_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.clients import geomet_client as geomet_module
    from app.services import forecast_service as forecast_module
    from app.services import forecast_training_service as training_module

    start = datetime(2026, 3, 22, tzinfo=timezone.utc)
    end = start + timedelta(hours=2)

    class _Response:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    transport = GeoMetHttpTransport(
        base_url='https://api.weather.gc.ca',
        station_identifier='30165',
        station_selector='fixed_climate_identifier',
    )

    monkeypatch.setattr(
        'app.clients.geomet_client.httpx.get',
        lambda *args, **kwargs: _Response(200, {'properties': {'hourlyForecastGroup': {'hourlyForecasts': 'not-a-list'}}}),
    )
    with pytest.raises(GeoMetClientError):
        transport.fetch_forecast_hourly_conditions(start, end)

    assert geomet_module._coerce_float(object()) == 0.0

    class HistoricalOnlyTransport:
        def fetch_hourly_conditions(self, horizon_start, horizon_end):
            return [{'timestamp': horizon_start, 'temperature_c': 1.0, 'precipitation_mm': 0.2}]

    class GenericTransport:
        def fetch(self, horizon_start, horizon_end):
            return [{'timestamp': horizon_start, 'temperature_c': 2.0, 'precipitation_mm': 0.3}]

    assert GeoMetClient(HistoricalOnlyTransport()).fetch_historical_hourly_conditions(start, end)[0]['temperature_c'] == 1.0
    assert GeoMetClient(HistoricalOnlyTransport()).fetch_forecast_hourly_conditions(start, end)[0]['precipitation_mm'] == 0.2
    assert GeoMetClient(GenericTransport()).fetch_historical_hourly_conditions(start, end)[0]['temperature_c'] == 2.0
    assert GeoMetClient(GenericTransport()).fetch_forecast_hourly_conditions(start, end)[0]['temperature_c'] == 2.0

    default_client = object.__new__(GeoMetClient)
    default_client.transport = None
    assert len(default_client.fetch_historical_hourly_conditions(start, end)) == 2
    assert len(default_client.fetch_forecast_hourly_conditions(start, end)) == 2

    assert forecast_module._fetch_historical_weather(object(), start, end) == []
    assert forecast_module._fetch_forecast_weather(object(), start, end) == []
    assert training_module._fetch_historical_weather(object(), start, end) == []

    merged = forecast_module._merge_weather_rows(
        [{'timestamp': 'bad-timestamp', 'temperature_c': 9.0, 'precipitation_mm': 9.0}],
        [{'timestamp': start, 'temperature_c': 3.0, 'precipitation_mm': 0.4}],
    )
    assert merged == [{'timestamp': start, 'temperature_c': 3.0, 'precipitation_mm': 0.4}]


@pytest.mark.unit
def test_geomet_forecast_parser_covers_payload_and_row_fallback_branches() -> None:
    from app.clients import geomet_client as module

    start = datetime(2026, 3, 22, 5, tzinfo=timezone.utc)
    end = start + timedelta(hours=2)

    assert module._nested_en_value({"en": "value"}) == "value"
    assert module._nested_en_value({"fr": "valeur"}) == {"fr": "valeur"}
    assert module._nested_en_value("plain") == "plain"

    with pytest.raises(GeoMetClientError):
        module._normalize_citypage_hourly_forecast("not-a-dict", horizon_start=start, horizon_end=end)
    with pytest.raises(GeoMetClientError):
        module._normalize_citypage_hourly_forecast({"type": "Feature"}, horizon_start=start, horizon_end=end)
    with pytest.raises(GeoMetClientError):
        module._normalize_citypage_hourly_forecast(
            {"type": "Feature", "properties": {}},
            horizon_start=start,
            horizon_end=end,
        )
    with pytest.raises(GeoMetClientError):
        module._normalize_citypage_hourly_forecast(
            {"type": "Feature", "properties": {"hourlyForecastGroup": {}}},
            horizon_start=start,
            horizon_end=end,
        )
    with pytest.raises(GeoMetClientError):
        module._normalize_citypage_hourly_forecast(
            {"type": "Feature", "properties": {"hourlyForecastGroup": {"hourlyForecasts": "bad"}}},
            horizon_start=start,
            horizon_end=end,
        )

    normalized = module._normalize_citypage_hourly_forecast(
        {
            "type": "Feature",
            "properties": {
                "hourlyForecastGroup": {
                    "hourlyForecasts": [
                        "skip-me",
                        {"timestamp": "bad-timestamp", "temperature": {"value": {"en": 1.0}}, "lop": {"value": {"en": 20}}},
                        {"timestamp": "2026-03-22T04:00:00Z", "temperature": {"value": {"en": 2.0}}, "lop": {"value": {"en": 30}}},
                        {"timestamp": "2026-03-22T05:00:00Z", "temperature": {"value": {"en": 3.0}}, "lop": {"value": {"en": 40}}},
                        {"timestamp": "2026-03-22T06:00:00Z", "temperature": {"value": {"en": 4.0}}, "lop": {"value": {"en": 50}}},
                    ]
                }
            },
        },
        horizon_start=start,
        horizon_end=end,
    )
    assert normalized == [
        {
            "timestamp": datetime(2026, 3, 22, 5, tzinfo=timezone.utc),
            "temperature_c": 3.0,
            "precipitation_mm": 0.4,
        },
        {
            "timestamp": datetime(2026, 3, 22, 6, tzinfo=timezone.utc),
            "temperature_c": 4.0,
            "precipitation_mm": 0.5,
        },
    ]

@pytest.mark.unit
def test_geomet_client_explicit_historical_forecast_and_default_paths() -> None:
    start = datetime(2026, 3, 22, tzinfo=timezone.utc)
    end = start + timedelta(hours=2)

    class ExplicitTransport:
        def fetch_historical_hourly_conditions(self, horizon_start, horizon_end):
            return [{'timestamp': horizon_start, 'temperature_c': 7.0, 'precipitation_mm': 0.7}]

        def fetch_forecast_hourly_conditions(self, horizon_start, horizon_end):
            return [{'timestamp': horizon_start, 'temperature_c': -1.0, 'precipitation_mm': 1.7}]

    client = GeoMetClient(ExplicitTransport())
    assert client.fetch_historical_hourly_conditions(start, end)[0]['temperature_c'] == 7.0
    assert client.fetch_forecast_hourly_conditions(start, end)[0]['precipitation_mm'] == 1.7

    default_client = object.__new__(GeoMetClient)
    default_client.transport = None
    assert len(default_client.fetch_forecast_hourly_conditions(start, end)) == 2


@pytest.mark.unit
def test_forecast_model_repository_helper_branches(session, tmp_path) -> None:
    from app.repositories.forecast_model_repository import ForecastModelRepository

    repository = ForecastModelRepository(session)

    run = repository.create_run(
        forecast_product_name="daily_1_day_demand",
        trigger_type="scheduled",
        source_cleaned_dataset_version_id="dataset-1",
        training_window_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        training_window_end=datetime(2026, 3, 23, tzinfo=timezone.utc),
    )
    artifact = repository.create_artifact(
        forecast_product_name="daily_1_day_demand",
        forecast_model_run_id=run.forecast_model_run_id,
        source_cleaned_dataset_version_id="dataset-1",
        geography_scope="category_only",
        model_family="lightgbm_global",
        baseline_method="historical_mean",
        feature_schema_version="hourly-v1",
        artifact_path=str(tmp_path / "hourly.pkl"),
        summary="stored artifact",
    )

    assert repository.get_current_marker("daily_1_day_demand") is None
    assert repository.find_current_model("daily_1_day_demand") is None

    repository.activate_artifact(
        forecast_product_name="daily_1_day_demand",
        forecast_model_artifact_id=artifact.forecast_model_artifact_id,
        source_cleaned_dataset_version_id="dataset-1",
        training_window_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        training_window_end=datetime(2026, 3, 23, tzinfo=timezone.utc),
        updated_by_run_id=run.forecast_model_run_id,
        geography_scope="category_only",
    )
    session.commit()

    current = repository.find_current_model("daily_1_day_demand")
    assert current is not None
    assert current.forecast_model_artifact_id == artifact.forecast_model_artifact_id

    artifact.storage_status = "pending"
    session.commit()
    assert repository.find_current_model("daily_1_day_demand") is None

    with pytest.raises(ValueError, match="Forecast model run not found"):
        repository.finalize_failed(
            "missing-run",
            result_type="engine_failure",
            failure_reason="boom",
            summary="failed",
        )

    with pytest.raises(ValueError, match="Forecast model run not found"):
        repository.finalize_trained(
            "missing-run",
            forecast_model_artifact_id=artifact.forecast_model_artifact_id,
            geography_scope="category_only",
            summary="trained",
        )

    with pytest.raises(ValueError, match="Forecast model artifact not found"):
        repository.activate_artifact(
            forecast_product_name="daily_1_day_demand",
            forecast_model_artifact_id="missing-artifact",
            source_cleaned_dataset_version_id="dataset-1",
            training_window_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
            training_window_end=datetime(2026, 3, 23, tzinfo=timezone.utc),
            updated_by_run_id=run.forecast_model_run_id,
            geography_scope="category_only",
        )
