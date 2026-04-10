from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.clients.actual_demand_client import ActualDemandClient, _parse_requested_at
from app.clients.forecast_history_client import ForecastHistoryClient, _day_bucket_start, _to_utc
from app.core.logging import (
    summarize_forecast_accuracy_event,
    summarize_forecast_accuracy_failure,
    summarize_forecast_accuracy_success,
)
from app.repositories.forecast_accuracy_repository import ForecastAccuracyRepository
from app.schemas.forecast_accuracy import ForecastAccuracyQuery, ForecastAccuracyRenderEvent
from app.services.forecast_accuracy_observability_service import ForecastAccuracyObservabilityService
from app.services.forecast_accuracy_query_service import ForecastAccuracyQueryService


class FakeCleanedDatasetRepository:
    def __init__(self, records: list[dict[str, object]] | None = None, dataset_version_id: str | None = "dataset-1") -> None:
        self.records = records or []
        self.dataset_version_id = dataset_version_id

    def list_current_cleaned_records(self, source_name: str, start_time, end_time):
        assert source_name == "edmonton_311"
        return self.records

    def get_current_approved_dataset(self, source_name: str):
        assert source_name == "edmonton_311"
        if self.dataset_version_id is None:
            return None
        return SimpleNamespace(dataset_version_id=self.dataset_version_id)


class FakeForecastRepository:
    def __init__(self, versions: list[object], buckets_by_version: dict[str, list[object]]) -> None:
        self.versions = versions
        self.buckets_by_version = buckets_by_version

    def list_stored_versions_overlapping_range(self, *, range_start, range_end):
        return self.versions

    def list_buckets(self, forecast_version_id: str):
        return self.buckets_by_version[forecast_version_id]


class EmptyAlignmentService:
    def align(self, *, forecast_rows, actual_rows):
        raise ValueError("No overlapping forecast and actual buckets are available for safe comparison")


class FakeMetricService:
    def __init__(self, status="computed_on_demand", metrics=None, evaluation_result_id=None, message=None) -> None:
        self.result = (status, metrics, evaluation_result_id, message)

    def resolve_metrics(self, **kwargs):
        return self.result


class FakeObservabilityService:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, object]]] = []

    def log_event(self, event: str, **fields) -> None:
        self.events.append((event, fields))


def _claims(subject: str = "planner-1", roles: list[str] | None = None) -> dict[str, object]:
    return {"sub": subject, "roles": roles or ["CityPlanner"]}


def test_actual_demand_client_aggregates_hourly_and_daily_and_filters_category() -> None:
    records = [
        {"requested_at": "2026-03-01T00:10:00Z", "category": "Roads"},
        {"requested_at": "2026-03-01T00:25:00Z", "category": "Roads"},
        {"requested_at": "2026-03-01T01:00:00Z", "category": "Waste"},
    ]
    client = ActualDemandClient(FakeCleanedDatasetRepository(records), "edmonton_311")

    hourly = client.list_actual_rows(
        time_range_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        time_range_end=datetime(2026, 3, 2, tzinfo=timezone.utc),
        service_category="Roads",
        comparison_granularity="hourly",
    )
    assert hourly == [
        {
            "bucket_start": datetime(2026, 3, 1, 0, 0, tzinfo=timezone.utc),
            "bucket_end": datetime(2026, 3, 1, 1, 0, tzinfo=timezone.utc),
            "service_category": "Roads",
            "actual_value": 2.0,
        }
    ]

    daily = client.list_actual_rows(
        time_range_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        time_range_end=datetime(2026, 3, 2, tzinfo=timezone.utc),
        service_category=None,
        comparison_granularity="daily",
    )
    assert len(daily) == 2
    assert any(row["actual_value"] == 2.0 for row in daily)


