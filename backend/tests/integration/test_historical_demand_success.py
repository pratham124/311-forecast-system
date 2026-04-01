from __future__ import annotations

from app.models import HistoricalAnalysisOutcomeRecord, HistoricalDemandAnalysisRequest, HistoricalDemandAnalysisResult, HistoricalDemandSummaryPoint
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository

import pytest


def _seed_success_records(session) -> None:
    # Include a second ward so supported_geography_levels() treats "ward" as reliable (needs ≥2 distinct values).
    records = [
        {"service_request_id": "roads-1", "requested_at": "2026-03-05T10:00:00Z", "category": "Roads", "ward": "Ward 1"},
        {"service_request_id": "roads-2", "requested_at": "2026-03-12T10:00:00Z", "category": "Roads", "ward": "Ward 1"},
        {"service_request_id": "roads-3", "requested_at": "2026-03-19T10:00:00Z", "category": "Roads", "ward": "Ward 1"},
        {"service_request_id": "roads-4", "requested_at": "2026-03-20T10:00:00Z", "category": "Roads", "ward": "Ward 2"},
    ]
    version = DatasetRepository(session).create_dataset_version(
        source_name="edmonton_311",
        run_id="run-success",
        candidate_id=None,
        record_count=len(records),
        records=records,
        validation_status="approved",
        dataset_kind="cleaned",
        approved_by_validation_run_id="validation-success",
    )
    DatasetRepository(session).activate_dataset("edmonton_311", version.dataset_version_id, "run-success")
    CleanedDatasetRepository(session).upsert_current_cleaned_records(
        source_name="edmonton_311",
        ingestion_run_id="run-success",
        source_dataset_version_id=version.dataset_version_id,
        approved_dataset_version_id=version.dataset_version_id,
        approved_by_validation_run_id="validation-success",
        cleaned_records=records,
    )
    session.commit()


@pytest.mark.integration
def test_historical_demand_success_persists_request_result_and_outcome(app_client, planner_headers, session):
    _seed_success_records(session)
    response = app_client.post(
        "/api/v1/historical-demand/queries",
        headers=planner_headers,
        json={
            "serviceCategory": "Roads",
            "timeRangeStart": "2026-03-01T00:00:00Z",
            "timeRangeEnd": "2026-03-31T23:59:59Z",
            "geographyLevel": "ward",
            "geographyValue": "Ward 1",
        },
    )
    assert response.status_code == 200
    analysis_request_id = response.json()["analysisRequestId"]

    stored_request = session.get(HistoricalDemandAnalysisRequest, analysis_request_id)
    assert stored_request is not None
    assert stored_request.status == "success"

    stored_result = session.query(HistoricalDemandAnalysisResult).filter_by(analysis_request_id=analysis_request_id).one()
    assert stored_result.record_count == 3
    assert session.query(HistoricalDemandSummaryPoint).filter_by(analysis_result_id=stored_result.analysis_result_id).count() == 3

    stored_outcome = session.query(HistoricalAnalysisOutcomeRecord).filter_by(analysis_request_id=analysis_request_id).one()
    assert stored_outcome.outcome_type == "success"
