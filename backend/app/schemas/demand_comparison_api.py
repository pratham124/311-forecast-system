from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class DateConstraints(BaseModel):
    historical_min: datetime | None = Field(default=None, alias="historicalMin")
    historical_max: datetime | None = Field(default=None, alias="historicalMax")
    forecast_min: datetime | None = Field(default=None, alias="forecastMin")
    forecast_max: datetime | None = Field(default=None, alias="forecastMax")
    overlap_start: datetime | None = Field(default=None, alias="overlapStart")
    overlap_end: datetime | None = Field(default=None, alias="overlapEnd")

    model_config = ConfigDict(populate_by_name=True)


class DatePreset(BaseModel):
    label: str
    time_range_start: datetime = Field(alias="timeRangeStart")
    time_range_end: datetime = Field(alias="timeRangeEnd")

    model_config = ConfigDict(populate_by_name=True)


class CategoryGeographyAvailability(BaseModel):
    geography_levels: list[str] = Field(alias="geographyLevels")
    geography_options: dict[str, list[str]] = Field(default_factory=dict, alias="geographyOptions")

    model_config = ConfigDict(populate_by_name=True)


class DemandComparisonAvailability(BaseModel):
    service_categories: list[str] = Field(alias="serviceCategories")
    by_category_geography: dict[str, CategoryGeographyAvailability] = Field(default_factory=dict, alias="byCategoryGeography")
    date_constraints: DateConstraints = Field(alias="dateConstraints")
    presets: list[DatePreset] = Field(default_factory=list)
    forecast_product: str | None = Field(default=None, alias="forecastProduct")
    summary: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class DemandComparisonContext(BaseModel):
    service_categories: list[str] = Field(alias="serviceCategories")
    geography_levels: list[str] = Field(alias="geographyLevels")
    geography_options: dict[str, list[str]] = Field(default_factory=dict, alias="geographyOptions")
    summary: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class SelectedComparisonFilters(BaseModel):
    service_categories: list[str] = Field(alias="serviceCategories")
    geography_level: str | None = Field(default=None, alias="geographyLevel")
    geography_values: list[str] = Field(default_factory=list, alias="geographyValues")
    time_range_start: datetime = Field(alias="timeRangeStart")
    time_range_end: datetime = Field(alias="timeRangeEnd")

    model_config = ConfigDict(populate_by_name=True)


class DemandComparisonQueryRequest(BaseModel):
    service_categories: list[str] = Field(alias="serviceCategories", min_length=1)
    geography_level: str | None = Field(default=None, alias="geographyLevel")
    geography_values: list[str] = Field(default_factory=list, alias="geographyValues")
    time_range_start: datetime = Field(alias="timeRangeStart")
    time_range_end: datetime = Field(alias="timeRangeEnd")
    proceed_after_warning: bool = Field(default=False, alias="proceedAfterWarning")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("service_categories")
    @classmethod
    def normalize_categories(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value if item.strip()]
        if not normalized:
            raise ValueError("serviceCategories must contain at least one category")
        return normalized

    @field_validator("geography_values")
    @classmethod
    def normalize_geographies(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_request(self) -> "DemandComparisonQueryRequest":
        if self.time_range_start.tzinfo is None or self.time_range_end.tzinfo is None:
            raise ValueError("timeRangeStart and timeRangeEnd must be timezone-aware")
        if self.time_range_end < self.time_range_start:
            raise ValueError("timeRangeEnd must not be earlier than timeRangeStart")
        return self


class HighVolumeWarning(BaseModel):
    shown: bool
    acknowledged: bool
    message: str | None = None


class DemandComparisonPointRead(BaseModel):
    bucket_start: datetime = Field(alias="bucketStart")
    bucket_end: datetime = Field(alias="bucketEnd")
    value: int

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("value", mode="before")
    @classmethod
    def round_value(cls, value: float | int) -> int:
        return int(round(float(value)))


class DemandComparisonSeriesRead(BaseModel):
    series_type: Literal["historical", "forecast"] = Field(alias="seriesType")
    service_category: str = Field(alias="serviceCategory")
    geography_key: str | None = Field(default=None, alias="geographyKey")
    points: list[DemandComparisonPointRead]

    model_config = ConfigDict(populate_by_name=True)


class MissingCombinationRead(BaseModel):
    service_category: str = Field(alias="serviceCategory")
    geography_key: str | None = Field(default=None, alias="geographyKey")
    missing_source: Literal["forecast"] = Field(alias="missingSource")
    message: str

    model_config = ConfigDict(populate_by_name=True)


class DemandComparisonWarningResponse(BaseModel):
    comparison_request_id: str = Field(alias="comparisonRequestId")
    filters: SelectedComparisonFilters
    outcome_status: Literal["warning_required"] = Field(alias="outcomeStatus")
    warning: HighVolumeWarning
    message: str
    summary: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class DemandComparisonDataResponse(BaseModel):
    comparison_request_id: str = Field(alias="comparisonRequestId")
    filters: SelectedComparisonFilters
    outcome_status: Literal["success", "historical_only", "forecast_only", "partial_forecast_missing"] = Field(alias="outcomeStatus")
    result_mode: Literal["chart", "table", "chart_and_table"] = Field(alias="resultMode")
    comparison_granularity: Literal["hourly", "daily", "weekly"] = Field(alias="comparisonGranularity")
    forecast_product: Literal["daily_1_day", "weekly_7_day"] | None = Field(default=None, alias="forecastProduct")
    forecast_granularity: Literal["hourly", "daily"] | None = Field(default=None, alias="forecastGranularity")
    source_cleaned_dataset_version_id: str | None = Field(default=None, alias="sourceCleanedDatasetVersionId")
    source_forecast_version_id: str | None = Field(default=None, alias="sourceForecastVersionId")
    source_weekly_forecast_version_id: str | None = Field(default=None, alias="sourceWeeklyForecastVersionId")
    series: list[DemandComparisonSeriesRead]
    missing_combinations: list[MissingCombinationRead] = Field(default_factory=list, alias="missingCombinations")
    message: str
    summary: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class DemandComparisonFailureResponse(BaseModel):
    comparison_request_id: str = Field(alias="comparisonRequestId")
    filters: SelectedComparisonFilters
    outcome_status: Literal["historical_retrieval_failed", "forecast_retrieval_failed", "alignment_failed"] = Field(alias="outcomeStatus")
    message: str
    summary: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class DemandComparisonRenderEvent(BaseModel):
    render_status: Literal["rendered", "render_failed"] = Field(alias="renderStatus")
    failure_reason: str | None = Field(default=None, alias="failureReason")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_payload(self) -> "DemandComparisonRenderEvent":
        if self.render_status == "render_failed" and not self.failure_reason:
            raise ValueError("failureReason is required when renderStatus is render_failed")
        return self


class DemandComparisonRenderEventResponse(BaseModel):
    comparison_request_id: str = Field(alias="comparisonRequestId")
    recorded_outcome_status: Literal["rendered", "render_failed"] = Field(alias="recordedOutcomeStatus")
    message: str | None = None

    model_config = ConfigDict(populate_by_name=True)
