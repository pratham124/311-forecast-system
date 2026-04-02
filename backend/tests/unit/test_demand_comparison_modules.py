from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.demand_comparison_observability import (
    summarize_demand_comparison_event,
    summarize_demand_comparison_failure,
    summarize_demand_comparison_success,
    summarize_demand_comparison_warning,
)
from app.repositories.demand_lineage_repository import DemandLineageRepository
from app.schemas.demand_comparison_api import DemandComparisonQueryRequest, DemandComparisonRenderEvent
from app.services.demand_comparison_context_service import DemandComparisonContextService
from app.services.demand_comparison_outcomes import build_terminal_message, map_terminal_outcome
from app.services.demand_comparison_availability_service import DemandComparisonAvailabilityService
from app.services.demand_comparison_render_service import DemandComparisonRenderService
from app.services.demand_comparison_result_builder import DemandComparisonAlignmentError, DemandComparisonResultBuilder
from app.services.demand_comparison_service import DemandComparisonService
from app.services.demand_comparison_source_resolution import AlignmentResolutionError, DemandComparisonSourceResolver
from app.services.demand_comparison_warning_service import DemandComparisonWarningService


class StubCleanedRepository:
    def __init__(self, records=None, dataset=None) -> None:
        self.records = records or []
        self.dataset = dataset

    def list_current_cleaned_records(self, source_name, **_kwargs):
        assert source_name == "edmonton_311"
        return self.records

    def get_current_approved_dataset(self, source_name):
        assert source_name == "edmonton_311"
        return self.dataset


class StubForecastRepository:
    def __init__(self, marker=None) -> None:
        self.marker = marker

    def get_current_marker(self, forecast_product_name):
        return self.marker if forecast_product_name == "daily_1_day_demand" else None


class StubWeeklyForecastRepository:
    def __init__(self, marker=None) -> None:
        self.marker = marker

    def get_current_marker(self, forecast_product_name):
        return self.marker if forecast_product_name == "weekly_7_day_demand" else None


class StubComparisonRepository:
    def __init__(self, owner="owner-user") -> None:
        self.request = SimpleNamespace(
            comparison_request_id="comparison-1",
            requested_by_subject=owner,
            warning_status="acknowledged",
            status="success",
            failure_reason=None,
        )
        self.finalized = []
        self.outcomes = []

    def require_request(self, comparison_request_id: str):
        if comparison_request_id != "comparison-1":
            raise LookupError("missing")
        return self.request

    def finalize_request(self, comparison_request_id: str, **kwargs):
        self.finalized.append((comparison_request_id, kwargs))
        for key, value in kwargs.items():
            setattr(self.request, key, value)
        return self.request

    def upsert_outcome(self, **kwargs):
        self.outcomes.append(kwargs)


class StubContextService:
    source_name = "edmonton_311"

    def get_context(self):
        return SimpleNamespace(
            service_categories=["Roads"],
            geography_levels=["ward"],
            geography_options={"ward": ["Ward 1"]},
        )

    @staticmethod
    def extract_geography_value(record, geography_level):
        return record.get(geography_level)


class StubBucket:
    def __init__(self) -> None:
        self.bucket_start = datetime(2026, 3, 1, tzinfo=timezone.utc)
        self.bucket_end = datetime(2026, 3, 1, 1, tzinfo=timezone.utc)
        self.service_category = "Roads"
        self.geography_key = "Ward 1"
        self.point_forecast = 1.0


def test_context_service_collects_categories_and_geography_levels() -> None:
    service = DemandComparisonContextService(
        StubCleanedRepository(
            records=[
                {"category": "Roads", "ward": "Ward 1"},
                {"category": "Waste", "district": "North"},
                {"category": "Roads", "neighbourhood": "Oliver"},
            ]
        ),
        "edmonton_311",
    )

    context = service.get_context()

    assert context.service_categories == ["Roads", "Waste"]
    assert set(context.geography_levels) == {"district", "geography_key", "neighbourhood", "ward"}
    assert context.geography_options["ward"] == ["Ward 1"]
    assert DemandComparisonContextService.extract_geography_value({"neighborhood": "Downtown"}, "neighbourhood") == "Downtown"
    assert DemandComparisonContextService.extract_geography_value({"ward": "Ward 1"}, None) is None
    assert DemandComparisonContextService.extract_geography_value({}, "ward") is None


