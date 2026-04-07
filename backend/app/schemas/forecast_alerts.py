from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ThresholdEvaluationTriggerRequest(BaseModel):
    forecast_reference_id: str = Field(alias="forecastReferenceId")
    forecast_product: str = Field(alias="forecastProduct")
    trigger_source: str = Field(alias="triggerSource")

    model_config = ConfigDict(populate_by_name=True)


class ThresholdEvaluationTriggerResponse(BaseModel):
    threshold_evaluation_run_id: str = Field(alias="thresholdEvaluationRunId")
    status: str
    accepted_at: datetime = Field(alias="acceptedAt")

    model_config = ConfigDict(populate_by_name=True)


class NotificationChannelAttemptRead(BaseModel):
    channel_type: str = Field(alias="channelType")
    attempt_number: int = Field(alias="attemptNumber")
    attempted_at: datetime = Field(alias="attemptedAt")
    status: str
    failure_reason: str | None = Field(default=None, alias="failureReason")
    provider_reference: str | None = Field(default=None, alias="providerReference")

    model_config = ConfigDict(populate_by_name=True)


class ThresholdAlertEventSummaryRead(BaseModel):
    notification_event_id: str = Field(alias="notificationEventId")
    service_category: str = Field(alias="serviceCategory")
    geography_type: str | None = Field(default=None, alias="geographyType")
    geography_value: str | None = Field(default=None, alias="geographyValue")
    forecast_window_type: str = Field(alias="forecastWindowType")
    forecast_window_start: datetime = Field(alias="forecastWindowStart")
    forecast_window_end: datetime = Field(alias="forecastWindowEnd")
    forecast_value: float = Field(alias="forecastValue")
    threshold_value: float = Field(alias="thresholdValue")
    overall_delivery_status: str = Field(alias="overallDeliveryStatus")
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class ThresholdAlertEventRead(ThresholdAlertEventSummaryRead):
    threshold_evaluation_run_id: str = Field(alias="thresholdEvaluationRunId")
    threshold_configuration_id: str = Field(alias="thresholdConfigurationId")
    follow_up_reason: str | None = Field(default=None, alias="followUpReason")
    delivered_at: datetime | None = Field(default=None, alias="deliveredAt")
    failed_channel_count: int = Field(alias="failedChannelCount")
    channel_attempts: list[NotificationChannelAttemptRead] = Field(alias="channelAttempts")


class ThresholdAlertEventListResponse(BaseModel):
    items: list[ThresholdAlertEventSummaryRead]

    model_config = ConfigDict(populate_by_name=True)


class ThresholdConfigurationUpdateRequest(BaseModel):
    threshold_value: float = Field(alias="thresholdValue")

    model_config = ConfigDict(populate_by_name=True)


class ThresholdConfigurationRead(BaseModel):
    threshold_configuration_id: str = Field(alias="thresholdConfigurationId")
    service_category: str = Field(alias="serviceCategory")
    forecast_window_type: str = Field(alias="forecastWindowType")
    threshold_value: float = Field(alias="thresholdValue")
    operational_manager_id: str = Field(alias="operationalManagerId")
    status: str
    effective_from: datetime = Field(alias="effectiveFrom")
    effective_to: datetime | None = Field(default=None, alias="effectiveTo")

    model_config = ConfigDict(populate_by_name=True)


class ThresholdConfigurationListResponse(BaseModel):
    items: list[ThresholdConfigurationRead]

    model_config = ConfigDict(populate_by_name=True)
