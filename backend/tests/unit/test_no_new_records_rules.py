from __future__ import annotations

import logging

import pytest

from app.clients.edmonton_311 import Edmonton311Client
from app.pipelines.ingestion.run_ingestion import IngestionPipeline
from app.repositories.dataset_repository import DatasetRepository
from app.services.ingestion_logging_service import IngestionLoggingService
from tests.conftest import FakeTransport


@pytest.mark.unit
def test_no_new_records_does_not_create_dataset_version(seed_current_dataset, session) -> None:
    existing = DatasetRepository(session).get_current("edmonton_311")
    pipeline = IngestionPipeline(
        session,
        Edmonton311Client(FakeTransport("no_new_records")),
        IngestionLoggingService(logging.getLogger("test")),
    )

    result = pipeline.run()
    current = DatasetRepository(session).get_current("edmonton_311")

    assert result.result_type == "no_new_records"
    assert result.dataset_version_id is None
    assert current is not None
    assert current.dataset_version_id == existing.dataset_version_id
