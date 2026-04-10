from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from app.models.ingestion_models import CleanedCurrentRecord, DatasetVersion
from app.models.forecast_models import ForecastBucket, ForecastVersion
from app.models.weekly_forecast_models import WeeklyForecastBucket, WeeklyForecastVersion
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.schemas.demand_comparison_api import DemandComparisonRenderEvent, DemandComparisonQueryRequest
from app.services.demand_comparison_service import DemandComparisonService
from sqlalchemy import select


def test_cleaned_dataset_repository_filtered_branches(session):
    repo = CleanedDatasetRepository(session)
    source_name = "test_source"
    
    # Missing all optional filters
    repo.list_current_cleaned_records_filtered(source_name)
    
    # Missing just geography and category
    repo.list_current_cleaned_records_filtered(
        source_name,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc) + timedelta(days=1),
    )
    
    # Missing just geography
    repo.list_current_cleaned_records_filtered(
        source_name,
        categories=["Roads"],
    )

    # Missing just category
    repo.list_current_cleaned_records_filtered(
        source_name,
        geography_keys=["Downtown"],
    )

    # Test the fallback and JSONDecodeError branch via MagicMock on scalars
    # Let's mock session.scalars to yield a row that throws JSONDecodeError
    mock_row = MagicMock()
    mock_row.record_payload = "invalid json"
    mock_row.service_request_id = "test_id"
    mock_row.requested_at = "test_time"
    mock_row.category = "Roads"
    mock_row.geography_key = "Downtown"
    
    mock_row2 = MagicMock()
    mock_row2.record_payload = "invalid json"
    mock_row2.service_request_id = "test_id2"
    mock_row2.requested_at = "test_time"
    mock_row2.category = "Roads"
    mock_row2.geography_key = None
    
    # If rows exist but json decode fails
    repo.session = MagicMock()
    repo.session.scalars.return_value = [mock_row, mock_row2]
    res = repo.list_current_cleaned_records_filtered(source_name)
    assert len(res) == 2
    assert res[0]["category"] == "Roads"
    assert res[0]["geography_key"] == "Downtown"
    assert "geography_key" not in res[1]

    # Test fallback path when rows is empty but current_dataset is None
    repo.session.scalars.return_value = []
    repo.get_current_approved_dataset = MagicMock(return_value=None)
    assert repo.list_current_cleaned_records_filtered(source_name) == []
    
    # Test fallback path when current_dataset exists
    mock_dataset = MagicMock()
    mock_dataset.dataset_version_id = "v1"
    repo.get_current_approved_dataset = MagicMock(return_value=mock_dataset)
    repo.list_dataset_records = MagicMock(return_value=[
        {"requested_at": "2026-04-10T10:00:00Z", "category": "Roads", "geography_key": "Downtown"},
        {"requested_at": "2026-04-12T10:00:00Z", "category": "Water", "geography_key": "West"}
    ])
    
    # No filters
    assert len(repo.list_current_cleaned_records_filtered(source_name)) == 2
    
    # Filters applied to the fallback dataset records
    res = repo.list_current_cleaned_records_filtered(
        source_name,
        start_time=datetime(2026, 4, 9, tzinfo=timezone.utc),
        end_time=datetime(2026, 4, 11, tzinfo=timezone.utc),
        categories=["Roads"],
        geography_keys=["Downtown"]
    )
    assert len(res) == 1


def test_forecast_repository_filtered_branches(session):
    repo = ForecastRepository(session)
    # version_ids is empty
    assert repo.list_buckets_filtered([]) == []
    
    # Provide various optional combo
    repo.list_buckets_filtered(
        version_ids=["v1"],
        service_categories=["Roads"],
        time_start=datetime.now(timezone.utc),
    )
    repo.list_buckets_filtered(
        version_ids=["v1"],
        time_end=datetime.now(timezone.utc),
        geography_keys=["Downtown"],
    )


def test_weekly_forecast_repository_filtered_branches(session):
    repo = WeeklyForecastRepository(session)
    assert repo.list_buckets_filtered([]) == []
    
    repo.list_buckets_filtered(
        version_ids=["v1"],
        service_categories=["Roads"],
        date_start=date(2026, 4, 1),
    )
    repo.list_buckets_filtered(
        version_ids=["v1"],
        date_end=date(2026, 4, 10),
        geography_keys=["Downtown"],
    )


