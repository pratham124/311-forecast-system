from __future__ import annotations

import logging

import pytest

from app.clients.edmonton_311 import Edmonton311Client
from app.pipelines.ingestion.run_ingestion import IngestionPipeline
from app.services.ingestion_logging_service import IngestionLoggingService
from tests.conftest import FakeTransport


@pytest.mark.contract
def test_review_needed_endpoint_lists_blocked_datasets(app_client, planner_headers, seed_current_dataset, session) -> None:
    records = [
        {"service_request_id": "SR-1", "requested_at": "2026-03-16T10:00:00Z", "category": "Roads"},
        {"service_request_id": "SR-1", "requested_at": "2026-03-16T10:01:00Z", "category": "Roads"},
        {"service_request_id": "SR-2", "requested_at": "2026-03-16T10:02:00Z", "category": "Roads"},
    ]
    pipeline = IngestionPipeline(
        session,
        Edmonton311Client(FakeTransport(records=records)),
        IngestionLoggingService(logging.getLogger("test")),
    )
    pipeline.run()

    response = app_client.get("/api/v1/datasets/review-needed", headers=planner_headers)

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["validationRunId"]
    assert payload["items"][0]["reason"]