def test_parse_requested_at_and_forecast_history_helpers_cover_utc_paths() -> None:
    parsed = _parse_requested_at("2026-03-01T00:10:00Z")
    assert parsed == datetime(2026, 3, 1, 0, 10, tzinfo=timezone.utc)

    naive = datetime(2026, 3, 1, 0, 0)
    aware = datetime(2026, 3, 1, 0, 0, tzinfo=timezone.utc)
    assert _to_utc(naive).tzinfo == timezone.utc
    assert _to_utc(aware) == aware
    assert _day_bucket_start(datetime(2026, 3, 1, 13, 45, tzinfo=timezone.utc)) == datetime(2026, 3, 1, 0, 0, tzinfo=timezone.utc)


def test_forecast_history_client_filters_out_of_range_and_aggregates_duplicates() -> None:
    version = SimpleNamespace(forecast_version_id="version-1")
    buckets = [
        SimpleNamespace(
            bucket_start=datetime(2026, 3, 1, 0, 0),
            bucket_end=datetime(2026, 3, 1, 1, 0),
            service_category="Roads",
            point_forecast=4.0,
        ),
        SimpleNamespace(
            bucket_start=datetime(2026, 3, 1, 0, 30, tzinfo=timezone.utc),
            bucket_end=datetime(2026, 3, 1, 1, 30, tzinfo=timezone.utc),
            service_category="Roads",
            point_forecast=2.0,
        ),
        SimpleNamespace(
            bucket_start=datetime(2026, 3, 1, 0, 0, tzinfo=timezone.utc),
            bucket_end=datetime(2026, 3, 1, 1, 0, tzinfo=timezone.utc),
            service_category="Roads",
            point_forecast=8.0,
        ),
        SimpleNamespace(
            bucket_start=datetime(2026, 2, 25, 0, 0, tzinfo=timezone.utc),
            bucket_end=datetime(2026, 2, 25, 1, 0, tzinfo=timezone.utc),
            service_category="Roads",
            point_forecast=99.0,
        ),
        SimpleNamespace(
            bucket_start=datetime(2026, 3, 1, 2, 0, tzinfo=timezone.utc),
            bucket_end=datetime(2026, 3, 1, 3, 0, tzinfo=timezone.utc),
            service_category="Waste",
            point_forecast=7.0,
        ),
    ]
    client = ForecastHistoryClient(FakeForecastRepository([version], {"version-1": buckets}))

    hourly_rows, version_id = client.list_forecast_rows(
        time_range_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        time_range_end=datetime(2026, 3, 2, tzinfo=timezone.utc),
        service_category="Roads",
        comparison_granularity="hourly",
    )
    assert version_id == "version-1"
    assert len(hourly_rows) == 2
    assert sum(1 for row in hourly_rows if row["bucket_start"] == datetime(2026, 3, 1, 0, 0, tzinfo=timezone.utc)) == 1

    daily_rows, _ = client.list_forecast_rows(
        time_range_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        time_range_end=datetime(2026, 3, 2, tzinfo=timezone.utc),
        service_category="Roads",
        comparison_granularity="daily",
    )
    assert daily_rows == [
        {
            "bucket_start": datetime(2026, 3, 1, 0, 0, tzinfo=timezone.utc),
            "bucket_end": datetime(2026, 3, 2, 0, 0, tzinfo=timezone.utc),
            "service_category": "Roads",
            "forecast_value": 14.0,
        }
    ]


