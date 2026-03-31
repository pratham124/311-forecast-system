from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

HistoricalOutcomeStatus = Literal["success", "no_data", "retrieval_failed", "render_failed"]
HistoricalAggregationGranularity = Literal["daily", "weekly", "monthly"]
HistoricalResultMode = Literal["chart", "table", "chart_and_table"]
HistoricalRenderStatus = Literal["rendered", "render_failed"]


class HistoricalDemandContextRead(BaseModel):
    service_categories: list[str] = Field(alias="serviceCategories")
    supported_geography_levels: list[str] = Field(alias="supportedGeographyLevels")
    summary: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class SelectedFiltersRead(BaseModel):
    service_category: str | None = Field(default=None, alias="serviceCategory")
    time_range_start: datetime = Field(alias="timeRangeStart")
    time_range_end: datetime = Field(alias="timeRangeEnd")
    geography_level: str | None = Field(default=None, alias="geographyLevel")
    geography_value: str | None = Field(default=None, alias="geographyValue")

    model_config = ConfigDict(populate_by_name=True)


class HistoricalDemandQueryRequest(BaseModel):
    service_category: str | None = Field(default=None, alias="serviceCategory")
    time_range_start: datetime = Field(alias="timeRangeStart")
    time_range_end: datetime = Field(alias="timeRangeEnd")
    geography_level: str | None = Field(default=None, alias="geographyLevel")
    geography_value: str | None = Field(default=None, alias="geographyValue")
    proceed_after_warning: bool = Field(default=False, alias="proceedAfterWarning")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_filters(self) -> "HistoricalDemandQueryRequest":
        if self.time_range_end < self.time_range_start:
            raise ValueError("timeRangeEnd must not be earlier than timeRangeStart")
        if self.geography_value and not self.geography_level:
            raise ValueError("geographyLevel is required when geographyValue is provided")
        return self


class HighVolumeWarningRead(BaseModel):
    shown: bool
    acknowledged: bool
    message: str | None = None


class HistoricalDemandSummaryPointRead(BaseModel):
    bucket_start: datetime = Field(alias="bucketStart")
    bucket_end: datetime = Field(alias="bucketEnd")
    service_category: str = Field(alias="serviceCategory")
    geography_key: str | None = Field(default=None, alias="geographyKey")
    demand_count: int = Field(alias="demandCount")

    model_config = ConfigDict(populate_by_name=True)


class HistoricalDemandResponseRead(BaseModel):
    analysis_request_id: str = Field(alias="analysisRequestId")
    filters: SelectedFiltersRead
    warning: HighVolumeWarningRead | None = None
    aggregation_granularity: HistoricalAggregationGranularity | None = Field(default=None, alias="aggregationGranularity")
    result_mode: HistoricalResultMode | None = Field(default=None, alias="resultMode")
    summary_points: list[HistoricalDemandSummaryPointRead] = Field(default_factory=list, alias="summaryPoints")
    outcome_status: HistoricalOutcomeStatus = Field(alias="outcomeStatus")
    message: str | None = None
    summary: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class HistoricalDemandRenderEvent(BaseModel):
    render_status: HistoricalRenderStatus = Field(alias="renderStatus")
    failure_reason: str | None = Field(default=None, alias="failureReason")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_render_failure(self) -> "HistoricalDemandRenderEvent":
        if self.render_status == "render_failed" and not self.failure_reason:
            raise ValueError("failureReason is required when renderStatus is render_failed")
        return self
