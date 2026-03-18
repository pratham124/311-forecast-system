from __future__ import annotations

import logging

import pytest

from app.clients.edmonton_311 import Edmonton311Client
from app.pipelines.ingestion.run_ingestion import IngestionPipeline
from app.repositories.dataset_repository import DatasetRepository
from app.services.ingestion_logging_service import IngestionLoggingService
from tests.conftest import FakeTransport


@pytest.mark.integration
def test_failed_run_never_changes_current_dataset(seed_current_dataset, session) -> None:
    previous = DatasetRepository(session).get_current("edmonton_311")
    pipeline = IngestionPipeline(
        session,
        Edmonton311Client(FakeTransport("new_data")),
        IngestionLoggingService(logging.getLogger("test")),
    )

    result = pipeline.run(inject_storage_failure=True)
    current = DatasetRepository(session).get_current("edmonton_311")

    assert result.status == "failed"
    assert current.dataset_version_id == previous.dataset_version_id