def test_warning_service_threshold_branches() -> None:
    service = DemandComparisonWarningService()

    assert service.evaluate(
        service_category_count=1,
        geography_count=0,
        time_range_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        time_range_end=datetime(2026, 3, 2, tzinfo=timezone.utc),
        proceed_after_warning=False,
    ) is None

    warning = service.evaluate(
        service_category_count=3,
        geography_count=4,
        time_range_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        time_range_end=datetime(2027, 2, 1, tzinfo=timezone.utc),
        proceed_after_warning=True,
    )

    assert warning is not None
    assert warning.shown is True
    assert warning.acknowledged is True
    assert "Retrieval has not started" in (warning.message or "")


def test_source_resolution_prefers_daily_then_weekly_and_alignment_guard() -> None:
    start = datetime(2026, 3, 1, tzinfo=timezone.utc)
    end = start + timedelta(hours=12)
    resolver = DemandComparisonSourceResolver(
        demand_lineage_repository=DemandLineageRepository(
            cleaned_dataset_repository=StubCleanedRepository(dataset=SimpleNamespace(dataset_version_id="dataset-1")),
            forecast_repository=StubForecastRepository(
                marker=SimpleNamespace(
                    forecast_version_id="forecast-1",
                    horizon_start=start - timedelta(hours=1),
                    horizon_end=end + timedelta(hours=1),
                )
            ),
            weekly_forecast_repository=StubWeeklyForecastRepository(
                marker=SimpleNamespace(
                    weekly_forecast_version_id="weekly-1",
                    week_start_local=start - timedelta(days=1),
                    week_end_local=end + timedelta(days=8),
                )
            ),
        ),
        source_name="edmonton_311",
        daily_forecast_product_name="daily_1_day_demand",
        weekly_forecast_product_name="weekly_7_day_demand",
    )

    dataset_id, daily = resolver.resolve(time_range_start=start, time_range_end=end, geography_level="ward")
    assert dataset_id == "dataset-1"
    assert daily is not None
    assert daily.forecast_product == "daily_1_day"
    assert daily.comparison_granularity == "hourly"

    resolver.ensure_alignment_supported(comparison_granularity="daily", geography_level=None, forecast_has_geography=False)
    with pytest.raises(AlignmentResolutionError):
        resolver.ensure_alignment_supported(comparison_granularity="daily", geography_level="ward", forecast_has_geography=False)

    weekly_only = DemandComparisonSourceResolver(
        demand_lineage_repository=DemandLineageRepository(
            cleaned_dataset_repository=StubCleanedRepository(dataset=SimpleNamespace(dataset_version_id="dataset-1")),
            forecast_repository=StubForecastRepository(marker=None),
            weekly_forecast_repository=StubWeeklyForecastRepository(
                marker=SimpleNamespace(
                    weekly_forecast_version_id="weekly-1",
                    week_start_local=start - timedelta(days=1),
                    week_end_local=end + timedelta(days=8),
                )
            ),
        ),
        source_name="edmonton_311",
        daily_forecast_product_name="daily_1_day_demand",
        weekly_forecast_product_name="weekly_7_day_demand",
    )
    _, weekly = weekly_only.resolve(time_range_start=start, time_range_end=end + timedelta(days=5), geography_level="ward")
    assert weekly is not None
    assert weekly.forecast_product == "weekly_7_day"
    assert weekly.comparison_granularity == "weekly"

    _, none_found = weekly_only.resolve(
        time_range_start=start + timedelta(days=20),
        time_range_end=end + timedelta(days=21),
        geography_level=None,
    )
    assert none_found is None


