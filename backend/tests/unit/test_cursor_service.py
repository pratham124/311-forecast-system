from __future__ import annotations

import logging

import pytest

from app.clients.edmonton_311 import Edmonton311Client
from app.pipelines.ingestion.run_ingestion import IngestionPipeline
from app.repositories.cursor_repository import CursorRepository
from app.services.ingestion_logging_service import IngestionLoggingService
from tests.conftest import FakeTransport


@pytest.mark.unit
def test_cursor_created_after_successful_new_data_run(session) -> None:
    pipeline = IngestionPipeline(
        session,
        Edmonton311Client(FakeTransport("new_data")),
        IngestionLoggingService(logging.getLogger("test")),
    )

    result = pipeline.run()

    cursor = CursorRepository(session).get("edmonton_311")
    assert result.result_type == "new_data"
    assert result.cursor_advanced is True
    assert cursor is not None
    assert cursor.updated_by_run_id == result.run_id


@pytest.mark.unit
def test_cursor_not_advanced_for_no_new_records(session) -> None:
    pipeline = IngestionPipeline(
        session,
        Edmonton311Client(FakeTransport("no_new_records")),
        IngestionLoggingService(logging.getLogger("test")),
    )

    result = pipeline.run()

    cursor = CursorRepository(session).get("edmonton_311")
    assert result.result_type == "no_new_records"
    assert result.cursor_advanced is False
    assert cursor is None
