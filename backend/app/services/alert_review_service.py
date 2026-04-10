from __future__ import annotations

from fastapi import HTTPException, status

from app.repositories.notification_event_repository import NotificationEventRepository
from app.schemas.forecast_alerts import NotificationChannelAttemptRead, ThresholdAlertEvent, ThresholdAlertEventListResponse, ThresholdAlertEventSummary


class AlertReviewService:
    def __init__(self, repository: NotificationEventRepository) -> None:
        self.repository = repository

    def list_events(self, **filters) -> ThresholdAlertEventListResponse:
        items = [
            ThresholdAlertEventSummary(
                notificationEventId=item.notification_event_id,
                serviceCategory=item.service_category,
                forecastWindowType=item.forecast_window_type,
                forecastWindowStart=item.forecast_window_start,
                forecastWindowEnd=item.forecast_window_end,
                forecastValue=float(item.forecast_value),
                thresholdValue=float(item.threshold_value),
                overallDeliveryStatus=item.overall_delivery_status,
                createdAt=item.created_at,
            )
            for item in self.repository.list_events(**filters)
        ]
        return ThresholdAlertEventListResponse(items=items)

    def get_event(self, notification_event_id: str) -> ThresholdAlertEvent:
        bundle = self.repository.get_event_bundle(notification_event_id)
        if bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert event not found")
        return ThresholdAlertEvent(
            notificationEventId=bundle.event.notification_event_id,
            thresholdEvaluationRunId=bundle.event.threshold_evaluation_run_id,
            thresholdConfigurationId=bundle.event.threshold_configuration_id,
            serviceCategory=bundle.event.service_category,
            forecastWindowType=bundle.event.forecast_window_type,
            forecastWindowStart=bundle.event.forecast_window_start,
            forecastWindowEnd=bundle.event.forecast_window_end,
            forecastValue=float(bundle.event.forecast_value),
            thresholdValue=float(bundle.event.threshold_value),
            overallDeliveryStatus=bundle.event.overall_delivery_status,
            followUpReason=bundle.event.follow_up_reason,
            channelAttempts=[
                NotificationChannelAttemptRead(
                    channelType=attempt.channel_type,
                    attemptNumber=attempt.attempt_number,
                    status=attempt.status,
                    attemptedAt=attempt.attempted_at,
                    failureReason=attempt.failure_reason,
                    providerReference=attempt.provider_reference,
                )
                for attempt in bundle.attempts
            ],
            createdAt=bundle.event.created_at,
        )
