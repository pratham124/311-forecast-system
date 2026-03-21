from __future__ import annotations

import logging

import pytest
from sqlalchemy import select

from app.clients.edmonton_311 import Edmonton311Client
from app.models import ValidationRun
from app.pipelines.ingestion.run_ingestion import IngestionPipeline
from app.repositories.dataset_repository import DatasetRepository
from app.services.ingestion_logging_service import IngestionLoggingService
from tests.conftest import FakeTransport


@pytest.mark.integration
def test_storage_failure_and_degraded_state_preserve_prior_approved_dataset(seed_current_dataset, session) -> None:
    previous = DatasetRepository(session).get_current("edmonton_311")
    pipeline = IngestionPipeline(
        session,
        Edmonton311Client(FakeTransport("new_data")),
        IngestionLoggingService(logging.getLogger("test")),
    )

    result = pipeline.run(inject_storage_failure=True)

    current = DatasetRepository(session).get_current("edmonton_311")
    validation_runs = session.scalars(select(ValidationRun).where(ValidationRun.ingestion_run_id == result.run_id)).all()

    assert result.result_type == "storage_failure"
    assert current.dataset_version_id == previous.dataset_version_id
    assert validation_runs == []