def test_result_builder_builds_series_missing_combinations_and_alignment_error() -> None:
    builder = DemandComparisonResultBuilder()
    historical_records = [
        {"requested_at": "2026-03-01T01:00:00Z", "category": "Roads", "ward": "Ward 1"},
        {"requested_at": "2026-03-01T03:00:00Z", "category": "Roads", "ward": "Ward 1"},
    ]
    forecast_records = [
        {
            "bucket_start": datetime(2026, 3, 1, 0, tzinfo=timezone.utc),
            "bucket_end": datetime(2026, 3, 1, 1, tzinfo=timezone.utc),
            "service_category": "Roads",
            "geography_key": "Ward 1",
            "point_forecast": 5.0,
        }
    ]

    series, missing, uncovered = builder.build(
        historical_records=historical_records,
        forecast_records=forecast_records,
        categories=["Roads", "Waste"],
        geography_level="ward",
        geography_values=["Ward 1"],
        comparison_granularity="daily",
    )
    assert len(series) == 2
    assert len(missing) == 1
    assert missing[0].service_category == "Waste"
    assert uncovered is not None
    flattened = builder.flatten_points(series)
    assert flattened[0]["series_type"] in {"historical", "forecast"}
    assert builder.flatten_missing_combinations(missing)[0]["missing_source"] == "forecast"

    weekly_rows = [
        {"forecast_date_local": date(2026, 3, 2), "service_category": "Roads", "geography_key": "Ward 1", "point_forecast": 3.0}
    ]
    weekly_series, _, _ = builder.build(
        historical_records=historical_records,
        forecast_records=weekly_rows,
        categories=["Roads"],
        geography_level="ward",
        geography_values=["Ward 1"],
        comparison_granularity="weekly",
    )
    assert weekly_series[0].points[0].bucket_end > weekly_series[0].points[0].bucket_start

    with pytest.raises(DemandComparisonAlignmentError):
        builder.build(
            historical_records=historical_records,
            forecast_records=[{"bucket_start": datetime(2026, 3, 1, tzinfo=timezone.utc), "service_category": "Roads", "point_forecast": 1.0}],
            categories=["Roads"],
            geography_level="ward",
            geography_values=["Ward 1"],
            comparison_granularity="daily",
        )


def test_outcomes_schemas_observability_and_render_service() -> None:
    assert map_terminal_outcome(has_historical_data=True, has_forecast_data=True, missing_combinations=[]) == "success"
    assert map_terminal_outcome(has_historical_data=True, has_forecast_data=True, missing_combinations=[SimpleNamespace()]) == "partial_forecast_missing"
    assert map_terminal_outcome(has_historical_data=False, has_forecast_data=True, missing_combinations=[]) == "forecast_only"
    assert map_terminal_outcome(has_historical_data=False, has_forecast_data=False, missing_combinations=[]) == "historical_only"
    assert "aligned successfully" in build_terminal_message("success")
    assert "missing forecast data" in build_terminal_message("partial_forecast_missing", missing_count=2)
    assert "Historical demand is unavailable" in build_terminal_message("forecast_only", uncovered_historical_interval="2026-03-01T00:00:00Z")
    assert "Forecast demand is unavailable" in build_terminal_message("historical_only")
    assert "could not be retrieved" in build_terminal_message("historical_retrieval_failed")
    assert "could not be retrieved" in build_terminal_message("forecast_retrieval_failed")
    assert "could not be aligned" in build_terminal_message("alignment_failed")
    assert "could not be completed" in build_terminal_message("unexpected")

    request = DemandComparisonQueryRequest.model_validate(
        {
            "serviceCategories": [" Roads "],
            "geographyLevel": "ward",
            "geographyValues": [" Ward 1 "],
            "timeRangeStart": "2026-03-01T00:00:00Z",
            "timeRangeEnd": "2026-03-02T00:00:00Z",
        }
    )
    assert request.service_categories == ["Roads"]
    assert request.geography_values == ["Ward 1"]
    with pytest.raises(ValueError):
        DemandComparisonQueryRequest.model_validate(
            {
                "serviceCategories": ["Roads"],
                "timeRangeStart": "2026-03-01T00:00:00",
                "timeRangeEnd": "2026-03-02T00:00:00Z",
            }
        )
    with pytest.raises(ValueError):
        DemandComparisonQueryRequest.model_validate(
            {
                "serviceCategories": ["   "],
                "timeRangeStart": "2026-03-01T00:00:00Z",
                "timeRangeEnd": "2026-03-02T00:00:00Z",
            }
        )
    with pytest.raises(ValueError):
        DemandComparisonQueryRequest.model_validate(
            {
                "serviceCategories": ["Roads"],
                "geographyValues": ["Ward 1"],
                "timeRangeStart": "2026-03-01T00:00:00Z",
                "timeRangeEnd": "2026-03-02T00:00:00Z",
            }
        )
    with pytest.raises(ValueError):
        DemandComparisonRenderEvent.model_validate({"renderStatus": "render_failed"})

    assert summarize_demand_comparison_event("event", token="secret-token")["token"] == "se***en"
    assert summarize_demand_comparison_success("event")["outcome"] == "success"
    assert summarize_demand_comparison_warning("event")["outcome"] == "warning"
    assert summarize_demand_comparison_failure("event")["outcome"] == "failure"

    repository = StubComparisonRepository()
    service = DemandComparisonRenderService(repository)
    response = service.record_event(
        comparison_request_id="comparison-1",
        payload=DemandComparisonRenderEvent.model_validate({"renderStatus": "rendered"}),
        claims={"sub": "owner-user", "roles": ["CityPlanner"]},
    )
    assert response.recorded_outcome_status == "rendered"
    failed_response = service.record_event(
        comparison_request_id="comparison-1",
        payload=DemandComparisonRenderEvent.model_validate({"renderStatus": "render_failed", "failureReason": "chart broke"}),
        claims={"sub": "owner-user", "roles": ["CityPlanner"]},
    )
    assert failed_response.recorded_outcome_status == "render_failed"
    with pytest.raises(HTTPException):
        service.record_event(
            comparison_request_id="comparison-1",
            payload=DemandComparisonRenderEvent.model_validate({"renderStatus": "rendered"}),
            claims={"sub": "other-user", "roles": ["CityPlanner"]},
        )


