from __future__ import annotations

from app.models import HistoricalAnalysisOutcomeRecord, HistoricalDemandAnalysisRequest
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository

import pytest


def _seed_failure_records(session) -> None:
    records = [
        {"service_request_id": "roads-1", "requested_at": "2026-03-05T10:00:00Z", "category": "Roads", "ward": "Ward 1"},
    ]
    version = DatasetRepository(session).create_dataset_version(
        source_name="edmonton_311",
        run_id="run-failure",
        candidate_id=None,
        record_count=len(records),
        records=records,
        validation_status="approved",
        dataset_kind="cleaned",
        approved_by_validation_run_id="validation-failure",
    )
    DatasetRepository(session).activate_dataset("edmonton_311", version.dataset_version_id, "run-failure")
    CleanedDatasetRepository(session).upsert_current_cleaned_records(
        source_name="edmonton_311",
        ingestion_run_id="run-failure",
        source_dataset_version_id=version.dataset_version_id,
        approved_dataset_version_id=version.dataset_version_id,
        approved_by_validation_run_id="validation-failure",
        cleaned_records=records,
    )
    session.commit()


@pytest.mark.integration
def test_historical_demand_no_data_persists_terminal_outcome(app_client, planner_headers, session):
    _seed_failure_records(session)
    response = app_client.post(
        "/api/v1/historical-demand/queries",
        headers=planner_headers,
        json={
            "serviceCategory": "Waste",
            "timeRangeStart": "2026-03-01T00:00:00Z",
            "timeRangeEnd": "2026-03-31T23:59:59Z",
        },
    )
    assert response.status_code == 200
    analysis_request_id = response.json()["analysisRequestId"]
    stored_request = session.get(HistoricalDemandAnalysisRequest, analysis_request_id)
    assert stored_request.status == "no_data"
    stored_outcome = session.query(HistoricalAnalysisOutcomeRecord).filter_by(analysis_request_id=analysis_request_id).one()
    assert stored_outcome.outcome_type == "no_data"


@pytest.mark.integration
def test_historical_demand_render_failure_updates_terminal_outcome(app_client, planner_headers, session):
    _seed_failure_records(session)
    created = app_client.post(
        "/api/v1/historical-demand/queries",
        headers=planner_headers,
        json={
            "serviceCategory": "Roads",
            "timeRangeStart": "2026-03-01T00:00:00Z",
            "timeRangeEnd": "2026-03-31T23:59:59Z",
        },
    )
    analysis_request_id = created.json()["analysisRequestId"]
    response = app_client.post(
        f"/api/v1/historical-demand/queries/{analysis_request_id}/render-events",
        headers=planner_headers,
        json={"renderStatus": "render_failed", "failureReason": "chart crashed"},
    )
    assert response.status_code == 202
    stored_request = session.get(HistoricalDemandAnalysisRequest, analysis_request_id)
    assert stored_request.status == "render_failed"
    stored_outcome = session.query(HistoricalAnalysisOutcomeRecord).filter_by(analysis_request_id=analysis_request_id).one()
    assert stored_outcome.outcome_type == "render_failed"