def test_forecast_accuracy_repository_update_and_lookup_paths(session) -> None:
    repository = ForecastAccuracyRepository(session)
    request = repository.create_request(
        requested_by_actor="city_planner",
        requested_by_subject="planner-1",
        source_cleaned_dataset_version_id=None,
        source_forecast_version_id=None,
        source_evaluation_result_id=None,
        forecast_product_name="daily_1_day",
        comparison_granularity="hourly",
        time_range_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        time_range_end=datetime(2026, 3, 2, tzinfo=timezone.utc),
        service_category="Roads",
        status="running",
        correlation_id="corr-1",
    )
    repository.finalize_request(
        request.forecast_accuracy_request_id,
        status="rendered_with_metrics",
        source_forecast_version_id="forecast-version-1",
        source_evaluation_result_id="evaluation-1",
        failure_reason="none",
        render_reported=True,
    )
    assert request.source_forecast_version_id == "forecast-version-1"
    assert request.source_evaluation_result_id == "evaluation-1"
    assert request.render_reported_at is not None

    created = repository.upsert_metric_resolution(
        forecast_accuracy_request_id=request.forecast_accuracy_request_id,
        resolution_status="computed_on_demand",
        metric_names=["mae"],
        metric_values={"mae": 1.0},
    )
    updated = repository.upsert_metric_resolution(
        forecast_accuracy_request_id=request.forecast_accuracy_request_id,
        resolution_status="retrieved_precomputed",
        metric_names=["mae", "rmse", "mape"],
        metric_values=None,
        status_message="updated",
    )
    assert created.forecast_accuracy_metric_resolution_id == updated.forecast_accuracy_metric_resolution_id
    assert updated.metric_values_json is None
    assert updated.status_message == "updated"

    result = repository.create_result(
        forecast_accuracy_request_id=request.forecast_accuracy_request_id,
        view_status="rendered_without_metrics",
        metric_resolution_status="unavailable",
        status_message="missing",
        aligned_bucket_count=1,
        excluded_bucket_count=2,
    )
    repository.replace_aligned_buckets(
        result.forecast_accuracy_result_id,
        [
            {
                "bucket_start": datetime(2026, 3, 1, 0, tzinfo=timezone.utc),
                "bucket_end": datetime(2026, 3, 1, 1, tzinfo=timezone.utc),
                "service_category": "Roads",
                "forecast_value": 4.0,
                "actual_value": 3.0,
                "absolute_error_value": 1.0,
                "percentage_error_value": 33.3,
            }
        ],
    )
    repository.create_render_event(
        forecast_accuracy_request_id=request.forecast_accuracy_request_id,
        forecast_accuracy_result_id=result.forecast_accuracy_result_id,
        render_outcome="rendered",
        failure_reason=None,
        reported_by_subject="planner-1",
    )

    assert repository.get_result_by_request(request.forecast_accuracy_request_id) is not None
    assert len(repository.list_aligned_buckets(result.forecast_accuracy_result_id)) == 1
    assert repository.get_metric_resolution(request.forecast_accuracy_request_id) is not None

    with pytest.raises(LookupError):
        repository.require_request("missing-request")


def test_forecast_accuracy_schema_and_logging_helpers_cover_wrappers() -> None:
    with pytest.raises(ValidationError):
        ForecastAccuracyQuery.model_validate({"timeRangeStart": "2026-03-01T00:00:00Z"})
    with pytest.raises(ValidationError):
        ForecastAccuracyQuery.model_validate(
            {
                "timeRangeStart": "2026-03-02T00:00:00Z",
                "timeRangeEnd": "2026-03-01T00:00:00Z",
            }
        )
    assert ForecastAccuracyRenderEvent.model_validate({"renderStatus": "rendered"}).render_status == "rendered"
    with pytest.raises(ValidationError):
        ForecastAccuracyRenderEvent.model_validate({"renderStatus": "render_failed"})

    assert summarize_forecast_accuracy_event("fa.started")["message"] == "fa.started"
    assert summarize_forecast_accuracy_success("fa.prepared")["outcome"] == "success"
    assert summarize_forecast_accuracy_failure("fa.failed")["outcome"] == "failure"


class FakeEvaluationRepository:
    def __init__(self, bundles=None, metric_values=None) -> None:
        self.bundles = bundles or []
        self.metric_values = metric_values or {}

    def list_result_bundles_for_product(self, _product: str, limit: int | None = None):
        return self.bundles[:limit]

    def list_metric_values(self, segment_id: str):
        return self.metric_values.get(segment_id, [])


