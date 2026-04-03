from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import logging

import pytest

from app.schemas.historical_demand import HistoricalDemandQueryRequest, HistoricalDemandRenderEvent
from app.services.historical_context_service import HistoricalContextService
from app.services.historical_demand_service import HistoricalDemandAnalysisService, HistoricalDemandService
from app.services.historical_warning_service import HistoricalWarningService


class StubCleanedDatasetRepository:
    def __init__(self, records, dataset_version_id: str | None = "dataset-1") -> None:
        self.records = records
        self.dataset_version_id = dataset_version_id

    def list_current_categories(self, source_name: str):
        return sorted(
            {
                str(record.get("category")).strip()
                for record in self.records
                if isinstance(record.get("category"), str) and str(record.get("category")).strip()
            }
        )

    def list_current_cleaned_records(self, source_name: str, *, start_time=None, end_time=None):
        return list(self.records)

    def get_current_approved_dataset(self, source_name: str):
        if self.dataset_version_id is None:
            return None
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


class StubHistoricalDemandRepositoryCreateResultFails(StubHistoricalDemandRepository):
    def create_result(self, **kwargs):
        raise RuntimeError("simulated persistence failure")


class StubHistoricalDemandRepositoryNotAcknowledged(StubHistoricalDemandRepository):
    def require_request(self, analysis_request_id: str):
        return type("Request", (), {"warning_status": "not_needed"})()


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
    assert context.supported_geography_levels == []


@pytest.mark.unit
def test_context_service_rejects_geography_level_with_insufficient_distinct_values():
    records = [{"category": "Roads", "ward": "W1"} for _ in range(10)]
    service = HistoricalContextService(StubCleanedDatasetRepository(records), "edmonton_311")
    assert service.supported_geography_levels(records) == []


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
def test_parse_timestamp_accepts_z_suffix_and_naive_input():
    ts = HistoricalDemandService._parse_timestamp("2026-03-05T10:00:00Z")
    assert ts is not None
    assert ts.tzinfo == timezone.utc
    naive = HistoricalDemandService._parse_timestamp("2026-03-05T10:00:00")
    assert naive is not None
    assert naive.tzinfo == timezone.utc


@pytest.mark.unit
def test_build_series_naive_boundary_and_hourly_buckets():
    records = [
        {"requested_at": "2026-03-05T11:30:00Z", "category": "Roads"},
    ]
    stub = StubCleanedDatasetRepository(records)
    svc = HistoricalDemandService(stub, "edmonton_311")
    boundary = datetime(2026, 3, 6, 12, 0, 0)
    series, vid, start, end = svc.build_series(boundary=boundary, granularity="hourly")
    assert len(series) == 1
    assert series[0].timestamp.hour == 11
    assert vid == "dataset-1"


@pytest.mark.unit
def test_build_series_filters_categories_and_excludes():
    records = [
        {"requested_at": "2026-03-05T10:00:00Z", "category": "Roads"},
        {"requested_at": "2026-03-05T11:00:00Z", "category": "Waste"},
    ]
    stub = StubCleanedDatasetRepository(records)
    svc = HistoricalDemandService(stub, "edmonton_311")
    boundary = datetime(2026, 3, 6, tzinfo=timezone.utc)
    series, _, _, _ = svc.build_series(
        boundary=boundary,
        granularity="daily",
        service_categories=["Roads", "Waste"],
        excluded_service_categories=["Waste"],
    )
    assert len(series) == 1


@pytest.mark.unit
def test_build_series_skips_categories_not_in_selected_list():
    records = [
        {"requested_at": "2026-03-05T10:00:00Z", "category": "Roads"},
        {"requested_at": "2026-03-05T11:00:00Z", "category": "Parks"},
    ]
    stub = StubCleanedDatasetRepository(records)
    svc = HistoricalDemandService(stub, "edmonton_311")
    boundary = datetime(2026, 3, 6, tzinfo=timezone.utc)
    series, _, _, _ = svc.build_series(
        boundary=boundary,
        granularity="daily",
        service_categories=["Roads"],
    )
    assert len(series) == 1


@pytest.mark.unit
def test_build_series_excludes_when_only_excluded_categories_present():
    records = [
        {"requested_at": "2026-03-05T10:00:00Z", "category": "Waste"},
    ]
    stub = StubCleanedDatasetRepository(records)
    svc = HistoricalDemandService(stub, "edmonton_311")
    boundary = datetime(2026, 3, 6, tzinfo=timezone.utc)
    series, _, _, _ = svc.build_series(
        boundary=boundary,
        granularity="daily",
        excluded_service_categories=["Waste"],
    )
    assert series == []


