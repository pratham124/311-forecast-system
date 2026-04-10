from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ViewStatus = Literal["rendered_with_metrics", "rendered_without_metrics", "unavailable", "error"]
MetricResolutionStatus = Literal["retrieved_precomputed", "computed_on_demand", "unavailable", "failed"]


class ForecastAccuracyQuery(BaseModel):
    time_range_start: datetime | None = Field(default=None, alias="timeRangeStart")
    time_range_end: datetime | None = Field(default=None, alias="timeRangeEnd")
    service_category: str | None = Field(default=None, alias="serviceCategory")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_scope(self) -> "ForecastAccuracyQuery":
        if (self.time_range_start is None) != (self.time_range_end is None):
            raise ValueError("timeRangeStart and timeRangeEnd must be provided together")
        if self.time_range_start and self.time_range_end and self.time_range_end <= self.time_range_start:
            raise ValueError("timeRangeEnd must be later than timeRangeStart")
        return self


class ForecastAccuracyMetrics(BaseModel):
    mae: float
    rmse: float
    mape: float


class ForecastAccuracyAlignedBucketRead(BaseModel):
    bucket_start: datetime = Field(alias="bucketStart")
    bucket_end: datetime = Field(alias="bucketEnd")
    service_category: str | None = Field(default=None, alias="serviceCategory")
    forecast_value: float = Field(alias="forecastValue")
    actual_value: float = Field(alias="actualValue")
    absolute_error_value: float = Field(alias="absoluteErrorValue")
    percentage_error_value: float | None = Field(default=None, alias="percentageErrorValue")

    model_config = ConfigDict(populate_by_name=True)


class ForecastAccuracyResponse(BaseModel):
    forecast_accuracy_request_id: str = Field(alias="forecastAccuracyRequestId")
    forecast_accuracy_result_id: str = Field(alias="forecastAccuracyResultId")
    correlation_id: str | None = Field(default=None, alias="correlationId")
    time_range_start: datetime = Field(alias="timeRangeStart")
    time_range_end: datetime = Field(alias="timeRangeEnd")
    service_category: str | None = Field(default=None, alias="serviceCategory")
    forecast_product_name: Literal["daily_1_day"] = Field(alias="forecastProductName")
    comparison_granularity: Literal["hourly", "daily"] = Field(alias="comparisonGranularity")
    view_status: ViewStatus = Field(alias="viewStatus")
    metric_resolution_status: MetricResolutionStatus | None = Field(default=None, alias="metricResolutionStatus")
    status_message: str | None = Field(default=None, alias="statusMessage")
    metrics: ForecastAccuracyMetrics | None = None
    aligned_buckets: list[ForecastAccuracyAlignedBucketRead] = Field(default_factory=list, alias="alignedBuckets")

    model_config = ConfigDict(populate_by_name=True)


class ForecastAccuracyRenderEvent(BaseModel):
    render_status: Literal["rendered", "render_failed"] = Field(alias="renderStatus")
    failure_reason: str | None = Field(default=None, alias="failureReason")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_event(self) -> "ForecastAccuracyRenderEvent":
        if self.render_status == "render_failed" and not self.failure_reason:
            raise ValueError("failureReason is required when renderStatus is render_failed")
        return self


class ForecastAccuracyRenderEventResponse(BaseModel):
    forecast_accuracy_request_id: str = Field(alias="forecastAccuracyRequestId")
    recorded_outcome_status: Literal["rendered", "render_failed"] = Field(alias="recordedOutcomeStatus")
    message: str

    model_config = ConfigDict(populate_by_name=True)