def test_result_builder_parsers_and_service_filter_guards() -> None:
    builder = DemandComparisonResultBuilder()
    assert builder._parse_historical_timestamp("") is None
    assert builder._parse_historical_timestamp("not-a-date") is None
    assert builder._parse_forecast_bucket("bad") is None
    series = builder._build_historical_series(
        [{"requested_at": "", "category": "Roads"}, {"requested_at": "bad", "category": "Roads"}],
        None,
        "daily",
    )
    assert series == []
    forecast_series = builder._build_forecast_series(
        [{"bucket_start": "invalid", "service_category": "Roads", "point_forecast": 1.0}],
        "daily",
    )
    assert forecast_series == []

    service = DemandComparisonService(
        comparison_repository=SimpleNamespace(),
        cleaned_dataset_repository=SimpleNamespace(
            list_current_cleaned_records=lambda *_args, **_kwargs: [
                {"category": "Roads", "ward": "Ward 2"},
                {"category": "Waste", "ward": "Ward 1"},
            ]
        ),
        forecast_repository=SimpleNamespace(list_buckets=lambda *_args, **_kwargs: [StubBucket()]),
        weekly_forecast_repository=SimpleNamespace(list_buckets=lambda *_args, **_kwargs: []),
        context_service=StubContextService(),
        warning_service=SimpleNamespace(),
        source_resolver=SimpleNamespace(),
        result_builder=builder,
    )
    with pytest.raises(LookupError):
        service._ensure_supported_filters(
            DemandComparisonQueryRequest.model_validate(
                {
                    "serviceCategories": ["Waste"],
                    "timeRangeStart": "2026-03-01T00:00:00Z",
                    "timeRangeEnd": "2026-03-02T00:00:00Z",
                }
            )
        )
    with pytest.raises(LookupError):
        service._ensure_supported_filters(
            DemandComparisonQueryRequest.model_validate(
                {
                    "serviceCategories": ["Roads"],
                    "geographyLevel": "district",
                    "timeRangeStart": "2026-03-01T00:00:00Z",
                    "timeRangeEnd": "2026-03-02T00:00:00Z",
                }
            )
        )
    with pytest.raises(LookupError):
        service._ensure_supported_filters(
            DemandComparisonQueryRequest.model_validate(
                {
                    "serviceCategories": ["Roads"],
                    "geographyLevel": "ward",
                    "geographyValues": ["Ward 2"],
                    "timeRangeStart": "2026-03-01T00:00:00Z",
                    "timeRangeEnd": "2026-03-02T00:00:00Z",
                }
            )
        )
    historical = service._load_historical_records(
        DemandComparisonQueryRequest.model_validate(
            {
                "serviceCategories": ["Roads"],
                "geographyLevel": "ward",
                "geographyValues": ["Ward 1"],
                "timeRangeStart": "2026-03-01T00:00:00Z",
                "timeRangeEnd": "2026-03-02T00:00:00Z",
            }
        )
    )
    assert historical == []
    forecast = service._load_forecast_records(
        DemandComparisonQueryRequest.model_validate(
            {
                "serviceCategories": ["Roads"],
                "geographyLevel": "ward",
                "geographyValues": ["Ward 1"],
                "timeRangeStart": "2026-03-01T00:00:00Z",
                "timeRangeEnd": "2026-03-02T00:00:00Z",
            }
        ),
        SimpleNamespace(forecast_product="daily_1_day", source_forecast_version_id="forecast-1"),
    )
    assert len(forecast) == 1


