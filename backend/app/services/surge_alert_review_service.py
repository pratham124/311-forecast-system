from __future__ import annotations

from fastapi import HTTPException, status

from app.repositories.surge_evaluation_repository import SurgeEvaluationRepository
from app.repositories.surge_notification_event_repository import SurgeNotificationEventRepository
from app.schemas.surge_alerts import (
    SurgeAlertEvent,
    SurgeAlertEventListResponse,
    SurgeAlertEventSummary,
    SurgeCandidateRead,
    SurgeConfirmationOutcomeRead,
    SurgeEvaluationRunDetail,
    SurgeEvaluationRunListResponse,
    SurgeEvaluationRunSummary,
    SurgeNotificationChannelAttemptRead,
)


class SurgeAlertReviewService:
    def __init__(
        self,
        evaluation_repository: SurgeEvaluationRepository,
        event_repository: SurgeNotificationEventRepository,
    ) -> None:
        self.evaluation_repository = evaluation_repository
        self.event_repository = event_repository

    def list_evaluations(self, *, ingestion_run_id: str | None = None, status: str | None = None) -> SurgeEvaluationRunListResponse:
        return SurgeEvaluationRunListResponse(
            items=[
                SurgeEvaluationRunSummary(
                    surgeEvaluationRunId=item.surge_evaluation_run_id,
                    ingestionRunId=item.ingestion_run_id,
                    triggerSource=item.trigger_source,
                    status=item.status,
                    evaluatedScopeCount=item.evaluated_scope_count,
                    candidateCount=item.candidate_count,
                    confirmedCount=item.confirmed_count,
                    notificationCreatedCount=item.notification_created_count,
                    startedAt=item.started_at,
                    completedAt=item.completed_at,
                    failureSummary=item.failure_summary,
                )
                for item in self.evaluation_repository.list_runs(ingestion_run_id=ingestion_run_id, status=status)
            ]
        )

    def get_evaluation(self, surge_evaluation_run_id: str) -> SurgeEvaluationRunDetail:
        bundle = self.evaluation_repository.get_run_detail(surge_evaluation_run_id)
        if bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surge evaluation run not found")
        return SurgeEvaluationRunDetail(
            surgeEvaluationRunId=bundle.run.surge_evaluation_run_id,
            ingestionRunId=bundle.run.ingestion_run_id,
            triggerSource=bundle.run.trigger_source,
            status=bundle.run.status,
            evaluatedScopeCount=bundle.run.evaluated_scope_count,
            candidateCount=bundle.run.candidate_count,
            confirmedCount=bundle.run.confirmed_count,
            notificationCreatedCount=bundle.run.notification_created_count,
            startedAt=bundle.run.started_at,
            completedAt=bundle.run.completed_at,
            failureSummary=bundle.run.failure_summary,
            candidates=[
                SurgeCandidateRead(
                    surgeCandidateId=item.candidate.surge_candidate_id,
                    serviceCategory=item.candidate.service_category,
                    evaluationWindowStart=item.candidate.evaluation_window_start,
                    evaluationWindowEnd=item.candidate.evaluation_window_end,
                    actualDemandValue=float(item.candidate.actual_demand_value),
                    forecastP50Value=None if item.candidate.forecast_p50_value is None else float(item.candidate.forecast_p50_value),
                    residualValue=None if item.candidate.residual_value is None else float(item.candidate.residual_value),
                    residualZScore=None if item.candidate.residual_z_score is None else float(item.candidate.residual_z_score),
                    percentAboveForecast=None if item.candidate.percent_above_forecast is None else float(item.candidate.percent_above_forecast),
                    rollingBaselineMean=None if item.candidate.rolling_baseline_mean is None else float(item.candidate.rolling_baseline_mean),
                    rollingBaselineStddev=None if item.candidate.rolling_baseline_stddev is None else float(item.candidate.rolling_baseline_stddev),
                    candidateStatus=item.candidate.candidate_status,
                    detectedAt=item.candidate.detected_at,
                    failureReason=item.candidate.failure_reason,
                    confirmation=None
                    if item.confirmation is None
                    else SurgeConfirmationOutcomeRead(
                        surgeConfirmationOutcomeId=item.confirmation.surge_confirmation_outcome_id,
                        outcome=item.confirmation.outcome,
                        zScoreCheckPassed=item.confirmation.z_score_check_passed,
                        percentFloorCheckPassed=item.confirmation.percent_floor_check_passed,
                        surgeNotificationEventId=item.confirmation.surge_notification_event_id,
                        confirmedAt=item.confirmation.confirmed_at,
                        failureReason=item.confirmation.failure_reason,
                    ),
                )
                for item in bundle.candidates
            ],
        )

    def list_events(self, *, service_category: str | None = None, overall_delivery_status: str | None = None) -> SurgeAlertEventListResponse:
        return SurgeAlertEventListResponse(
            items=[
                SurgeAlertEventSummary(
                    surgeNotificationEventId=item.surge_notification_event_id,
                    surgeEvaluationRunId=item.surge_evaluation_run_id,
                    surgeCandidateId=item.surge_candidate_id,
                    serviceCategory=item.service_category,
                    evaluationWindowStart=item.evaluation_window_start,
                    evaluationWindowEnd=item.evaluation_window_end,
                    actualDemandValue=float(item.actual_demand_value),
                    forecastP50Value=float(item.forecast_p50_value),
                    residualValue=float(item.residual_value),
                    residualZScore=float(item.residual_z_score),
                    percentAboveForecast=None if item.percent_above_forecast is None else float(item.percent_above_forecast),
                    overallDeliveryStatus=item.overall_delivery_status,
                    createdAt=item.created_at,
                )
                for item in self.event_repository.list_events(
                    service_category=service_category,
                    overall_delivery_status=overall_delivery_status,
                )
            ]
        )

    def get_event(self, surge_notification_event_id: str) -> SurgeAlertEvent:
        bundle = self.event_repository.get_event_bundle(surge_notification_event_id)
        if bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surge alert event not found")
        event = bundle.event
        return SurgeAlertEvent(
            surgeNotificationEventId=event.surge_notification_event_id,
            surgeEvaluationRunId=event.surge_evaluation_run_id,
            surgeCandidateId=event.surge_candidate_id,
            surgeDetectionConfigurationId=event.surge_detection_configuration_id,
            serviceCategory=event.service_category,
            evaluationWindowStart=event.evaluation_window_start,
            evaluationWindowEnd=event.evaluation_window_end,
            actualDemandValue=float(event.actual_demand_value),
            forecastP50Value=float(event.forecast_p50_value),
            residualValue=float(event.residual_value),
            residualZScore=float(event.residual_z_score),
            percentAboveForecast=None if event.percent_above_forecast is None else float(event.percent_above_forecast),
            overallDeliveryStatus=event.overall_delivery_status,
            createdAt=event.created_at,
            followUpReason=event.follow_up_reason,
            correlationId=event.correlation_id,
            channelAttempts=[
                SurgeNotificationChannelAttemptRead(
                    channelType=item.channel_type,
                    attemptNumber=item.attempt_number,
                    status=item.status,
                    attemptedAt=item.attempted_at,
                    failureReason=item.failure_reason,
                    providerReference=item.provider_reference,
                )
                for item in bundle.attempts
            ],
        )
