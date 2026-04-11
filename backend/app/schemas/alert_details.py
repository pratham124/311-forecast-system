from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


AlertSource = Literal["threshold_alert", "surge_alert"]
AlertForecastProduct = Literal["daily", "weekly"]
AlertComponentStatus = Literal["available", "unavailable", "failed"]
AlertDetailViewStatus = Literal["rendered", "partial", "unavailable", "error"]


class AlertScopeRead(BaseModel):
    service_category: str = Field(alias="serviceCategory")
    geography_type: str | None = Field(default=None, alias="geographyType")
    geography_value: str | None = Field(default=None, alias="geographyValue")

    model_config = ConfigDict(populate_by_name=True)


class AlertDistributionPointRead(BaseModel):
    label: str
    bucket_start: datetime | None = Field(default=None, alias="bucketStart")
    bucket_end: datetime | None = Field(default=None, alias="bucketEnd")
    forecast_date_local: date | None = Field(default=None, alias="forecastDateLocal")
    p10: float
    p50: float
    p90: float
    is_alerted_bucket: bool = Field(alias="isAlertedBucket")

    model_config = ConfigDict(populate_by_name=True)


class AlertDistributionComponentRead(BaseModel):
    status: AlertComponentStatus
    granularity: Literal["hourly", "daily"] | None = None
    summary_value: float | None = Field(default=None, alias="summaryValue")
    points: list[AlertDistributionPointRead] = Field(default_factory=list)
    unavailable_reason: str | None = Field(default=None, alias="unavailableReason")
    failure_reason: str | None = Field(default=None, alias="failureReason")

    model_config = ConfigDict(populate_by_name=True)


class AlertDriverRead(BaseModel):
    label: str
    contribution: float
    direction: Literal["increase", "decrease"]


class AlertDriversComponentRead(BaseModel):
    status: AlertComponentStatus
    drivers: list[AlertDriverRead] = Field(default_factory=list)
    unavailable_reason: str | None = Field(default=None, alias="unavailableReason")
    failure_reason: str | None = Field(default=None, alias="failureReason")

    model_config = ConfigDict(populate_by_name=True)


class AlertAnomalyContextItemRead(BaseModel):
    surge_candidate_id: str = Field(alias="surgeCandidateId")
    surge_notification_event_id: str | None = Field(default=None, alias="surgeNotificationEventId")
    evaluation_window_start: datetime = Field(alias="evaluationWindowStart")
    evaluation_window_end: datetime = Field(alias="evaluationWindowEnd")
    actual_demand_value: float = Field(alias="actualDemandValue")
    forecast_p50_value: float | None = Field(default=None, alias="forecastP50Value")
    residual_z_score: float | None = Field(default=None, alias="residualZScore")
    percent_above_forecast: float | None = Field(default=None, alias="percentAboveForecast")
    candidate_status: str = Field(alias="candidateStatus")
    confirmation_outcome: str | None = Field(default=None, alias="confirmationOutcome")
    is_selected_alert: bool = Field(alias="isSelectedAlert")

    model_config = ConfigDict(populate_by_name=True)


class AlertAnomaliesComponentRead(BaseModel):
    status: AlertComponentStatus
    items: list[AlertAnomalyContextItemRead] = Field(default_factory=list)
    unavailable_reason: str | None = Field(default=None, alias="unavailableReason")
    failure_reason: str | None = Field(default=None, alias="failureReason")

    model_config = ConfigDict(populate_by_name=True)


class AlertDetailRead(BaseModel):
    alert_detail_load_id: str = Field(alias="alertDetailLoadId")
    alert_source: AlertSource = Field(alias="alertSource")
    alert_id: str = Field(alias="alertId")
    correlation_id: str | None = Field(default=None, alias="correlationId")
    alert_triggered_at: datetime = Field(alias="alertTriggeredAt")
    overall_delivery_status: str = Field(alias="overallDeliveryStatus")
    forecast_product: AlertForecastProduct | None = Field(default=None, alias="forecastProduct")
    forecast_reference_id: str | None = Field(default=None, alias="forecastReferenceId")
    forecast_window_type: str | None = Field(default=None, alias="forecastWindowType")
    window_start: datetime = Field(alias="windowStart")
    window_end: datetime = Field(alias="windowEnd")
    primary_metric_label: str = Field(alias="primaryMetricLabel")
    primary_metric_value: float = Field(alias="primaryMetricValue")
    secondary_metric_label: str = Field(alias="secondaryMetricLabel")
    secondary_metric_value: float = Field(alias="secondaryMetricValue")
    scope: AlertScopeRead
    view_status: AlertDetailViewStatus = Field(alias="viewStatus")
    failure_reason: str | None = Field(default=None, alias="failureReason")
    distribution: AlertDistributionComponentRead
    drivers: AlertDriversComponentRead
    anomalies: AlertAnomaliesComponentRead

    model_config = ConfigDict(populate_by_name=True)


class AlertDetailRenderEvent(BaseModel):
    render_status: Literal["rendered", "render_failed"] = Field(alias="renderStatus")
    failure_reason: str | None = Field(default=None, alias="failureReason")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_event(self) -> "AlertDetailRenderEvent":
        if self.render_status == "render_failed" and not self.failure_reason:
            raise ValueError("failureReason is required when renderStatus is render_failed")
        return self


class AlertDetailRenderEventResponse(BaseModel):
    alert_detail_load_id: str = Field(alias="alertDetailLoadId")
    recorded_outcome_status: Literal["rendered", "render_failed"] = Field(alias="recordedOutcomeStatus")
    message: str

    model_config = ConfigDict(populate_by_name=True)
