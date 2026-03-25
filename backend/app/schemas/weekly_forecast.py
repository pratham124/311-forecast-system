from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WeeklyForecastTriggerRequest(BaseModel):
    trigger_type: str = Field(default="on_demand", alias="triggerType")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("trigger_type")
    @classmethod
    def validate_trigger_type(cls, value: str) -> str:
        if value != "on_demand":
            raise ValueError("triggerType must be on_demand")
        return value


class WeeklyForecastRunAccepted(BaseModel):
    weekly_forecast_run_id: str = Field(alias="weeklyForecastRunId")
    status: str

    model_config = ConfigDict(populate_by_name=True)


class WeeklyForecastBucketRead(BaseModel):
    forecast_date_local: date = Field(alias="forecastDateLocal")
    service_category: str = Field(alias="serviceCategory")
    geography_key: str | None = Field(default=None, alias="geographyKey")
    point_forecast: float = Field(alias="pointForecast")
    quantile_p10: float = Field(alias="quantileP10")
    quantile_p50: float = Field(alias="quantileP50")
    quantile_p90: float = Field(alias="quantileP90")
    baseline_value: float = Field(alias="baselineValue")

    model_config = ConfigDict(populate_by_name=True)


class WeeklyForecastRunStatusRead(BaseModel):
    weekly_forecast_run_id: str = Field(alias="weeklyForecastRunId")
    trigger_type: str = Field(alias="triggerType")
    source_cleaned_dataset_version_id: str | None = Field(default=None, alias="sourceCleanedDatasetVersionId")
    week_start_local: datetime = Field(alias="weekStartLocal")
    week_end_local: datetime = Field(alias="weekEndLocal")
    status: str
    result_type: str | None = Field(default=None, alias="resultType")
    generated_forecast_version_id: str | None = Field(default=None, alias="generatedForecastVersionId")
    served_forecast_version_id: str | None = Field(default=None, alias="servedForecastVersionId")
    geography_scope: str | None = Field(default=None, alias="geographyScope")
    started_at: datetime = Field(alias="startedAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    failure_reason: str | None = Field(default=None, alias="failureReason")
    summary: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class WeeklyForecastModelRunStatusRead(BaseModel):
    forecast_model_run_id: str = Field(alias="forecastModelRunId")
    forecast_product_name: str = Field(alias="forecastProductName")
    trigger_type: str = Field(alias="triggerType")
    source_cleaned_dataset_version_id: str | None = Field(default=None, alias="sourceCleanedDatasetVersionId")
    training_window_start: datetime = Field(alias="trainingWindowStart")
    training_window_end: datetime = Field(alias="trainingWindowEnd")
    status: str
    result_type: str | None = Field(default=None, alias="resultType")
    forecast_model_artifact_id: str | None = Field(default=None, alias="forecastModelArtifactId")
    geography_scope: str | None = Field(default=None, alias="geographyScope")
    started_at: datetime = Field(alias="startedAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    failure_reason: str | None = Field(default=None, alias="failureReason")
    summary: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class CurrentWeeklyForecastModelRead(BaseModel):
    forecast_product_name: str = Field(alias="forecastProductName")
    forecast_model_artifact_id: str = Field(alias="forecastModelArtifactId")
    source_cleaned_dataset_version_id: str = Field(alias="sourceCleanedDatasetVersionId")
    training_window_start: datetime = Field(alias="trainingWindowStart")
    training_window_end: datetime = Field(alias="trainingWindowEnd")
    updated_at: datetime = Field(alias="updatedAt")
    updated_by_run_id: str = Field(alias="updatedByRunId")
    geography_scope: str = Field(alias="geographyScope")
    model_family: str = Field(alias="modelFamily")
    baseline_method: str = Field(alias="baselineMethod")
    feature_schema_version: str = Field(alias="featureSchemaVersion")
    artifact_path: str = Field(alias="artifactPath")
    summary: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class CurrentWeeklyForecastRead(BaseModel):
    weekly_forecast_version_id: str = Field(alias="weeklyForecastVersionId")
    source_cleaned_dataset_version_id: str = Field(alias="sourceCleanedDatasetVersionId")
    week_start_local: datetime = Field(alias="weekStartLocal")
    week_end_local: datetime = Field(alias="weekEndLocal")
    bucket_granularity: str = Field(alias="bucketGranularity")
    bucket_count_days: int = Field(alias="bucketCountDays")
    geography_scope: str = Field(alias="geographyScope")
    updated_at: datetime = Field(alias="updatedAt")
    updated_by_run_id: str = Field(alias="updatedByRunId")
    summary: str | None = None
    buckets: list[WeeklyForecastBucketRead]

    model_config = ConfigDict(populate_by_name=True)
