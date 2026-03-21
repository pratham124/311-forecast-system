from __future__ import annotations

import logging

import pytest
from sqlalchemy import select

from app.clients.edmonton_311 import Edmonton311Client
from app.core.config import get_settings
from app.models import DuplicateGroup, ValidationRun
from app.pipelines.ingestion.run_ingestion import IngestionPipeline
from app.repositories.dataset_repository import DatasetRepository
from app.services.ingestion_logging_service import IngestionLoggingService
from tests.conftest import FakeTransport


@pytest.mark.integration
def test_clean_validation_flow_creates_cleaned_dataset_and_updates_marker(seed_current_dataset, session, monkeypatch) -> None:
    monkeypatch.setenv("DUPLICATE_REVIEW_THRESHOLD_PERCENTAGE", "50")
    get_settings.cache_clear()
    records = [
        {"service_request_id": "SR-1", "requested_at": "2026-03-16T10:00:00Z", "category": "Roads", "district": "NW"},
        {"service_request_id": "SR-1", "requested_at": "2026-03-16T10:00:00Z", "category": "Roads", "district": ""},
        {"service_request_id": "SR-2", "requested_at": "2026-03-16T11:00:00Z", "category": "Transit", "district": "SE"},
    ]
    pipeline = IngestionPipeline(
        session,
        Edmonton311Client(FakeTransport(records=records)),
        IngestionLoggingService(logging.getLogger("test")),
    )

    result = pipeline.run()

    current = DatasetRepository(session).get_current("edmonton_311")
    current_records = DatasetRepository(session).list_dataset_records(current.dataset_version_id)
    validation_run = session.scalars(select(ValidationRun).where(ValidationRun.ingestion_run_id == result.run_id)).one()
    groups = session.scalars(select(DuplicateGroup)).all()

    assert result.status == "success"
    assert result.result_type == "new_data"
    assert current is not None
    assert len(current_records) == 2
    assert validation_run.status == "approved"
    assert len(groups) == 1
