from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ForecastAlertProduct = Literal["daily", "weekly"]
ForecastWindowType = Literal["hourly", "daily"]
TriggerSource = Literal["forecast_publish", "forecast_refresh", "scheduled_recheck", "manual_replay"]
OverallDeliveryStatus = Literal["delivered", "partial_delivery", "retry_pending", "manual_review_required"]


class ThresholdEvaluationTriggerRequest(BaseModel):
    forecast_reference_id: str = Field(alias="forecastReferenceId")
    forecast_product: ForecastAlertProduct = Field(alias="forecastProduct")
    trigger_source: TriggerSource = Field(alias="triggerSource")

    model_config = ConfigDict(populate_by_name=True)


class ThresholdEvaluationTriggerResponse(BaseModel):
    threshold_evaluation_run_id: str = Field(alias="thresholdEvaluationRunId")
    status: Literal["accepted"]
    accepted_at: datetime = Field(alias="acceptedAt")

    model_config = ConfigDict(populate_by_name=True)


class ThresholdConfigurationWrite(BaseModel):
    service_category: str = Field(alias="serviceCategory", min_length=1)
    forecast_window_type: ForecastWindowType = Field(alias="forecastWindowType")
    threshold_value: float = Field(alias="thresholdValue", gt=0)
    notification_channels: list[str] = Field(alias="notificationChannels", min_length=1)

    model_config = ConfigDict(populate_by_name=True)


class ThresholdConfigurationUpdate(ThresholdConfigurationWrite):
    pass


class ThresholdConfigurationRead(BaseModel):
    threshold_configuration_id: str = Field(alias="thresholdConfigurationId")
    service_category: str = Field(alias="serviceCategory")
    forecast_window_type: ForecastWindowType = Field(alias="forecastWindowType")
    threshold_value: float = Field(alias="thresholdValue")
    notification_channels: list[str] = Field(alias="notificationChannels")
    operational_manager_id: str = Field(alias="operationalManagerId")
    status: str
    effective_from: datetime = Field(alias="effectiveFrom")
    effective_to: datetime | None = Field(default=None, alias="effectiveTo")

    model_config = ConfigDict(populate_by_name=True)


class ThresholdConfigurationListResponse(BaseModel):
    items: list[ThresholdConfigurationRead]


class ServiceCategoryListResponse(BaseModel):
    items: list[str]


class NotificationChannelAttemptRead(BaseModel):
    channel_type: str = Field(alias="channelType")
    attempt_number: int = Field(alias="attemptNumber")
    status: Literal["succeeded", "failed"]
    attempted_at: datetime = Field(alias="attemptedAt")
    failure_reason: str | None = Field(default=None, alias="failureReason")
    provider_reference: str | None = Field(default=None, alias="providerReference")

    model_config = ConfigDict(populate_by_name=True)


class ThresholdAlertEventSummary(BaseModel):
    notification_event_id: str = Field(alias="notificationEventId")
    service_category: str = Field(alias="serviceCategory")
    forecast_window_type: ForecastWindowType = Field(alias="forecastWindowType")
    forecast_window_start: datetime = Field(alias="forecastWindowStart")
    forecast_window_end: datetime = Field(alias="forecastWindowEnd")
    forecast_value: float = Field(alias="forecastValue")
    threshold_value: float = Field(alias="thresholdValue")
    overall_delivery_status: OverallDeliveryStatus = Field(alias="overallDeliveryStatus")
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class ThresholdAlertEventListResponse(BaseModel):
    items: list[ThresholdAlertEventSummary]


class ThresholdAlertEvent(ThresholdAlertEventSummary):
    threshold_evaluation_run_id: str = Field(alias="thresholdEvaluationRunId")
    threshold_configuration_id: str = Field(alias="thresholdConfigurationId")
    follow_up_reason: str | None = Field(default=None, alias="followUpReason")
    channel_attempts: list[NotificationChannelAttemptRead] = Field(alias="channelAttempts")
