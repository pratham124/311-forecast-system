from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

OverallDeliveryStatus = Literal["delivered", "partial_delivery", "retry_pending", "manual_review_required"]
SurgeEvaluationRunStatus = Literal["running", "completed", "completed_with_failures"]
TriggerSource = Literal["ingestion_completion", "manual_replay"]
CandidateStatus = Literal["flagged", "below_candidate_threshold", "detector_failed"]
ConfirmationOutcome = Literal["confirmed", "filtered", "suppressed_active_surge", "failed"]


class SurgeEvaluationTriggerRequest(BaseModel):
    forecast_reference_id: str = Field(alias="forecastReferenceId")
    trigger_source: TriggerSource = Field(alias="triggerSource")

    model_config = ConfigDict(populate_by_name=True)


class SurgeEvaluationTriggerResponse(BaseModel):
    surge_evaluation_run_id: str = Field(alias="surgeEvaluationRunId")
    status: Literal["accepted"]
    accepted_at: datetime = Field(alias="acceptedAt")

    model_config = ConfigDict(populate_by_name=True)


class SurgeNotificationChannelAttemptRead(BaseModel):
    channel_type: str = Field(alias="channelType")
    attempt_number: int = Field(alias="attemptNumber")
    status: Literal["succeeded", "failed"]
    attempted_at: datetime = Field(alias="attemptedAt")
    failure_reason: str | None = Field(default=None, alias="failureReason")
    provider_reference: str | None = Field(default=None, alias="providerReference")

    model_config = ConfigDict(populate_by_name=True)


class SurgeConfirmationOutcomeRead(BaseModel):
    surge_confirmation_outcome_id: str = Field(alias="surgeConfirmationOutcomeId")
    outcome: ConfirmationOutcome
    z_score_check_passed: bool | None = Field(default=None, alias="zScoreCheckPassed")
    percent_floor_check_passed: bool | None = Field(default=None, alias="percentFloorCheckPassed")
    surge_notification_event_id: str | None = Field(default=None, alias="surgeNotificationEventId")
    confirmed_at: datetime = Field(alias="confirmedAt")
    failure_reason: str | None = Field(default=None, alias="failureReason")

    model_config = ConfigDict(populate_by_name=True)


class SurgeCandidateRead(BaseModel):
    surge_candidate_id: str = Field(alias="surgeCandidateId")
    service_category: str = Field(alias="serviceCategory")
    evaluation_window_start: datetime = Field(alias="evaluationWindowStart")
    evaluation_window_end: datetime = Field(alias="evaluationWindowEnd")
    actual_demand_value: float = Field(alias="actualDemandValue")
    forecast_p50_value: float | None = Field(default=None, alias="forecastP50Value")
    residual_value: float | None = Field(default=None, alias="residualValue")
    residual_z_score: float | None = Field(default=None, alias="residualZScore")
    percent_above_forecast: float | None = Field(default=None, alias="percentAboveForecast")
    rolling_baseline_mean: float | None = Field(default=None, alias="rollingBaselineMean")
    rolling_baseline_stddev: float | None = Field(default=None, alias="rollingBaselineStddev")
    candidate_status: CandidateStatus = Field(alias="candidateStatus")
    detected_at: datetime = Field(alias="detectedAt")
    failure_reason: str | None = Field(default=None, alias="failureReason")
    confirmation: SurgeConfirmationOutcomeRead | None = None

    model_config = ConfigDict(populate_by_name=True)


class SurgeEvaluationRunSummary(BaseModel):
    surge_evaluation_run_id: str = Field(alias="surgeEvaluationRunId")
    ingestion_run_id: str = Field(alias="ingestionRunId")
    trigger_source: TriggerSource = Field(alias="triggerSource")
    status: SurgeEvaluationRunStatus
    evaluated_scope_count: int = Field(alias="evaluatedScopeCount")
    candidate_count: int = Field(alias="candidateCount")
    confirmed_count: int = Field(alias="confirmedCount")
    notification_created_count: int = Field(alias="notificationCreatedCount")
    started_at: datetime = Field(alias="startedAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    failure_summary: str | None = Field(default=None, alias="failureSummary")

    model_config = ConfigDict(populate_by_name=True)


class SurgeEvaluationRunListResponse(BaseModel):
    items: list[SurgeEvaluationRunSummary]


class SurgeEvaluationRunDetail(SurgeEvaluationRunSummary):
    candidates: list[SurgeCandidateRead]


class SurgeAlertEventSummary(BaseModel):
    surge_notification_event_id: str = Field(alias="surgeNotificationEventId")
    surge_evaluation_run_id: str = Field(alias="surgeEvaluationRunId")
    surge_candidate_id: str = Field(alias="surgeCandidateId")
    service_category: str = Field(alias="serviceCategory")
    evaluation_window_start: datetime = Field(alias="evaluationWindowStart")
    evaluation_window_end: datetime = Field(alias="evaluationWindowEnd")
    actual_demand_value: float = Field(alias="actualDemandValue")
    forecast_p50_value: float = Field(alias="forecastP50Value")
    residual_value: float = Field(alias="residualValue")
    residual_z_score: float = Field(alias="residualZScore")
    percent_above_forecast: float | None = Field(default=None, alias="percentAboveForecast")
    overall_delivery_status: OverallDeliveryStatus = Field(alias="overallDeliveryStatus")
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class SurgeAlertEventListResponse(BaseModel):
    items: list[SurgeAlertEventSummary]


class SurgeAlertEvent(SurgeAlertEventSummary):
    surge_detection_configuration_id: str = Field(alias="surgeDetectionConfigurationId")
    follow_up_reason: str | None = Field(default=None, alias="followUpReason")
    correlation_id: str | None = Field(default=None, alias="correlationId")
    channel_attempts: list[SurgeNotificationChannelAttemptRead] = Field(alias="channelAttempts")