def test_demand_comparison_api_render_event():
    # Should not raise ValueError when reason is supplied
    event = DemandComparisonRenderEvent(renderStatus="render_failed", failureReason="server exploded")
    assert event.render_status == "render_failed"


def test_demand_comparison_service_branches():
    mock_context = MagicMock()
    mock_context.source_name = "edmonton_311"
    
    service = DemandComparisonService(
        context_service=mock_context,
        cleaned_dataset_repository=MagicMock(),
        forecast_repository=MagicMock(),
        weekly_forecast_repository=MagicMock(),
        comparison_repository=MagicMock(),
        warning_service=MagicMock(),
        source_resolver=MagicMock(),
        result_builder=MagicMock(),
    )
    
    # Mock repositories
    service.forecast_repository.list_stored_versions_overlapping_range.return_value = [ForecastVersion(forecast_version_id="fd1")]
    
    # We will yield buckets to hit the `daily_comparison_granularity == "daily"`
    # So we need duration > 2 days
    req = DemandComparisonQueryRequest(
        serviceCategories=["Roads"],
        timeRangeStart=datetime(2026, 4, 1, tzinfo=timezone.utc),
        timeRangeEnd=datetime(2026, 4, 5, tzinfo=timezone.utc), # > 2 days -> "daily" comparison granularity
    )
    
    # Time aware vs non-aware bucket test (branch coverage for normalize_dt)
    fb1 = ForecastBucket(
        forecast_version_id="fd1",
        service_category="Roads",
        geography_key="Downtown",
        bucket_start=datetime(2026, 4, 2), # naive
        point_forecast="5.0"
    )
    fb_agg = ForecastBucket(
        forecast_version_id="fd1",
        service_category="Roads",
        geography_key="Downtown",
        bucket_start=datetime(2026, 4, 2, tzinfo=timezone.utc), # aware, will merge into previous daily key
        point_forecast="2.0"
    )
    
    service.forecast_repository.list_buckets_filtered.return_value = [fb1, fb_agg]
    
    # Weekly versions
    service.weekly_forecast_repository.list_stored_versions_overlapping_range.return_value = [WeeklyForecastVersion(weekly_forecast_version_id="fw1")]
    
    # Daily key already covered
    wb1 = WeeklyForecastBucket(
        weekly_forecast_version_id="fw1",
        service_category="Roads",
        geography_key="Downtown",
        forecast_date_local=date(2026, 4, 2), 
        point_forecast="10.0"
    )
    
    # Out of range test
    wb2 = WeeklyForecastBucket(
        weekly_forecast_version_id="fw1",
        service_category="Roads",
        geography_key="Downtown",
        forecast_date_local=date(2026, 3, 1), 
        point_forecast="0.0"
    )
    
    # Null geography test (using same category so it's not daily_days_covered)
    # To hit line 283, we need geographyLevel set on the payload, so let's set it.
    req.geography_level = "geography_key"
    
    wb3 = WeeklyForecastBucket(
        weekly_forecast_version_id="fw1",
        service_category="Roads",
        geography_key=None,
        forecast_date_local=date(2026, 4, 3), 
        point_forecast="15.0"
    )
    
    service.weekly_forecast_repository.list_buckets_filtered.return_value = [wb1, wb2, wb3]
    
    # Run
    res = service._load_forecast_records(req)
    
    # Validate
    assert res.comparison_granularity == "daily"
    assert res.forecast_product is None # both used
    
    # Let's test only daily
    service.weekly_forecast_repository.list_stored_versions_overlapping_range.return_value = []
    res = service._load_forecast_records(req)
    assert res.forecast_product == "daily_1_day"
    assert res.forecast_granularity == "hourly"
    
    # Let's test only weekly
    service.forecast_repository.list_stored_versions_overlapping_range.return_value = []
    service.weekly_forecast_repository.list_stored_versions_overlapping_range.return_value = [WeeklyForecastVersion(weekly_forecast_version_id="fw1")]
    res = service._load_forecast_records(req)
    assert res.forecast_product == "weekly_7_day"
    assert res.forecast_granularity == "daily"
                 
    # Let's test none
    service.forecast_repository.list_stored_versions_overlapping_range.return_value = []
    service.weekly_forecast_repository.list_stored_versions_overlapping_range.return_value = []
    res = service._load_forecast_records(req)
    assert res.forecast_product is None

