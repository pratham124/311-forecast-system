from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ForecastProduct = Literal["daily_1_day", "weekly_7_day"]
MetricName = Literal["mae", "rmse", "mape"]


class EvaluationRunTrigger(BaseModel):
    forecast_product: ForecastProduct = Field(alias="forecastProduct")
    trigger_type: str = Field(default="on_demand", alias="triggerType")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("trigger_type")
    @classmethod
    def validate_trigger_type(cls, value: str) -> str:
        if value != "on_demand":
            raise ValueError("triggerType must be on_demand")
        return value


class EvaluationRunAccepted(BaseModel):
    evaluation_run_id: str = Field(alias="evaluationRunId")
    status: Literal["running"]

    model_config = ConfigDict(populate_by_name=True)


class EvaluationRunStatusRead(BaseModel):
    evaluation_run_id: str = Field(alias="evaluationRunId")
    trigger_type: str = Field(alias="triggerType")
    forecast_product: ForecastProduct = Field(alias="forecastProduct")
    source_cleaned_dataset_version_id: str | None = Field(default=None, alias="sourceCleanedDatasetVersionId")
    source_forecast_version_id: str | None = Field(default=None, alias="sourceForecastVersionId")
    source_weekly_forecast_version_id: str | None = Field(default=None, alias="sourceWeeklyForecastVersionId")
    evaluation_window_start: datetime = Field(alias="evaluationWindowStart")
    evaluation_window_end: datetime = Field(alias="evaluationWindowEnd")
    status: Literal["running", "success", "failed"]
    result_type: str | None = Field(default=None, alias="resultType")
    evaluation_result_id: str | None = Field(default=None, alias="evaluationResultId")
    started_at: datetime = Field(alias="startedAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    failure_reason: str | None = Field(default=None, alias="failureReason")
    summary: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class MetricValueRead(BaseModel):
    metric_name: MetricName = Field(alias="metricName")
    metric_value: float | None = Field(default=None, alias="metricValue")
    is_excluded: bool = Field(alias="isExcluded")
    exclusion_reason: str | None = Field(default=None, alias="exclusionReason")

    model_config = ConfigDict(populate_by_name=True)


class MethodMetricSummaryRead(BaseModel):
    method_name: str = Field(alias="methodName")
    metrics: list[MetricValueRead]

    model_config = ConfigDict(populate_by_name=True)


class EvaluationSegmentRead(BaseModel):
    segment_type: Literal["overall", "service_category", "time_period"] = Field(alias="segmentType")
    segment_key: str = Field(alias="segmentKey")
    segment_status: Literal["complete", "partial"] = Field(alias="segmentStatus")
    comparison_row_count: int = Field(alias="comparisonRowCount")
    excluded_metric_count: int = Field(alias="excludedMetricCount")
    notes: str | None = None
    method_metrics: list[MethodMetricSummaryRead] = Field(alias="methodMetrics")

    model_config = ConfigDict(populate_by_name=True)


class FairComparisonMetadataRead(BaseModel):
    evaluation_window_start: datetime = Field(alias="evaluationWindowStart")
    evaluation_window_end: datetime = Field(alias="evaluationWindowEnd")
    product_scope: ForecastProduct = Field(alias="productScope")
    segment_coverage: list[str] = Field(alias="segmentCoverage")

    model_config = ConfigDict(populate_by_name=True)


class CurrentEvaluationRead(BaseModel):
    evaluation_result_id: str = Field(alias="evaluationResultId")
    forecast_product: ForecastProduct = Field(alias="forecastProduct")
    source_cleaned_dataset_version_id: str = Field(alias="sourceCleanedDatasetVersionId")
    source_forecast_version_id: str | None = Field(default=None, alias="sourceForecastVersionId")
    source_weekly_forecast_version_id: str | None = Field(default=None, alias="sourceWeeklyForecastVersionId")
    evaluation_window_start: datetime = Field(alias="evaluationWindowStart")
    evaluation_window_end: datetime = Field(alias="evaluationWindowEnd")
    comparison_status: Literal["complete", "partial"] = Field(alias="comparisonStatus")
    baseline_methods: list[str] = Field(alias="baselineMethods")
    metric_set: list[MetricName] = Field(alias="metricSet")
    fair_comparison: FairComparisonMetadataRead = Field(alias="fairComparison")
    updated_at: datetime = Field(alias="updatedAt")
    updated_by_run_id: str = Field(alias="updatedByRunId")
    summary: str | None = None
    comparison_summary: str | None = Field(default=None, alias="comparisonSummary")
    segments: list[EvaluationSegmentRead]

    model_config = ConfigDict(populate_by_name=True)
