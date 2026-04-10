from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import HTTPException

import app.core.db as db_module
import app.main as main_module
from app.api.routes.approved_dataset_status import get_approved_dataset_status
from app.api.routes.review_needed_status import list_review_needed_datasets
from app.api.routes.validation_run_status import get_validation_run_status
from app.api.errors import WEATHER_OVERLAY_STATUS_MESSAGES
from app.core.auth import _decode_jwt_payload, get_current_claims, require_roles
from app.core.config import _to_bool, get_settings
from app.core.db import get_db_session, get_engine
from app.core.logging import (
    configure_logging,
    redact_value,
    sanitize_mapping,
    summarize_status,
    summarize_threshold_alert_failure,
)
from app.models.validation_models import _uuid
from app.repositories.approval_status_repository import ApprovalStatusRepository
from app.repositories.cursor_repository import CursorRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.review_needed_repository import ReviewNeededRepository
from app.repositories.run_repository import RunRepository
from app.repositories.validation_repository import ValidationRepository
from tests.conftest import build_token


class Creds:
    def __init__(self, token: str) -> None:
        self.credentials = token


@pytest.mark.unit
def test_auth_module_covers_decode_and_role_paths() -> None:
    claims = _decode_jwt_payload(build_token(["OperationalManager"]))
    assert claims["roles"] == ["OperationalManager"]

    with pytest.raises(HTTPException) as invalid_token:
        _decode_jwt_payload("invalid.token")
    assert invalid_token.value.status_code == 401

    with pytest.raises(HTTPException) as missing_bearer:
        get_current_claims(None)
    assert missing_bearer.value.status_code == 401

    dependency = require_roles("OperationalManager")
    assert dependency({"roles": ["OperationalManager"]}) == {"roles": ["OperationalManager"]}

    with pytest.raises(HTTPException) as invalid_roles:
        dependency({"roles": "wrong"})
    assert invalid_roles.value.status_code == 403

    with pytest.raises(HTTPException) as forbidden:
        dependency({"roles": ["Viewer"]})
    assert forbidden.value.status_code == 403


@pytest.mark.unit
def test_config_and_db_modules_cover_remaining_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _to_bool(None, True) is True
    assert _to_bool("true") is True
    assert _to_bool("false") is False

    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()
    with pytest.raises(RuntimeError):
        get_settings()

    db_module._engine = None
    db_module._session_factory = None
    create_engine_calls: list[tuple[str, bool, dict[str, object]]] = []

    def fake_create_engine(url, future=True, connect_args=None):
        create_engine_calls.append((url, future, connect_args or {}))
        return object()

    monkeypatch.setattr(db_module, "create_engine", fake_create_engine)
    monkeypatch.setattr(db_module, "get_settings", lambda: SimpleNamespace(database_url="postgresql://db"))
    engine = get_engine()
    assert engine is not None
    assert get_engine() is engine
    assert create_engine_calls == [("postgresql://db", True, {})]

    closed: list[bool] = []

    class FakeSession:
        def commit(self) -> None:
            return None

        def rollback(self) -> None:
            return None

        def close(self) -> None:
            closed.append(True)

    db_module._session_factory = lambda: FakeSession()
    generator = get_db_session()
    next(generator)
    with pytest.raises(StopIteration):
        next(generator)
    assert closed == [True]


@pytest.mark.unit
def test_reconcile_legacy_migration_state_stamps_uc01(monkeypatch: pytest.MonkeyPatch) -> None:
    stamps: list[str] = []

    class FakeInspector:
        def get_table_names(self):
            return sorted(db_module.UC01_TABLES)

        def get_columns(self, table_name):
            assert table_name == "dataset_versions"
            return [{"name": "dataset_version_id"}]

    monkeypatch.setattr(db_module, "inspect", lambda engine: FakeInspector())
    monkeypatch.setattr(db_module, "get_engine", lambda: object())
    monkeypatch.setattr(db_module.command, "stamp", lambda config, revision: stamps.append(revision))

    db_module._reconcile_legacy_migration_state(SimpleNamespace())
    assert stamps == ["001_uc01_ingestion_foundation"]


