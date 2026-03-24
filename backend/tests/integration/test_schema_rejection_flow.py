from __future__ import annotations

import logging

import pytest
from sqlalchemy import select

from app.clients.edmonton_311 import Edmonton311Client
from app.models import DuplicateAnalysisResult, ForecastModelRun, ValidationRun
from app.pipelines.ingestion.run_ingestion import IngestionPipeline
from app.repositories.dataset_repository import DatasetRepository
from app.services.ingestion_logging_service import IngestionLoggingService
from tests.conftest import FakeTransport


@pytest.mark.integration
def test_schema_rejection_preserves_prior_approved_dataset(seed_current_dataset, session) -> None:
    previous = DatasetRepository(session).get_current("edmonton_311")
    pipeline = IngestionPipeline(
        session,
        Edmonton311Client(FakeTransport("invalid_payload")),
        IngestionLoggingService(logging.getLogger("test")),
    )

    result = pipeline.run()

    current = DatasetRepository(session).get_current("edmonton_311")
    validation_run = session.scalars(select(ValidationRun).where(ValidationRun.ingestion_run_id == result.run_id)).one()
    duplicate_results = session.scalars(select(DuplicateAnalysisResult)).all()
    model_runs = session.scalars(select(ForecastModelRun)).all()

    assert result.status == "success"
    assert result.result_type == "rejected"
    assert validation_run.status == "rejected"
    assert current.dataset_version_id == previous.dataset_version_id
    assert duplicate_results == []
    assert model_runs == []