def test_availability_service_intersects_historical_and_forecast_options() -> None:
    cleaned_repository = StubCleanedRepository(
        records=[
            {"requested_at": "2026-03-01T00:15:00Z", "category": "Roads", "ward": "Ward 1"},
            {"requested_at": "2026-03-01T01:15:00Z", "category": "Roads", "ward": "Ward 2"},
            {"requested_at": "2026-03-01T02:15:00Z", "category": "Waste", "ward": "Ward 1"},
        ]
    )
    daily_marker = SimpleNamespace(
        forecast_version_id="forecast-1",
        horizon_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        horizon_end=datetime(2026, 3, 2, tzinfo=timezone.utc),
    )
    forecast_repository = SimpleNamespace(
        get_current_marker=lambda product: daily_marker if product == "daily_1_day_demand" else None,
        list_buckets=lambda _version_id: [
            SimpleNamespace(service_category="Roads", geography_key="Ward 1"),
            SimpleNamespace(service_category="Parks", geography_key="Ward 3"),
        ],
    )
    weekly_forecast_repository = SimpleNamespace(
        get_current_marker=lambda _product: None,
        list_buckets=lambda _version_id: [],
    )

    availability = DemandComparisonAvailabilityService(
        cleaned_dataset_repository=cleaned_repository,
        forecast_repository=forecast_repository,
        weekly_forecast_repository=weekly_forecast_repository,
        source_name="edmonton_311",
        daily_forecast_product_name="daily_1_day_demand",
        weekly_forecast_product_name="weekly_7_day_demand",
    ).get_availability()

    assert availability.service_categories == ["Roads"]
    assert availability.forecast_product == "daily_1_day"
    roads = availability.by_category_geography["Roads"]
    assert "ward" in roads.geography_levels
    assert roads.geography_options["ward"] == ["Ward 1"]
    assert availability.date_constraints.historical_min is not None
    assert availability.date_constraints.forecast_min is not None
    assert availability.date_constraints.overlap_start is not None


def test_availability_service_hides_geography_when_forecast_is_category_only() -> None:
    cleaned_repository = StubCleanedRepository(
        records=[
            {"requested_at": "2026-03-01T00:15:00Z", "category": "Roads", "ward": "Ward 1"},
            {"requested_at": "2026-03-01T01:15:00Z", "category": "Roads", "ward": "Ward 2"},
        ]
    )
    daily_marker = SimpleNamespace(
        forecast_version_id="forecast-1",
        horizon_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        horizon_end=datetime(2026, 3, 2, tzinfo=timezone.utc),
    )
    forecast_repository = SimpleNamespace(
        get_current_marker=lambda product: daily_marker if product == "daily_1_day_demand" else None,
        list_buckets=lambda _version_id: [
            SimpleNamespace(service_category="Roads", geography_key=None),
        ],
    )
    weekly_forecast_repository = SimpleNamespace(
        get_current_marker=lambda _product: None,
        list_buckets=lambda _version_id: [],
    )

    availability = DemandComparisonAvailabilityService(
        cleaned_dataset_repository=cleaned_repository,
        forecast_repository=forecast_repository,
        weekly_forecast_repository=weekly_forecast_repository,
        source_name="edmonton_311",
        daily_forecast_product_name="daily_1_day_demand",
        weekly_forecast_product_name="weekly_7_day_demand",
    ).get_availability()

    assert availability.service_categories == ["Roads"]
    roads = availability.by_category_geography["Roads"]
    assert roads.geography_levels == []
    assert roads.geography_options == {}