@pytest.mark.unit
def test_build_series_skips_invalid_timestamps_and_nil_dataset():
    records = [
        {"requested_at": "not-a-date", "category": "Roads"},
        {"requested_at": "2026-03-05T10:00:00Z", "category": "Roads"},
    ]
    stub = StubCleanedDatasetRepository(records, dataset_version_id=None)
    svc = HistoricalDemandService(stub, "edmonton_311")
    boundary = datetime(2026, 3, 6, tzinfo=timezone.utc)
    series, vid, _, _ = svc.build_series(boundary=boundary, granularity="daily", service_category="Roads")
    assert len(series) == 1
    assert vid is None


@pytest.mark.unit
def test_context_service_summary_when_no_dataset():
    service = HistoricalContextService(StubCleanedDatasetRepository([], dataset_version_id=None), "edmonton_311")
    ctx = service.get_context()
    assert "none" in (ctx.summary or "").lower()
    assert ctx.service_categories == []
    assert ctx.supported_geography_levels == []


@pytest.mark.unit
def test_context_service_require_approved_dataset_raises():
    service = HistoricalContextService(StubCleanedDatasetRepository([], dataset_version_id=None), "edmonton_311")
    with pytest.raises(LookupError, match="No approved"):
        service.require_approved_dataset_id()


@pytest.mark.unit
def test_context_service_normalize_record_payload_json():
    service = HistoricalContextService(StubCleanedDatasetRepository([]), "edmonton_311")
    merged = service.normalize_record(
        {
            "record_payload": json.dumps({"category": "Roads", "ward": "W1"}),
            "geography_key": "gk-1",
        }
    )
    assert merged["category"] == "Roads"
    assert merged["ward"] == "W1"
    assert merged.get("geography_key") == "gk-1"


@pytest.mark.unit
def test_context_service_normalize_record_invalid_json_returns_original():
    service = HistoricalContextService(StubCleanedDatasetRepository([]), "edmonton_311")
    raw = {"record_payload": "{not json", "ward": "W1"}
    assert service.normalize_record(raw) is raw


@pytest.mark.unit
def test_context_service_normalize_record_non_dict_json_returns_original():
    service = HistoricalContextService(StubCleanedDatasetRepository([]), "edmonton_311")
    raw = {"record_payload": "[1,2,3]"}
    assert service.normalize_record(raw) is raw


@pytest.mark.unit
def test_analysis_service_post_init_default_logger():
    cleaned = StubCleanedDatasetRepository([])
    svc = HistoricalDemandAnalysisService(
        historical_demand_repository=StubHistoricalDemandRepository(),
        cleaned_dataset_repository=cleaned,
        context_service=HistoricalContextService(cleaned, "edmonton_311"),
        warning_service=HistoricalWarningService(record_threshold=100),
        source_name="edmonton_311",
        logger=None,
    )
    assert isinstance(svc.logger, logging.Logger)


@pytest.mark.unit
def test_analysis_service_retrieval_failure_without_prior_request():
    cleaned = StubCleanedDatasetRepository([], dataset_version_id=None)
    context = HistoricalContextService(cleaned, "edmonton_311")
    svc = HistoricalDemandAnalysisService(
        historical_demand_repository=StubHistoricalDemandRepository(),
        cleaned_dataset_repository=cleaned,
        context_service=context,
        warning_service=HistoricalWarningService(record_threshold=100),
        source_name="edmonton_311",
    )
    resp = svc.execute_query(
        HistoricalDemandQueryRequest(
            timeRangeStart=datetime(2026, 3, 1, tzinfo=timezone.utc),
            timeRangeEnd=datetime(2026, 3, 31, tzinfo=timezone.utc),
        )
    )
    assert resp.outcome_status == "retrieval_failed"
    assert resp.analysis_request_id


