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
def test_no_new_records_is_successful_no_change(seed_current_dataset, session) -> None:
    previous = DatasetRepository(session).get_current("edmonton_311")
    pipeline = IngestionPipeline(
        session,
        Edmonton311Client(FakeTransport("no_new_records")),
        IngestionLoggingService(logging.getLogger("test")),
    )

    result = pipeline.run()
    current = DatasetRepository(session).get_current("edmonton_311")
    cursor = CursorRepository(session).get("edmonton_311")
    records = DatasetRepository(session).list_dataset_records(previous.dataset_version_id)

    assert result.status == "success"
    assert result.result_type == "no_new_records"
    assert current.dataset_version_id == previous.dataset_version_id
    assert cursor is None
    assert len(records) == 1
