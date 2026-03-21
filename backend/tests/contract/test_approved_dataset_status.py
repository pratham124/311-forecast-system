from __future__ import annotations

import pytest

from app.clients.edmonton_311 import Edmonton311Client
from app.pipelines.ingestion.run_ingestion import IngestionPipeline
from app.services.ingestion_logging_service import IngestionLoggingService
from tests.conftest import FakeTransport


@pytest.mark.contract
def test_approved_dataset_status_endpoint_returns_current_cleaned_dataset(app_client, planner_headers, session) -> None:
    pipeline = IngestionPipeline(
        session,
        Edmonton311Client(FakeTransport("new_data")),
        IngestionLoggingService(__import__("logging").getLogger("test")),
    )
    pipeline.run()

    response = app_client.get("/api/v1/datasets/approved/current", headers=planner_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["datasetVersionId"]
    assert payload["cleanedRecordCount"] == 1
    assert payload["summary"] == "Current approved cleaned dataset."
