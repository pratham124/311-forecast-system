from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Iterator

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./bootstrap-test.db")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.ingestion import get_client
from app.clients.edmonton_311 import Edmonton311AuthError, Edmonton311Client, Edmonton311UnavailableError
from app.core import config as config_module
from app.core import db as db_module
from app.core.db import Base, get_session_factory
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


def build_token(roles: list[str]) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({"roles": roles}).encode()).decode().rstrip("=")
    return f"{header}.{payload}.signature"


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("EDMONTON_311_SOURCE_NAME", "edmonton_311")
    config_module.get_settings.cache_clear()
    db_module._engine = None
    db_module._session_factory = None
    Base.metadata.create_all(bind=db_module.get_engine())
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
