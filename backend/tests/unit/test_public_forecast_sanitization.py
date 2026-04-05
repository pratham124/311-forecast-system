from __future__ import annotations

from datetime import datetime, timezone

from app.services.public_forecast_sanitization_service import PublicForecastSanitizationService
from app.services.public_forecast_source_service import PublicForecastBucketRow, ResolvedPublicForecastSource


def _source(rows: list[PublicForecastBucketRow]) -> ResolvedPublicForecastSource:
    return ResolvedPublicForecastSource(
        forecast_product="daily",
        approved_forecast_version_id="forecast-1",
        forecast_window_label="2026-03-20 to 2026-03-21",
        published_at=datetime(2026, 3, 20, tzinfo=timezone.utc),
        source_cleaned_dataset_version_id="dataset-1",
        category_rows=rows,
        source_category_count=len({row.service_category for row in rows}),
    )


def test_sanitize_passes_safe_rows_as_is():
    service = PublicForecastSanitizationService()
    result = service.sanitize(_source([PublicForecastBucketRow(service_category="Roads", forecast_demand_value=10)]))
    assert result.sanitization_status == "passed_as_is"
    assert result.removed_detail_count == 0
    assert len(result.category_rows) == 1


def test_sanitize_removes_restricted_rows():
    service = PublicForecastSanitizationService()
    result = service.sanitize(
        _source(
            [
                PublicForecastBucketRow(service_category="Roads", forecast_demand_value=10),
                PublicForecastBucketRow(service_category="Transit", forecast_demand_value=40, geography_key="Ward 1"),
            ]
        )
    )
    assert result.sanitization_status == "sanitized"
    assert result.removed_detail_count == 1
    assert result.removed_categories == ["Transit"]


def test_sanitize_blocks_when_no_safe_rows_remain():
    service = PublicForecastSanitizationService()
    result = service.sanitize(
        _source([PublicForecastBucketRow(service_category="Transit", forecast_demand_value=40, geography_key="Ward 1")])
    )
    assert result.sanitization_status == "blocked"
    assert result.failure_reason is not None