def test_metric_service_covers_missing_segments_filtered_values_and_compute_failures() -> None:
    from app.services.forecast_accuracy_metric_service import ForecastAccuracyMetricService

    bundle_no_segment = SimpleNamespace(
        result=SimpleNamespace(
            evaluation_result_id="eval-1",
            evaluation_window_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
            evaluation_window_end=datetime(2026, 3, 2, tzinfo=timezone.utc),
        ),
        segments=[SimpleNamespace(evaluation_segment_id="seg-overall", segment_type="overall", segment_key="overall")],
    )
    bundle_incomplete_metrics = SimpleNamespace(
        result=SimpleNamespace(
            evaluation_result_id="eval-2",
            evaluation_window_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
            evaluation_window_end=datetime(2026, 3, 2, tzinfo=timezone.utc),
        ),
        segments=[SimpleNamespace(evaluation_segment_id="seg-roads", segment_type="service_category", segment_key="Roads")],
    )
    repository = FakeEvaluationRepository(
        bundles=[
            SimpleNamespace(
                result=SimpleNamespace(
                    evaluation_result_id="eval-0",
                    evaluation_window_start=datetime(2026, 2, 1, tzinfo=timezone.utc),
                    evaluation_window_end=datetime(2026, 2, 2, tzinfo=timezone.utc),
                ),
                segments=[SimpleNamespace(evaluation_segment_id="seg-mismatch", segment_type="overall", segment_key="overall")],
            ),
            bundle_no_segment,
            bundle_incomplete_metrics,
        ],
        metric_values={
            "seg-roads": [
                SimpleNamespace(metric_name="mae", metric_value=1.0, compared_method="other", is_excluded=False),
                SimpleNamespace(metric_name="rmse", metric_value=None, compared_method="forecast_engine", is_excluded=False),
                SimpleNamespace(metric_name="mape", metric_value=4.0, compared_method="forecast_engine", is_excluded=True),
            ]
        },
    )
    service = ForecastAccuracyMetricService(repository)

    assert service._find_precomputed_metrics(
        time_range_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        time_range_end=datetime(2026, 3, 2, tzinfo=timezone.utc),
        service_category="Roads",
    ) is None

    status, metrics, _, message = service.resolve_metrics(
        aligned_buckets=[],
        time_range_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        time_range_end=datetime(2026, 3, 2, tzinfo=timezone.utc),
        service_category="Roads",
    )
    assert status == "unavailable"
    assert metrics is None
    assert "No aligned buckets" in str(message)

    with pytest.raises(ValueError, match="at least two aligned buckets"):
        service._compute_on_demand([{"forecast_value": 1.0, "actual_value": 1.0}])


def test_observability_service_covers_missing_result_and_role_override(session) -> None:
    repository = ForecastAccuracyRepository(session)
    request = repository.create_request(
        requested_by_actor="city_planner",
        requested_by_subject="planner-1",
        source_cleaned_dataset_version_id=None,
        source_forecast_version_id=None,
        source_evaluation_result_id=None,
        forecast_product_name="daily_1_day",
        comparison_granularity="hourly",
        time_range_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        time_range_end=datetime(2026, 3, 2, tzinfo=timezone.utc),
        service_category=None,
        status="running",
        correlation_id=None,
    )
    service = ForecastAccuracyObservabilityService(repository)

    with pytest.raises(LookupError, match="Forecast accuracy result not found"):
        service.record_render_event(
            forecast_accuracy_request_id=request.forecast_accuracy_request_id,
            payload=ForecastAccuracyRenderEvent.model_validate({"renderStatus": "rendered"}),
            claims=_claims("planner-1"),
        )

    result = repository.create_result(
        forecast_accuracy_request_id=request.forecast_accuracy_request_id,
        view_status="rendered_with_metrics",
        metric_resolution_status="computed_on_demand",
        status_message=None,
        aligned_bucket_count=1,
        excluded_bucket_count=0,
    )
    response = service.record_render_event(
        forecast_accuracy_request_id=request.forecast_accuracy_request_id,
        payload=ForecastAccuracyRenderEvent.model_validate({"renderStatus": "rendered"}),
        claims={"sub": "other-user", "roles": ["OperationalManager"]},
    )
    assert response.recorded_outcome_status == "rendered"
    assert result.forecast_accuracy_result_id is not None

    with pytest.raises(HTTPException):
        service.record_render_event(
            forecast_accuracy_request_id=request.forecast_accuracy_request_id,
            payload=ForecastAccuracyRenderEvent.model_validate({"renderStatus": "rendered"}),
            claims={"sub": "other-user", "roles": ["Viewer"]},
        )


