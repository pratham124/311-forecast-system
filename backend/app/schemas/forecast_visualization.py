from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ForecastProduct = Literal["daily_1_day", "weekly_7_day"]
RenderStatus = Literal["rendered", "render_failed"]
ViewStatus = Literal["success", "degraded", "fallback_shown", "unavailable", "render_failed"]
DegradationType = Literal["history_missing", "uncertainty_missing"]


class CategoryFilter(BaseModel):
    selected_category: str | None = Field(default=None, alias="selectedCategory")
    selected_categories: list[str] = Field(default_factory=list, alias="selectedCategories")

    model_config = ConfigDict(populate_by_name=True)


class ServiceCategoryOptionsRead(BaseModel):
    forecast_product: ForecastProduct = Field(alias="forecastProduct")
    categories: list[str]

    model_config = ConfigDict(populate_by_name=True)


class VisualizationPoint(BaseModel):
    timestamp: datetime
    value: int

    @field_validator("value", mode="before")
    @classmethod
    def round_value(cls, value: float | int) -> int:
        return int(round(float(value)))


class VisualizationForecastPoint(BaseModel):
    timestamp: datetime
    point_forecast: int = Field(alias="pointForecast")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("point_forecast", mode="before")
    @classmethod
    def round_point_forecast(cls, value: float | int) -> int:
        return int(round(float(value)))


class UncertaintyPoint(BaseModel):
    timestamp: datetime
    p10: int
    p50: int
    p90: int

    @field_validator("p10", "p50", "p90", mode="before")
    @classmethod
    def round_band_value(cls, value: float | int) -> int:
        return int(round(float(value)))


class UncertaintyBands(BaseModel):
    labels: list[str]
    points: list[UncertaintyPoint]


class StatusMessage(BaseModel):
    code: str
    level: Literal["info", "warning", "error"]
    message: str


class FallbackMetadata(BaseModel):
    snapshot_id: str = Field(alias="snapshotId")
    created_at: datetime = Field(alias="createdAt")
    expires_at: datetime = Field(alias="expiresAt")

    model_config = ConfigDict(populate_by_name=True)


class ForecastVisualizationRead(BaseModel):
    visualization_load_id: str = Field(alias="visualizationLoadId")
    forecast_product: ForecastProduct = Field(alias="forecastProduct")
    forecast_granularity: Literal["hourly", "daily"] = Field(alias="forecastGranularity")
    category_filter: CategoryFilter = Field(alias="categoryFilter")
    history_window_start: datetime = Field(alias="historyWindowStart")
    history_window_end: datetime = Field(alias="historyWindowEnd")
    forecast_window_start: datetime | None = Field(default=None, alias="forecastWindowStart")
    forecast_window_end: datetime | None = Field(default=None, alias="forecastWindowEnd")
    forecast_boundary: datetime | None = Field(default=None, alias="forecastBoundary")
    last_updated_at: datetime | None = Field(default=None, alias="lastUpdatedAt")
    source_cleaned_dataset_version_id: str | None = Field(default=None, alias="sourceCleanedDatasetVersionId")
    source_forecast_version_id: str | None = Field(default=None, alias="sourceForecastVersionId")
    source_weekly_forecast_version_id: str | None = Field(default=None, alias="sourceWeeklyForecastVersionId")
    historical_series: list[VisualizationPoint] = Field(default_factory=list, alias="historicalSeries")
    forecast_series: list[VisualizationForecastPoint] = Field(default_factory=list, alias="forecastSeries")
    uncertainty_bands: UncertaintyBands | None = Field(default=None, alias="uncertaintyBands")
    alerts: list[StatusMessage] = Field(default_factory=list)
    pipeline_status: list[StatusMessage] = Field(default_factory=list, alias="pipelineStatus")
    fallback: FallbackMetadata | None = None
    view_status: ViewStatus = Field(alias="viewStatus")
    degradation_type: DegradationType | None = Field(default=None, alias="degradationType")
    summary: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class VisualizationRenderEvent(BaseModel):
    render_status: RenderStatus = Field(alias="renderStatus")
    failure_reason: str | None = Field(default=None, alias="failureReason")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("failure_reason")
    @classmethod
    def validate_failure_reason(cls, value: str | None, info):
        render_status = info.data.get("render_status")
        if render_status == "render_failed" and not value:
            raise ValueError("failureReason is required when renderStatus is render_failed")
        return value
