from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

ForecastProduct = Literal["daily_1_day", "weekly_7_day"]
ForecastGranularity = Literal["hourly", "daily"]
ComparisonGranularity = Literal["hourly", "daily", "weekly"]
ComparisonOutcomeStatus = Literal[
    "warning_required",
    "success",
    "historical_only",
    "forecast_only",
    "partial_forecast_missing",
    "historical_retrieval_failed",
    "forecast_retrieval_failed",
    "alignment_failed",
]
RenderEventStatus = Literal["rendered", "render_failed"]
WarningStatus = Literal["not_needed", "shown", "acknowledged"]
ResultMode = Literal["chart", "table", "chart_and_table"]
SeriesType = Literal["historical", "forecast"]
MissingSource = Literal["forecast"]


@dataclass(frozen=True)
class ComparisonFilters:
    service_categories: list[str]
    geography_level: str | None
    geography_values: list[str]
    time_range_start: datetime
    time_range_end: datetime


@dataclass(frozen=True)
class ComparisonPoint:
    bucket_start: datetime
    bucket_end: datetime
    value: float


@dataclass(frozen=True)
class ComparisonSeries:
    series_type: SeriesType
    service_category: str
    geography_key: str | None
    points: list[ComparisonPoint]


@dataclass(frozen=True)
class MissingCombinationRecord:
    service_category: str
    geography_key: str | None
    missing_source: MissingSource
    message: str


@dataclass(frozen=True)
class ForecastSourceResolution:
    forecast_product: ForecastProduct
    forecast_granularity: ForecastGranularity
    comparison_granularity: ComparisonGranularity
    source_forecast_version_id: str | None
    source_weekly_forecast_version_id: str | None
    source_cleaned_dataset_version_id: str | None


@dataclass(frozen=True)
class ForecastLoadResult:
    rows: list[dict[str, object]]
    forecast_product: ForecastProduct | None
    forecast_granularity: ForecastGranularity | None
    comparison_granularity: ComparisonGranularity
    source_forecast_version_id: str | None
    source_weekly_forecast_version_id: str | None
