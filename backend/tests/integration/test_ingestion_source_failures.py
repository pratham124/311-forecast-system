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
@pytest.mark.parametrize("mode, expected", [("auth_failure", "auth_failure"), ("source_unavailable", "source_unavailable")])
def test_source_failures_preserve_current_dataset(seed_current_dataset, session, mode, expected) -> None:
    previous = DatasetRepository(session).get_current("edmonton_311")
    pipeline = IngestionPipeline(
        session,
        Edmonton311Client(FakeTransport(mode)),
        IngestionLoggingService(logging.getLogger("test")),
    )

    result = pipeline.run()
    current = DatasetRepository(session).get_current("edmonton_311")
    notifications = FailureNotificationRepository(session).list(run_id=result.run_id)

    assert result.status == "failed"
    assert result.result_type == expected
    assert current is not None
    assert current.dataset_version_id == previous.dataset_version_id
    assert len(notifications) == 1
