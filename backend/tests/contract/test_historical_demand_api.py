from __future__ import annotations

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository

import pytest


def _seed_historical_dataset(session) -> str:
    records = [
        {"service_request_id": "roads-1", "requested_at": "2026-03-05T10:00:00Z", "category": "Roads", "ward": "Ward 1"},
        {"service_request_id": "roads-2", "requested_at": "2026-03-06T10:00:00Z", "category": "Roads", "ward": "Ward 1"},
        {"service_request_id": "waste-1", "requested_at": "2026-03-06T11:00:00Z", "category": "Waste", "ward": "Ward 2"},
        {"service_request_id": "waste-2", "requested_at": "2026-03-07T11:00:00Z", "category": "Waste", "ward": "Ward 2"},
    ]
    version = DatasetRepository(session).create_dataset_version(
        source_name="edmonton_311",
        run_id="run-hd",
        candidate_id=None,
        record_count=len(records),
        records=records,
        validation_status="approved",
        dataset_kind="cleaned",
        approved_by_validation_run_id="validation-hd",
    )
    DatasetRepository(session).activate_dataset("edmonton_311", version.dataset_version_id, "run-hd")
    CleanedDatasetRepository(session).upsert_current_cleaned_records(
        source_name="edmonton_311",
        ingestion_run_id="run-hd",
        source_dataset_version_id=version.dataset_version_id,
        approved_dataset_version_id=version.dataset_version_id,
        approved_by_validation_run_id="validation-hd",
        cleaned_records=records,
    )
    session.commit()
    return version.dataset_version_id


@pytest.mark.contract
def test_get_historical_demand_context(app_client, planner_headers, session):
    _seed_historical_dataset(session)
    response = app_client.get("/api/v1/historical-demand/context", headers=planner_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["serviceCategories"] == ["Roads", "Waste"]
    assert body["supportedGeographyLevels"] == ["ward"]


@pytest.mark.contract
def test_historical_demand_requires_auth(app_client):
    response = app_client.get("/api/v1/historical-demand/context")
    assert response.status_code == 401


@pytest.mark.contract
def test_create_historical_demand_query_success(app_client, planner_headers, session):
    _seed_historical_dataset(session)
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
    body = response.json()
    assert body["outcomeStatus"] == "success"
    assert body["aggregationGranularity"] == "daily"
    assert len(body["summaryPoints"]) == 2


@pytest.mark.contract
def test_create_historical_demand_query_warning_decline(app_client, planner_headers, session):
    _seed_historical_dataset(session)
    response = app_client.post(
        "/api/v1/historical-demand/queries",
        headers=planner_headers,
        json={
            "timeRangeStart": "2025-01-01T00:00:00Z",
            "timeRangeEnd": "2026-12-31T23:59:59Z",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["warning"]["shown"] is True
    assert body["warning"]["acknowledged"] is False


@pytest.mark.contract
def test_create_historical_demand_query_no_data(app_client, planner_headers, session):
    _seed_historical_dataset(session)
    response = app_client.post(
        "/api/v1/historical-demand/queries",
        headers=planner_headers,
        json={
            "serviceCategory": "Roads",
            "timeRangeStart": "2024-01-01T00:00:00Z",
            "timeRangeEnd": "2024-01-31T23:59:59Z",
        },
    )
    assert response.status_code == 200
    assert response.json()["outcomeStatus"] == "no_data"


@pytest.mark.contract
def test_record_historical_render_failure(app_client, planner_headers, session):
    _seed_historical_dataset(session)
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
        json={"renderStatus": "render_failed", "failureReason": "chart boom"},
    )
    assert response.status_code == 202