@pytest.mark.unit
def test_analysis_service_retrieval_failure_after_request_created():
    records = [
        {"requested_at": "2026-03-05T10:00:00Z", "category": "Roads", "ward": "W1"},
        {"requested_at": "2026-03-06T10:00:00Z", "category": "Roads", "ward": "W2"},
    ]
    cleaned = StubCleanedDatasetRepository(records)
    context = HistoricalContextService(cleaned, "edmonton_311")
    svc = HistoricalDemandAnalysisService(
        historical_demand_repository=StubHistoricalDemandRepositoryCreateResultFails(),
        cleaned_dataset_repository=cleaned,
        context_service=context,
        warning_service=HistoricalWarningService(record_threshold=100),
        source_name="edmonton_311",
    )
    resp = svc.execute_query(
        HistoricalDemandQueryRequest(
            timeRangeStart=datetime(2026, 3, 1, tzinfo=timezone.utc),
            timeRangeEnd=datetime(2026, 3, 31, tzinfo=timezone.utc),
            geographyLevel="ward",
            geographyValue="W1",
        )
    )
    assert resp.outcome_status == "retrieval_failed"


@pytest.mark.unit
def test_analysis_service_record_render_success_path():
    repo = StubHistoricalDemandRepositoryNotAcknowledged()
    cleaned = StubCleanedDatasetRepository([])
    context = HistoricalContextService(cleaned, "edmonton_311")
    svc = HistoricalDemandAnalysisService(
        historical_demand_repository=repo,
        cleaned_dataset_repository=cleaned,
        context_service=context,
        warning_service=HistoricalWarningService(),
        source_name="edmonton_311",
    )
    svc.record_render_event("request-1", HistoricalDemandRenderEvent(render_status="rendered"))
    assert repo.outcomes["request-1"]["outcome_type"] == "success"


@pytest.mark.unit
def test_analysis_service_record_render_failed_default_message():
    repo = StubHistoricalDemandRepositoryNotAcknowledged()
    cleaned = StubCleanedDatasetRepository([])
    context = HistoricalContextService(cleaned, "edmonton_311")
    svc = HistoricalDemandAnalysisService(
        historical_demand_repository=repo,
        cleaned_dataset_repository=cleaned,
        context_service=context,
        warning_service=HistoricalWarningService(),
        source_name="edmonton_311",
    )
    payload = HistoricalDemandRenderEvent.model_construct(render_status="render_failed", failure_reason=None)
    svc.record_render_event("request-1", payload)
    assert repo.outcomes["request-1"]["message"] == "Historical demand rendering failed."


@pytest.mark.unit
def test_analysis_service_unsupported_geography_raises():
    records = [{"category": "Roads", "ward": "W1"}, {"category": "Roads", "ward": "W2"}]
    cleaned = StubCleanedDatasetRepository(records)
    context = HistoricalContextService(cleaned, "edmonton_311")
    svc = HistoricalDemandAnalysisService(
        historical_demand_repository=StubHistoricalDemandRepository(),
        cleaned_dataset_repository=cleaned,
        context_service=context,
        warning_service=HistoricalWarningService(record_threshold=100),
        source_name="edmonton_311",
    )
    with pytest.raises(LookupError, match="not supported"):
        svc.execute_query(
            HistoricalDemandQueryRequest(
                timeRangeStart=datetime(2026, 3, 1, tzinfo=timezone.utc),
                timeRangeEnd=datetime(2026, 3, 31, tzinfo=timezone.utc),
                geographyLevel="neighbourhood",
                geographyValue="X",
            )
        )


@pytest.mark.unit
def test_filter_records_category_and_geography_and_time_bounds():
    records = [
        {"requested_at": "bad", "category": "Roads", "ward": "W1"},
        {"requested_at": "2026-03-04T10:00:00Z", "category": "Roads", "ward": "W1"},
        {"requested_at": "2026-03-10T12:00:00Z", "category": "Roads", "ward": "W1"},
        {"requested_at": "2026-03-10T13:00:00Z", "category": "Waste", "ward": "W1"},
        {"requested_at": "2026-03-10T14:00:00Z", "category": "Roads", "ward": "W2"},
        {"requested_at": "2026-03-30T10:00:00Z", "category": "Roads", "ward": "W1"},
    ]
    cleaned = StubCleanedDatasetRepository(records)
    context = HistoricalContextService(cleaned, "edmonton_311")
    svc = HistoricalDemandAnalysisService(
        historical_demand_repository=StubHistoricalDemandRepository(),
        cleaned_dataset_repository=cleaned,
        context_service=context,
        warning_service=HistoricalWarningService(record_threshold=100),
        source_name="edmonton_311",
    )
    payload = HistoricalDemandQueryRequest(
        serviceCategory="Roads",
        timeRangeStart=datetime(2026, 3, 5, tzinfo=timezone.utc),
        timeRangeEnd=datetime(2026, 3, 25, tzinfo=timezone.utc),
        geographyLevel="ward",
        geographyValue="W1",
    )
    filtered = svc._filter_records(records, payload)
    assert len(filtered) == 1
    assert filtered[0]["ward"] == "W1"


