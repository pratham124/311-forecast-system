from __future__ import annotations

import importlib
import logging

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine

from app.core import config as config_module
from app.core.auth import _decode_jwt_payload, get_current_claims, require_roles
from app.core.db import get_db_session, get_engine
from app.core.logging import configure_logging, redact_value, sanitize_mapping


class Creds:
    def __init__(self, token: str) -> None:
        self.credentials = token


@pytest.mark.unit
def test_creds_stores_token() -> None:
    assert Creds("token").credentials == "token"


@pytest.mark.unit
def test_decode_jwt_payload_rejects_bad_structure() -> None:
    with pytest.raises(HTTPException) as exc:
        _decode_jwt_payload("bad-token")
    assert exc.value.status_code == 401


@pytest.mark.unit
def test_get_current_claims_requires_credentials() -> None:
    with pytest.raises(HTTPException) as exc:
        get_current_claims(None)
    assert exc.value.status_code == 401


@pytest.mark.unit
def test_require_roles_rejects_non_list_roles() -> None:
    dependency = require_roles("OperationalManager")
    with pytest.raises(HTTPException) as exc:
        dependency({"roles": "OperationalManager"})
    assert exc.value.status_code == 403


@pytest.mark.unit
def test_to_bool_defaults_when_value_missing() -> None:
    assert config_module._to_bool(None, default=True) is True


@pytest.mark.unit
def test_to_bool_returns_false_for_non_truthy_string() -> None:
    assert config_module._to_bool("false") is False


@pytest.mark.unit
def test_get_settings_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    config_module.get_settings.cache_clear()
    with pytest.raises(RuntimeError):
        config_module.get_settings()
    config_module.get_settings.cache_clear()


@pytest.mark.unit
def test_get_engine_non_sqlite_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    config_module.get_settings.cache_clear()
    import app.core.db as db_module

    original_create_engine = db_module.create_engine
    db_module.create_engine = lambda *args, **kwargs: create_engine("sqlite:///:memory:")
    db_module._engine = None
    engine = get_engine()

    assert engine.url.drivername.startswith("sqlite")
    db_module.create_engine = original_create_engine
    db_module._engine = None
    config_module.get_settings.cache_clear()


@pytest.mark.unit
def test_get_db_session_closes_session() -> None:
    generator = get_db_session()
    session = next(generator)
    assert session.is_active is True
    with pytest.raises(StopIteration):
        generator.close()
        next(generator)


@pytest.mark.unit
def test_get_session_factory_returns_cached_factory() -> None:
    import app.core.db as db_module

    db_module._session_factory = None
    first = db_module.get_session_factory()
    second = db_module.get_session_factory()
    assert first is second


@pytest.mark.unit
def test_redact_value_handles_none_dict_list_and_passthrough() -> None:
    assert redact_value(None) is None
    assert redact_value("abcd") == "***"
    assert redact_value(5) == 5
    assert redact_value({"token": "secret"})["token"] != "secret"
    assert redact_value(["abcd", {"token": "secret"}])[0] == "***"


@pytest.mark.unit
def test_sanitize_mapping_handles_nested_values() -> None:
    payload = sanitize_mapping(
        {
            "nested": {"password": "abc123"},
            "items": [{"authorization": "token-value"}, {"plain": 1}],
        }
    )
    assert payload["nested"]["password"] != "abc123"
    assert payload["items"][0]["authorization"] != "token-value"
    assert payload["items"][1]["plain"] == 1


@pytest.mark.unit
def test_configure_logging_returns_named_logger() -> None:
    logger = configure_logging()
    assert isinstance(logger, logging.Logger)
    assert logger.name == "forecast_system"


@pytest.mark.unit
def test_protocol_module_imports() -> None:
    module = importlib.import_module("app.repositories.ingestion_repository")
    assert hasattr(module, "CursorRepositoryProtocol")
