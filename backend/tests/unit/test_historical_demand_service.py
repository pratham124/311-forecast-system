from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.schemas.historical_demand import HistoricalDemandQueryRequest
from app.services.historical_context_service import HistoricalContextService
from app.services.historical_demand_service import HistoricalDemandAnalysisService, HistoricalDemandService
from app.services.historical_warning_service import HistoricalWarningService


class StubCleanedDatasetRepository:
    def __init__(self, records, dataset_version_id: str = "dataset-1") -> None:
        self.records = records
        self.dataset_version_id = dataset_version_id

    def list_current_cleaned_records(self, source_name: str):
        return list(self.records)

    def get_current_approved_dataset(self, source_name: str):
        return type("DatasetVersion", (), {"dataset_version_id": self.dataset_version_id})()


class StubHistoricalDemandRepository:
    def __init__(self) -> None:
        self.requests = []
        self.results = []
        self.points = []
        self.outcomes = {}

    def create_request(self, **kwargs):
        record = type("Request", (), {"analysis_request_id": f"request-{len(self.requests) + 1}", **kwargs})()
        self.requests.append(record)
        return record

    def finalize_request(self, analysis_request_id: str, **kwargs):
        return analysis_request_id, kwargs

    def create_result(self, **kwargs):
        record = type("Result", (), {"analysis_result_id": f"result-{len(self.results) + 1}", **kwargs})()
        self.results.append(record)
        return record

    def replace_summary_points(self, analysis_result_id: str, points):
        self.points = list(points)

    def upsert_outcome(self, **kwargs):
        self.outcomes[kwargs["analysis_request_id"]] = kwargs

    def require_request(self, analysis_request_id: str):
        return type("Request", (), {"warning_status": "acknowledged"})()


@pytest.mark.unit
def test_parse_timestamp_handles_invalid_values():
    assert HistoricalDemandService._parse_timestamp("") is None
    assert HistoricalDemandService._parse_timestamp("bad-date") is None


@pytest.mark.unit
def test_context_service_exposes_only_reliable_geography_levels():
    records = [
        {"category": "Roads", "ward": "Ward 1"},
        {"category": "Waste", "ward": "Ward 2"},
    ]
    service = HistoricalContextService(StubCleanedDatasetRepository(records), "edmonton_311")
    context = service.get_context()
    assert context.service_categories == ["Roads", "Waste"]
    assert context.supported_geography_levels == ["ward"]


@pytest.mark.unit
def test_warning_service_detects_large_requests():
    warning = HistoricalWarningService(record_threshold=2).evaluate(
        candidate_record_count=3,
        time_range_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        time_range_end=datetime(2026, 3, 1, tzinfo=timezone.utc),
        service_category=None,
        geography_level=None,
        proceed_after_warning=False,
    )
    assert warning is not None
    assert warning.shown is True
    assert warning.acknowledged is False


@pytest.mark.unit
def test_analysis_service_aggregates_successful_summary():
    records = [
        {"requested_at": "2026-03-05T10:00:00Z", "category": "Roads", "ward": "Ward 1"},
        {"requested_at": "2026-03-06T10:00:00Z", "category": "Roads", "ward": "Ward 1"},
    ]
    cleaned_repository = StubCleanedDatasetRepository(records)
    repository = StubHistoricalDemandRepository()
    context_service = HistoricalContextService(cleaned_repository, "edmonton_311")
    service = HistoricalDemandAnalysisService(
        historical_demand_repository=repository,
        cleaned_dataset_repository=cleaned_repository,
        context_service=context_service,
        warning_service=HistoricalWarningService(record_threshold=100),
        source_name="edmonton_311",
    )
    response = service.execute_query(
        HistoricalDemandQueryRequest(
            serviceCategory="Roads",
            timeRangeStart=datetime(2026, 3, 1, tzinfo=timezone.utc),
            timeRangeEnd=datetime(2026, 3, 31, 23, 59, 59, tzinfo=timezone.utc),
            geographyLevel="ward",
            geographyValue="Ward 1",
        )
    )
    assert response.outcome_status == "success"
    assert len(response.summary_points) == 2
