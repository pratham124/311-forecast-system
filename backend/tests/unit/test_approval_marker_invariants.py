from __future__ import annotations

import logging

import pytest

from app.clients.edmonton_311 import Edmonton311Client
from app.pipelines.ingestion.run_ingestion import IngestionPipeline
from app.repositories.dataset_repository import DatasetRepository
from app.services.ingestion_logging_service import IngestionLoggingService
from tests.conftest import FakeTransport


@pytest.mark.unit
def test_rejected_validation_preserves_existing_marker(seed_current_dataset, session) -> None:
    previous = DatasetRepository(session).get_current("edmonton_311")
    pipeline = IngestionPipeline(
        session,
        Edmonton311Client(FakeTransport("invalid_payload")),
        IngestionLoggingService(logging.getLogger("test")),
    )

    pipeline.run()

    current = DatasetRepository(session).get_current("edmonton_311")
    assert current.dataset_version_id == previous.dataset_version_id


@pytest.mark.unit
def test_review_needed_validation_preserves_existing_marker(seed_current_dataset, session) -> None:
    records = [
        {"service_request_id": "SR-1", "requested_at": "2026-03-16T10:00:00Z", "category": "Roads"},
        {"service_request_id": "SR-1", "requested_at": "2026-03-16T10:01:00Z", "category": "Roads"},
        {"service_request_id": "SR-2", "requested_at": "2026-03-16T10:02:00Z", "category": "Roads"},
    ]
    previous = DatasetRepository(session).get_current("edmonton_311")
    pipeline = IngestionPipeline(
        session,
        Edmonton311Client(FakeTransport(records=records)),
        IngestionLoggingService(logging.getLogger("test")),
    )

    pipeline.run()

    current = DatasetRepository(session).get_current("edmonton_311")
    assert current.dataset_version_id == previous.dataset_version_id