@pytest.mark.unit
def test_select_granularity_and_bucket_boundaries():
    cleaned = StubCleanedDatasetRepository([])
    context = HistoricalContextService(cleaned, "edmonton_311")
    svc = HistoricalDemandAnalysisService(
        historical_demand_repository=StubHistoricalDemandRepository(),
        cleaned_dataset_repository=cleaned,
        context_service=context,
        warning_service=HistoricalWarningService(),
        source_name="edmonton_311",
    )
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert svc._select_granularity(start, start) == "daily"
    assert svc._select_granularity(start, start + timedelta(days=32)) == "weekly"
    assert svc._select_granularity(start, start + timedelta(days=200)) == "monthly"
    ts = datetime(2026, 3, 15, 14, 30, tzinfo=timezone.utc)
    assert svc._bucket_start(ts, "daily").hour == 0
    mon = datetime(2026, 6, 10, tzinfo=timezone.utc)
    bs = svc._bucket_start(mon, "monthly")
    assert bs.day == 1 and bs.month == 6
    wk = svc._bucket_start(mon, "weekly")
    assert wk.weekday() == 0
    dec = datetime(2026, 12, 15, tzinfo=timezone.utc)
    dbs = svc._bucket_start(dec, "monthly")
    end_dec = svc._bucket_end(dbs, "monthly")
    assert end_dec.month == 1 and end_dec.year == 2027
    nov = datetime(2026, 11, 10, tzinfo=timezone.utc)
    nbs = svc._bucket_start(nov, "monthly")
    end_nov = svc._bucket_end(nbs, "monthly")
    assert end_nov.month == 12
    wbs = svc._bucket_start(datetime(2026, 3, 4, tzinfo=timezone.utc), "weekly")
    assert svc._bucket_end(wbs, "weekly") == wbs + timedelta(days=7)
    dbs2 = svc._bucket_start(ts, "daily")
    assert svc._bucket_end(dbs2, "daily") == dbs2 + timedelta(days=1)


@pytest.mark.unit
def test_aggregate_unknown_category_and_no_geography_level():
    records = [
        {"requested_at": "2026-03-10T10:00:00Z"},
    ]
    cleaned = StubCleanedDatasetRepository(records)
    context = HistoricalContextService(cleaned, "edmonton_311")
    svc = HistoricalDemandAnalysisService(
        historical_demand_repository=StubHistoricalDemandRepository(),
        cleaned_dataset_repository=cleaned,
        context_service=context,
        warning_service=HistoricalWarningService(),
        source_name="edmonton_311",
    )
    points = svc._aggregate(records, "daily", None)
    assert len(points) == 1
    assert points[0]["service_category"] == "Unknown"
    assert points[0]["geography_key"] is None


@pytest.mark.unit
def test_aggregate_skips_unparseable_timestamps():
    records = [
        {"requested_at": "not-a-ts", "category": "Roads"},
        {"requested_at": "2026-03-10T10:00:00Z", "category": "Roads"},
    ]
    cleaned = StubCleanedDatasetRepository(records)
    context = HistoricalContextService(cleaned, "edmonton_311")
    svc = HistoricalDemandAnalysisService(
        historical_demand_repository=StubHistoricalDemandRepository(),
        cleaned_dataset_repository=cleaned,
        context_service=context,
        warning_service=HistoricalWarningService(),
        source_name="edmonton_311",
    )
    points = svc._aggregate(records, "daily", None)
    assert len(points) == 1


@pytest.mark.unit
def test_analysis_service_aggregates_successful_summary():
    records = [
        {"requested_at": "2026-03-05T10:00:00Z", "category": "Roads", "ward": "Ward 1"},
        {"requested_at": "2026-03-06T10:00:00Z", "category": "Roads", "ward": "Ward 1"},
        {"requested_at": "2026-03-07T10:00:00Z", "category": "Roads", "ward": "Ward 2"},
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