def test_query_service_covers_actual_missing_alignment_unavailable_and_default_window(session, monkeypatch) -> None:
    repository = ForecastAccuracyRepository(session)
    observability = FakeObservabilityService()

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 4, 10, 9, 30, tzinfo=tz)

    monkeypatch.setattr("app.services.forecast_accuracy_query_service.datetime", FixedDateTime)

    default_service = ForecastAccuracyQueryService(
        repository=repository,
        cleaned_dataset_repository=FakeCleanedDatasetRepository([], dataset_version_id=None),
        forecast_history_client=SimpleNamespace(list_forecast_rows=lambda **kwargs: ([], None)),
        actual_demand_client=SimpleNamespace(list_actual_rows=lambda **kwargs: []),
        metric_service=FakeMetricService(),
        alignment_service=EmptyAlignmentService(),
        observability_service=observability,
        source_name="edmonton_311",
    )
    start, end = default_service._resolve_time_range(ForecastAccuracyQuery.model_validate({}))
    assert end - start == timedelta(days=30)
    assert start.tzinfo == timezone.utc
    assert end.tzinfo == timezone.utc

    actual_missing_service = ForecastAccuracyQueryService(
        repository=repository,
        cleaned_dataset_repository=FakeCleanedDatasetRepository(),
        forecast_history_client=SimpleNamespace(
            list_forecast_rows=lambda **kwargs: (
                [{"bucket_start": start, "bucket_end": start + timedelta(hours=1), "service_category": "Roads", "forecast_value": 2.0}],
                "forecast-version-1",
            )
        ),
        actual_demand_client=SimpleNamespace(list_actual_rows=lambda **kwargs: []),
        metric_service=FakeMetricService(),
        alignment_service=EmptyAlignmentService(),
        observability_service=observability,
        source_name="edmonton_311",
    )
    actual_missing = actual_missing_service.get_view(ForecastAccuracyQuery.model_validate({"serviceCategory": "Roads"}), _claims())
    assert actual_missing.view_status == "unavailable"
    assert actual_missing.status_message == "Actual demand data is unavailable for the selected scope."

    alignment_unavailable_service = ForecastAccuracyQueryService(
        repository=repository,
        cleaned_dataset_repository=FakeCleanedDatasetRepository(),
        forecast_history_client=SimpleNamespace(
            list_forecast_rows=lambda **kwargs: (
                [{"bucket_start": start, "bucket_end": start + timedelta(hours=1), "service_category": "Roads", "forecast_value": 2.0}],
                "forecast-version-1",
            )
        ),
        actual_demand_client=SimpleNamespace(
            list_actual_rows=lambda **kwargs: [{"bucket_start": start, "bucket_end": start + timedelta(hours=1), "service_category": "Roads", "actual_value": 1.0}]
        ),
        metric_service=FakeMetricService(),
        alignment_service=EmptyAlignmentService(),
        observability_service=observability,
        source_name="edmonton_311",
    )
    alignment_unavailable = alignment_unavailable_service.get_view(
        ForecastAccuracyQuery.model_validate({"serviceCategory": "Roads"}),
        _claims(),
    )
    assert alignment_unavailable.view_status == "error"
    assert "No overlapping forecast and actual buckets" in str(alignment_unavailable.status_message)
