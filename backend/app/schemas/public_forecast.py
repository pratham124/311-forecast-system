from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PublicForecastCategorySummary(BaseModel):
    service_category: str = Field(alias="serviceCategory")
    forecast_demand_value: float | None = Field(default=None, alias="forecastDemandValue")
    demand_level_summary: str | None = Field(default=None, alias="demandLevelSummary")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_summary(self) -> "PublicForecastCategorySummary":
        if self.forecast_demand_value is None and not self.demand_level_summary:
            raise ValueError("Each category summary requires a numeric demand value or a summary label")
        return self


class PublicForecastView(BaseModel):
    public_forecast_request_id: str = Field(alias="publicForecastRequestId")
    status: Literal["available", "unavailable", "error"]
    forecast_window_label: str | None = Field(default=None, alias="forecastWindowLabel")
    published_at: datetime | None = Field(default=None, alias="publishedAt")
    coverage_status: Literal["complete", "incomplete"] | None = Field(default=None, alias="coverageStatus")
    coverage_message: str | None = Field(default=None, alias="coverageMessage")
    sanitization_status: Literal["passed_as_is", "sanitized", "blocked", "failed"] | None = Field(default=None, alias="sanitizationStatus")
    sanitization_summary: str | None = Field(default=None, alias="sanitizationSummary")
    category_summaries: list[PublicForecastCategorySummary] | None = Field(default=None, alias="categorySummaries")
    status_message: str | None = Field(default=None, alias="statusMessage")
    client_correlation_id: str | None = Field(default=None, alias="clientCorrelationId")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_view(self) -> "PublicForecastView":
        if self.status == "available":
            required = [
                self.forecast_window_label,
                self.published_at,
                self.coverage_status,
                self.sanitization_status,
                self.category_summaries,
            ]
            if any(value is None for value in required):
                raise ValueError("Available public forecast responses must include payload details")
            if self.sanitization_status in {"blocked", "failed"}:
                raise ValueError("Blocked and failed sanitization states cannot be returned as available")
            if self.coverage_status == "incomplete" and not self.coverage_message:
                raise ValueError("Incomplete coverage responses require a message")
        else:
            if not self.status_message:
                raise ValueError("Unavailable and error responses require a status message")
        return self


class PublicForecastDisplayEventRequest(BaseModel):
    display_outcome: Literal["rendered", "render_failed"] = Field(alias="displayOutcome")
    failure_reason: str | None = Field(default=None, alias="failureReason")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_request(self) -> "PublicForecastDisplayEventRequest":
        if self.display_outcome == "render_failed" and not self.failure_reason:
            raise ValueError("failureReason is required when displayOutcome is render_failed")
        return self
