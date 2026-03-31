from __future__ import annotations

from app.models import HistoricalDemandAnalysisRequest
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository

import pytest


def _seed_warning_records(session) -> None:
    records = [
        {"service_request_id": f"roads-{idx}", "requested_at": f"2026-03-{idx:02d}T10:00:00Z", "category": "Roads", "ward": "Ward 1"}
        for idx in range(1, 10)
    ]
    version = DatasetRepository(session).create_dataset_version(
        source_name="edmonton_311",
        run_id="run-warning",
        candidate_id=None,
        record_count=len(records),
        records=records,
        validation_status="approved",
        dataset_kind="cleaned",
        approved_by_validation_run_id="validation-warning",
    )
    DatasetRepository(session).activate_dataset("edmonton_311", version.dataset_version_id, "run-warning")
    CleanedDatasetRepository(session).upsert_current_cleaned_records(
        source_name="edmonton_311",
        ingestion_run_id="run-warning",
        source_dataset_version_id=version.dataset_version_id,
        approved_dataset_version_id=version.dataset_version_id,
        approved_by_validation_run_id="validation-warning",
        cleaned_records=records,
    )
    session.commit()


@pytest.mark.integration
def test_historical_demand_warning_decline_does_not_persist_request(app_client, planner_headers, session):
    _seed_warning_records(session)
    response = app_client.post(
        "/api/v1/historical-demand/queries",
        headers=planner_headers,
        json={
            "timeRangeStart": "2025-01-01T00:00:00Z",
            "timeRangeEnd": "2026-12-31T23:59:59Z",
        },
    )
    assert response.status_code == 200
    assert response.json()["warning"]["shown"] is True
    assert session.query(HistoricalDemandAnalysisRequest).count() == 0


@pytest.mark.integration
def test_historical_demand_warning_acknowledge_executes_query(app_client, planner_headers, session):
    _seed_warning_records(session)
    response = app_client.post(
        "/api/v1/historical-demand/queries",
        headers=planner_headers,
        json={
            "timeRangeStart": "2025-01-01T00:00:00Z",
            "timeRangeEnd": "2026-12-31T23:59:59Z",
            "proceedAfterWarning": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["warning"]["acknowledged"] is True
    assert session.query(HistoricalDemandAnalysisRequest).count() == 1
