from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ForecastTriggerRequest(BaseModel):
    trigger_type: str = Field(default="on_demand", alias="triggerType")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("trigger_type")
    @classmethod
    def validate_trigger_type(cls, value: str) -> str:
        if value != "on_demand":
            raise ValueError("triggerType must be on_demand")
        return value


class ForecastRunAccepted(BaseModel):
    forecast_run_id: str = Field(alias="forecastRunId")
    status: str

    model_config = ConfigDict(populate_by_name=True)


class ForecastBucketRead(BaseModel):
    bucket_start: datetime = Field(alias="bucketStart")
    bucket_end: datetime = Field(alias="bucketEnd")
    service_category: str = Field(alias="serviceCategory")
    geography_key: str | None = Field(default=None, alias="geographyKey")
    point_forecast: float = Field(alias="pointForecast")
    quantile_p10: float = Field(alias="quantileP10")
    quantile_p50: float = Field(alias="quantileP50")
    quantile_p90: float = Field(alias="quantileP90")
    baseline_value: float = Field(alias="baselineValue")

    model_config = ConfigDict(populate_by_name=True)


class ForecastRunStatusRead(BaseModel):
    forecast_run_id: str = Field(alias="forecastRunId")
    trigger_type: str = Field(alias="triggerType")
    source_cleaned_dataset_version_id: str | None = Field(default=None, alias="sourceCleanedDatasetVersionId")
    requested_horizon_start: datetime = Field(alias="requestedHorizonStart")
    requested_horizon_end: datetime = Field(alias="requestedHorizonEnd")
    status: str
    result_type: str | None = Field(default=None, alias="resultType")
    forecast_version_id: str | None = Field(default=None, alias="forecastVersionId")
    served_forecast_version_id: str | None = Field(default=None, alias="servedForecastVersionId")
    geography_scope: str | None = Field(default=None, alias="geographyScope")
    started_at: datetime = Field(alias="startedAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    failure_reason: str | None = Field(default=None, alias="failureReason")
    summary: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class CurrentForecastRead(BaseModel):
    forecast_version_id: str = Field(alias="forecastVersionId")
    source_cleaned_dataset_version_id: str = Field(alias="sourceCleanedDatasetVersionId")
    horizon_start: datetime = Field(alias="horizonStart")
    horizon_end: datetime = Field(alias="horizonEnd")
    bucket_granularity: str = Field(alias="bucketGranularity")
    bucket_count: int = Field(alias="bucketCount")
    geography_scope: str = Field(alias="geographyScope")
    summary: str | None = None
    updated_at: datetime = Field(alias="updatedAt")
    updated_by_run_id: str = Field(alias="updatedByRunId")
    buckets: list[ForecastBucketRead]

    model_config = ConfigDict(populate_by_name=True)