@pytest.mark.unit
def test_reconcile_legacy_migration_state_stamps_uc02(monkeypatch: pytest.MonkeyPatch) -> None:
    stamps: list[str] = []

    class FakeInspector:
        def get_table_names(self):
            return sorted(db_module.UC01_TABLES | db_module.UC02_TABLES)

        def get_columns(self, table_name):
            assert table_name == "dataset_versions"
            return [
                {"name": "dataset_version_id"},
                {"name": "source_dataset_version_id"},
                {"name": "dataset_kind"},
                {"name": "duplicate_group_count"},
                {"name": "approved_by_validation_run_id"},
            ]

    monkeypatch.setattr(db_module, "inspect", lambda engine: FakeInspector())
    monkeypatch.setattr(db_module, "get_engine", lambda: object())
    monkeypatch.setattr(db_module.command, "stamp", lambda config, revision: stamps.append(revision))

    db_module._reconcile_legacy_migration_state(SimpleNamespace())
    assert stamps == ["002_uc02_validation_pipeline"]


@pytest.mark.unit
def test_reconcile_legacy_migration_state_skips_when_alembic_version_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    stamps: list[str] = []

    class FakeInspector:
        def get_table_names(self):
            return ["alembic_version", *sorted(db_module.UC01_TABLES)]

        def get_columns(self, table_name):
            raise AssertionError("get_columns should not be called when alembic_version exists")

    monkeypatch.setattr(db_module, "inspect", lambda engine: FakeInspector())
    monkeypatch.setattr(db_module, "get_engine", lambda: object())
    monkeypatch.setattr(db_module.command, "stamp", lambda config, revision: stamps.append(revision))

    db_module._reconcile_legacy_migration_state(SimpleNamespace())
    assert stamps == []

    db_module._engine = None
    db_module._session_factory = None


@pytest.mark.unit
def test_expand_local_frontend_origins_covers_127_alias() -> None:
    assert main_module._expand_local_frontend_origins('http://127.0.0.1:5173') == [
        'http://127.0.0.1:5173',
        'http://localhost:5173',
    ]

@pytest.mark.unit
def test_expand_local_frontend_origins_keeps_non_local_origin() -> None:
    assert main_module._expand_local_frontend_origins('https://forecast.edmonton.ca') == [
        'https://forecast.edmonton.ca',
    ]


@pytest.mark.unit
def test_logging_helpers_cover_remaining_paths() -> None:
    assert redact_value(None) is None
    assert redact_value("abcd") == "***"
    assert redact_value([{"token": "abc12345"}, 3])[1] == 3
    nested = sanitize_mapping({"secret": "abc12345", "items": [{"password": "secret"}, "keep"]})
    assert nested["secret"] != "abc12345"
    assert nested["items"][0]["password"] != "secret"
    assert nested["items"][1] == "keep"
    summary = summarize_status("event", password="abc12345")
    assert summary["message"] == "event"
    assert summary["password"] != "abc12345"
    alert_failure = summarize_threshold_alert_failure("threshold.failed", run_id="run-1")
    assert alert_failure["message"] == "threshold.failed"
    assert alert_failure["outcome"] == "failure"
    assert configure_logging().name == "forecast_system"
    assert WEATHER_OVERLAY_STATUS_MESSAGES["retrieval-failed"].startswith("Weather data retrieval failed")


@pytest.mark.unit
@pytest.mark.anyio
async def test_main_create_app_and_lifespan_cover_remaining_paths(monkeypatch: pytest.MonkeyPatch) -> None:
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
    monkeypatch.setattr(main_module, "run_migrations", lambda: events.append("run_migrations"))
    monkeypatch.setattr(main_module, "get_session_factory", lambda: lambda: "session")
    monkeypatch.setattr(main_module, "get_settings", lambda: SimpleNamespace(scheduler_enabled=True, scheduler_cron="*/5 * * * *"))

    app = main_module.create_app()
    assert app.state.session_factory() == "session"
    assert "run_migrations" in events

    async with app.router.lifespan_context(app):
        pass

    assert "register:edmonton_311_ingestion:*/5 * * * *" in events
    assert "start" in events
    assert "shutdown" in events


