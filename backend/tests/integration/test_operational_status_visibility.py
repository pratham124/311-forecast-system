from __future__ import annotations

import logging

import pytest
from sqlalchemy import select

from app.clients.edmonton_311 import Edmonton311Client
from app.models import ValidationRun
from app.pipelines.ingestion.run_ingestion import IngestionPipeline
from app.services.ingestion_logging_service import IngestionLoggingService
from tests.conftest import FakeTransport


@pytest.mark.integration
def test_operational_routes_distinguish_approved_and_blocked_states(app_client, planner_headers, seed_current_dataset, session) -> None:
    approved_pipeline = IngestionPipeline(
        session,
        Edmonton311Client(FakeTransport("new_data")),
        IngestionLoggingService(logging.getLogger("test")),
    )
    approved_result = approved_pipeline.run()
    approved_run = session.scalars(select(ValidationRun).where(ValidationRun.ingestion_run_id == approved_result.run_id)).one()

    blocked_pipeline = IngestionPipeline(
        session,
        Edmonton311Client(FakeTransport("invalid_payload")),
        IngestionLoggingService(logging.getLogger("test")),
    )
    blocked_result = blocked_pipeline.run()
    blocked_run = session.scalars(select(ValidationRun).where(ValidationRun.ingestion_run_id == blocked_result.run_id)).one()

    approved_response = app_client.get(f"/api/v1/validation-runs/{approved_run.validation_run_id}", headers=planner_headers)
    blocked_response = app_client.get(f"/api/v1/validation-runs/{blocked_run.validation_run_id}", headers=planner_headers)

    assert approved_response.status_code == 200
    assert approved_response.json()["visibilityState"] == "approved_active"
    assert blocked_response.status_code == 200
    assert blocked_response.json()["visibilityState"] == "blocked"
