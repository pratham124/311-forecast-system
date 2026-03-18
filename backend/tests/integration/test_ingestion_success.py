from __future__ import annotations

import logging

import pytest

from app.clients.edmonton_311 import Edmonton311Client
from app.pipelines.ingestion.run_ingestion import IngestionPipeline
from app.repositories.cursor_repository import CursorRepository
from app.repositories.dataset_repository import DatasetRepository
from app.services.ingestion_logging_service import IngestionLoggingService
from tests.conftest import FakeTransport


@pytest.mark.integration
def test_successful_ingestion_creates_and_activates_new_dataset(seed_current_dataset, session) -> None:
    pipeline = IngestionPipeline(
        session,
        Edmonton311Client(FakeTransport("new_data")),
        IngestionLoggingService(logging.getLogger("test")),
    )

    result = pipeline.run(trigger_type="scheduled")

    current = DatasetRepository(session).get_current("edmonton_311")
    cursor = CursorRepository(session).get("edmonton_311")
    records = DatasetRepository(session).list_dataset_records(result.dataset_version_id)
    assert result.status == "success"
    assert result.result_type == "new_data"
    assert current is not None
    assert current.updated_by_run_id == result.run_id
    assert cursor is not None
    assert len(records) == result.records_received
    assert records[0].source_record_id == "SR-1"
