from __future__ import annotations

import logging

import pytest
from sqlalchemy import select

from app.clients.edmonton_311 import Edmonton311Client
from app.core.config import get_settings
from app.models import CurrentForecastModelMarker, DuplicateGroup, ForecastModelArtifact, ForecastModelRun, ValidationRun
from app.pipelines.ingestion.run_ingestion import IngestionPipeline
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository
from app.services.ingestion_logging_service import IngestionLoggingService
from tests.conftest import FakeTransport


@pytest.mark.integration
def test_clean_validation_flow_creates_cleaned_dataset_and_updates_marker(seed_current_dataset, session, monkeypatch) -> None:
    monkeypatch.setenv("DUPLICATE_REVIEW_THRESHOLD_PERCENTAGE", "50")
    get_settings.cache_clear()
    records = [
        {"service_request_id": "SR-1", "requested_at": "2026-03-16T10:00:00Z", "category": "Roads", "district": "NW"},
        {"service_request_id": "SR-1", "requested_at": "2026-03-16T10:00:00Z", "category": "Roads", "district": ""},
        {"service_request_id": "SR-2", "requested_at": "2026-03-16T11:00:00Z", "category": "Transit", "district": "SE"},
    ]
    pipeline = IngestionPipeline(
        session,
        Edmonton311Client(FakeTransport(records=records)),
        IngestionLoggingService(logging.getLogger("test")),
    )

    result = pipeline.run()

    current = DatasetRepository(session).get_current("edmonton_311")
    current_records = CleanedDatasetRepository(session).list_current_cleaned_records("edmonton_311")
    validation_run = session.scalars(select(ValidationRun).where(ValidationRun.ingestion_run_id == result.run_id)).one()
    groups = session.scalars(select(DuplicateGroup)).all()
    model_runs = session.scalars(select(ForecastModelRun).order_by(ForecastModelRun.started_at.desc())).all()
    model_artifacts = session.scalars(select(ForecastModelArtifact).order_by(ForecastModelArtifact.trained_at.desc())).all()
    hourly_model_marker = session.get(CurrentForecastModelMarker, "daily_1_day_demand")
    weekly_model_marker = session.get(CurrentForecastModelMarker, "weekly_7_day_demand")

    assert result.status == "success"
    assert result.result_type == "new_data"
    assert current is not None
    assert current.record_count == 2
    assert len(current_records) == 2
    assert validation_run.status == "approved"
    assert len(groups) == 1
    assert len(model_runs) >= 2
    hourly_model_run = next(run for run in model_runs if run.forecast_product_name == "daily_1_day_demand")
    weekly_model_run = next(run for run in model_runs if run.forecast_product_name == "weekly_7_day_demand")
    assert hourly_model_run.trigger_type == "approval"
    assert weekly_model_run.trigger_type == "approval"
    assert hourly_model_run.status == "success"
    assert weekly_model_run.status == "success"
    hourly_artifact = next(artifact for artifact in model_artifacts if artifact.forecast_product_name == "daily_1_day_demand")
    weekly_artifact = next(artifact for artifact in model_artifacts if artifact.forecast_product_name == "weekly_7_day_demand")
    assert hourly_model_marker is not None
    assert weekly_model_marker is not None
    assert hourly_model_marker.forecast_model_artifact_id == hourly_artifact.forecast_model_artifact_id
    assert weekly_model_marker.forecast_model_artifact_id == weekly_artifact.forecast_model_artifact_id
