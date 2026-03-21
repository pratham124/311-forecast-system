from __future__ import annotations

from sqlalchemy import select

import pytest

from app.models import ValidationRun
from app.pipelines.ingestion.validation_pipeline import ValidationPipeline


@pytest.mark.contract
def test_validation_run_status_endpoint_returns_expected_payload(app_client, planner_headers, session) -> None:
    source_dataset = __import__("app.repositories.dataset_repository", fromlist=["DatasetRepository"]).DatasetRepository(session).create_dataset_version(
        source_name="edmonton_311",
        run_id="run-1",
        candidate_id=None,
        record_count=1,
        records=[{"service_request_id": "SR-1", "requested_at": "2026-03-16T10:00:00Z", "category": "Roads"}],
    )
    validation_run_id = ValidationPipeline(session).run(
        ingestion_run_id="run-1",
        source_dataset_version_id=source_dataset.dataset_version_id,
        records=[{"service_request_id": "SR-1", "requested_at": "2026-03-16T10:00:00Z", "category": "Roads"}],
    )
    session.commit()

    response = app_client.get(f"/api/v1/validation-runs/{validation_run_id}", headers=planner_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["validationRunId"] == validation_run_id
    assert payload["status"] == "approved"
    assert payload["visibilityState"] == "approved_active"
    assert payload["summary"]
