from __future__ import annotations

import logging

import pytest
from sqlalchemy import select

from app.clients.edmonton_311 import Edmonton311Client
from app.models import ReviewNeededRecord, ValidationRun
from app.pipelines.ingestion.run_ingestion import IngestionPipeline
from app.repositories.dataset_repository import DatasetRepository
from app.services.ingestion_logging_service import IngestionLoggingService
from tests.conftest import FakeTransport


@pytest.mark.integration
def test_excessive_duplicate_percentage_blocks_approval(seed_current_dataset, session, monkeypatch) -> None:
    monkeypatch.setenv("DUPLICATE_REVIEW_THRESHOLD_PERCENTAGE", "20")
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

    result = pipeline.run()

    current = DatasetRepository(session).get_current("edmonton_311")
    validation_run = session.scalars(select(ValidationRun).where(ValidationRun.ingestion_run_id == result.run_id)).one()
    review_record = session.scalars(select(ReviewNeededRecord)).one()

    assert result.result_type == "review_needed"
    assert validation_run.status == "review_needed"
    assert current.dataset_version_id == previous.dataset_version_id
    assert review_record.validation_run_id == validation_run.validation_run_id