@pytest.mark.unit
def test_routes_cover_direct_handler_paths(session, monkeypatch: pytest.MonkeyPatch) -> None:
    approved_service = SimpleNamespace(
        get_current_approved_dataset=lambda source_name: SimpleNamespace(dataset_version_id=source_name)
    )
    monkeypatch.setattr("app.api.routes.approved_dataset_status.ApprovalStatusService", lambda repo: approved_service)
    monkeypatch.setattr("app.api.routes.approved_dataset_status.get_settings", lambda: SimpleNamespace(source_name="edmonton_311"))
    assert get_approved_dataset_status(session=session, _claims={}).dataset_version_id == "edmonton_311"

    validation_service = SimpleNamespace(
        get_validation_run_status=lambda run_id: SimpleNamespace(validation_run_id=run_id)
    )
    monkeypatch.setattr("app.api.routes.validation_run_status.ValidationStatusService", lambda a, r: validation_service)
    run_id = UUID("00000000-0000-0000-0000-000000000001")
    assert get_validation_run_status(validation_run_id=run_id, session=session, _claims={}).validation_run_id == str(run_id)

    review_service = SimpleNamespace(list_review_needed=lambda run_id: SimpleNamespace(items=[run_id]))
    monkeypatch.setattr("app.api.routes.review_needed_status.ValidationStatusService", lambda a, r: review_service)
    assert list_review_needed_datasets(validation_run_id=None, session=session, _claims={}).items == [None]


@pytest.mark.unit
def test_validation_model_uuid_helper_is_executable() -> None:
    assert len(_uuid()) == 36


@pytest.mark.unit
def test_repositories_cover_remaining_paths(session) -> None:
    cursor_repo = CursorRepository(session)
    assert cursor_repo.get("missing") is None
    inserted = cursor_repo.upsert("edmonton_311", "cursor-1", "run-1")
    assert inserted.cursor_value == "cursor-1"

    run_repo = RunRepository(session)
    ingestion_run = run_repo.create_run("manual", None)
    assert run_repo.get_run(ingestion_run.run_id) == ingestion_run
    with pytest.raises(ValueError):
        run_repo.finalize_run("missing", "failed", "error")

    dataset_repo = DatasetRepository(session)
    source_dataset = dataset_repo.create_dataset_version("edmonton_311", ingestion_run.run_id, None, 1)
    activated = dataset_repo.activate_dataset("edmonton_311", source_dataset.dataset_version_id, ingestion_run.run_id)
    assert activated.dataset_version_id == source_dataset.dataset_version_id

    validation_repo = ValidationRepository(session)
    validation_run = validation_repo.create_run(ingestion_run.run_id, source_dataset.dataset_version_id, 20)
    validation_repo.record_validation_result(
        validation_run.validation_run_id,
        status="passed",
        required_field_check="passed",
        type_check="passed",
        format_check="passed",
        completeness_check="passed",
        issue_summary=None,
    )
    analysis = validation_repo.record_duplicate_analysis(
        validation_run.validation_run_id,
        status="review_needed",
        total_record_count=2,
        duplicate_record_count=1,
        duplicate_percentage=50,
        threshold_percentage=20,
        duplicate_group_count=1,
    )
    validation_repo.record_duplicate_groups(
        analysis.duplicate_analysis_id,
        [{"group_key": "key", "source_record_count": 2, "resolution_status": "consolidated", "cleaned_record_id": None, "resolution_summary": "done"}],
    )
    validation_repo.finalize_run(validation_run.validation_run_id, status="review_needed", duplicate_percentage=50, review_reason="review")
    assert validation_repo.get_run(validation_run.validation_run_id) is not None
    with pytest.raises(ValueError):
        validation_repo.finalize_run("missing", status="failed")

    approval_repo = ApprovalStatusRepository(session)
    assert approval_repo.get_current_marker("edmonton_311") is not None
    assert approval_repo.get_dataset_version(source_dataset.dataset_version_id) == source_dataset
    assert approval_repo.get_validation_run(validation_run.validation_run_id) is not None

    cleaned_dataset = dataset_repo.create_dataset_version(
        "edmonton_311",
        ingestion_run.run_id,
        None,
        1,
        dataset_kind="cleaned",
        source_dataset_version_id=source_dataset.dataset_version_id,
    )
    approved_run = validation_repo.create_run(ingestion_run.run_id, source_dataset.dataset_version_id, 20)
    validation_repo.finalize_run(
        approved_run.validation_run_id,
        status="approved",
        approved_dataset_version_id=cleaned_dataset.dataset_version_id,
    )
    assert approval_repo.get_validation_run_by_approved_dataset(cleaned_dataset.dataset_version_id) is not None

    review_repo = ReviewNeededRepository(session)
    review_repo.create(validation_run.validation_run_id, analysis.duplicate_analysis_id, "reason")
    assert len(review_repo.list()) == 1
    assert len(review_repo.list(validation_run.validation_run_id)) == 1
