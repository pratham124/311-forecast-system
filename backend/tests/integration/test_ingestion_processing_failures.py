from __future__ import annotations

import logging

import pytest

from app.clients.edmonton_311 import Edmonton311Client
from app.pipelines.ingestion.run_ingestion import IngestionPipeline
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.failure_notification_repository import FailureNotificationRepository
from app.services.ingestion_logging_service import IngestionLoggingService
from tests.conftest import FakeTransport


@pytest.mark.integration
def test_validation_failure_rejects_candidate_and_preserves_current(seed_current_dataset, session) -> None:
    previous = DatasetRepository(session).get_current("edmonton_311")
    pipeline = IngestionPipeline(
        session,
        Edmonton311Client(FakeTransport("invalid_payload")),
        IngestionLoggingService(logging.getLogger("test")),
    )

    result = pipeline.run()
    current = DatasetRepository(session).get_current("edmonton_311")

    assert result.result_type == "validation_failure"
    assert result.candidate_dataset_id is not None
    assert current.dataset_version_id == previous.dataset_version_id
    assert DatasetRepository(session).list_dataset_records(previous.dataset_version_id)


@pytest.mark.integration
def test_storage_failure_does_not_activate_new_dataset(seed_current_dataset, session) -> None:
    previous = DatasetRepository(session).get_current("edmonton_311")
    pipeline = IngestionPipeline(
        session,
        Edmonton311Client(FakeTransport("new_data")),
        IngestionLoggingService(logging.getLogger("test")),
    )

    result = pipeline.run(inject_storage_failure=True)
    current = DatasetRepository(session).get_current("edmonton_311")
    notifications = FailureNotificationRepository(session).list(run_id=result.run_id)

    assert result.result_type == "storage_failure"
    assert current.dataset_version_id == previous.dataset_version_id
    assert len(notifications) == 1
    assert DatasetRepository(session).list_dataset_records(previous.dataset_version_id)
