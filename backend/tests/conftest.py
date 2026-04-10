from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
import tempfile

import jwt
from pathlib import Path
from typing import Iterator
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{Path(tempfile.gettempdir()) / (f'bootstrap-test-{uuid4().hex}.db')}")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.ingestion import get_client
from app.clients.edmonton_311 import Edmonton311AuthError, Edmonton311Client, Edmonton311UnavailableError
from app.core import config as config_module
from app.core import db as db_module
from app.core.db import get_session_factory, run_migrations
from app.main import create_app
from app.repositories.dataset_repository import DatasetRepository


class FakeTransport:
    def __init__(self, mode: str = "new_data", records: list[dict] | None = None) -> None:
        self.mode = mode
        self.records = records or [
            {
                "service_request_id": "SR-1",
                "requested_at": "2026-03-16T10:00:00Z",
                "category": "Roads",
            }
        ]

    def fetch(self, cursor: str | None) -> list[dict]:
        if self.mode == "auth_failure":
            raise Edmonton311AuthError("invalid credentials")
        if self.mode == "source_unavailable":
            raise Edmonton311UnavailableError("timeout from upstream")
        if self.mode == "no_new_records":
            return []
        if self.mode == "invalid_payload":
            return [{"service_request_id": "SR-1"}]
        return self.records


def build_token(
    roles: list[str],
    *,
    secret: str | None = None,
    issuer: str | None = None,
    audience: str | None = None,
    expires_in_seconds: int = 3600,
) -> str:
    settings = config_module.get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "test-user",
        "email": "test-user@example.com",
        "roles": roles,
        "iss": issuer or settings.jwt_issuer,
        "aud": audience or settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in_seconds)).timestamp()),
        "token_type": "access",
    }
    return jwt.encode(payload, secret or settings.jwt_secret, algorithm="HS256")


import shutil

_template_db_path: Path | None = None

@pytest.fixture(scope="session", autouse=True)
def _prepare_template_db(tmp_path_factory: pytest.TempPathFactory) -> None:
    global _template_db_path
    template_dir = tmp_path_factory.mktemp("db_template")
    _template_db_path = template_dir / "template.db"
    
    # Run migrations once on the template db
    os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{_template_db_path}"
    config_module.get_settings.cache_clear()
    db_module._engine = None
    db_module._session_factory = None
    run_migrations()


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    test_db = tmp_path / 'test.db'
    if _template_db_path and _template_db_path.exists():
        shutil.copy(_template_db_path, test_db)
    
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{test_db}")
    monkeypatch.setenv("EDMONTON_311_SOURCE_NAME", "edmonton_311")
    config_module.get_settings.cache_clear()
    db_module._engine = None
    db_module._session_factory = None
    yield
    config_module.get_settings.cache_clear()
    db_module._engine = None
    db_module._session_factory = None


@pytest.fixture
def session() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def app_client() -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_client] = lambda: Edmonton311Client(FakeTransport())
    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def operational_manager_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {build_token(['OperationalManager'])}"}


@pytest.fixture
def planner_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {build_token(['CityPlanner'])}"}


@pytest.fixture
def viewer_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {build_token(['Viewer'])}"}


@pytest.fixture
def seed_current_dataset(session: Session) -> str:
    repository = DatasetRepository(session)
    version = repository.create_dataset_version(
        source_name="edmonton_311",
        run_id="seed-run",
        candidate_id=None,
        record_count=10,
        records=[
            {
                "service_request_id": "seed-1",
                "requested_at": "2026-03-15T00:00:00Z",
                "category": "Seed",
            }
        ],
    )
    repository.activate_dataset("edmonton_311", version.dataset_version_id, "seed-run")
    session.commit()
    return version.dataset_version_id
