from __future__ import annotations

from app.repositories.notification_event_repository import NotificationEventRepository
from app.schemas.forecast_alerts import (
    NotificationChannelAttemptRead,
    ThresholdAlertEventRead,
    ThresholdAlertEventSummaryRead,
)


class AlertReviewService:
    def __init__(self, repository: NotificationEventRepository) -> None:
        self.repository = repository

    def list_events(
        self,
        *,
        service_category: str | None,
        geography_value: str | None,
        overall_delivery_status: str | None,
        forecast_window_type: str | None,
        forecast_window_start,
        forecast_window_end,
    ) -> list[ThresholdAlertEventSummaryRead]:
        events = self.repository.list_events(
            service_category=service_category,
            geography_value=geography_value,
            overall_delivery_status=overall_delivery_status,
            forecast_window_type=forecast_window_type,
            forecast_window_start=forecast_window_start,
            forecast_window_end=forecast_window_end,
        )
        return [
            ThresholdAlertEventSummaryRead(
                notificationEventId=row.notification_event_id,
                serviceCategory=row.service_category,
                geographyType=row.geography_type,
                geographyValue=row.geography_value,
                forecastWindowType=row.forecast_window_type,
                forecastWindowStart=row.forecast_window_start,
                forecastWindowEnd=row.forecast_window_end,
                forecastValue=float(row.forecast_value),
                thresholdValue=float(row.threshold_value),
                overallDeliveryStatus=row.overall_delivery_status,
                createdAt=row.created_at,
            )
            for row in events
        ]

    def get_event(self, notification_event_id: str) -> ThresholdAlertEventRead | None:
        row = self.repository.get_event(notification_event_id)
        if row is None:
            return None
        attempts = self.repository.list_channel_attempts(notification_event_id)
        failed_count = sum(1 for item in attempts if item.status == "failed")
        return ThresholdAlertEventRead(
            notificationEventId=row.notification_event_id,
            thresholdEvaluationRunId=row.threshold_evaluation_run_id,
            thresholdConfigurationId=row.threshold_configuration_id,
            serviceCategory=row.service_category,
            geographyType=row.geography_type,
            geographyValue=row.geography_value,
            forecastWindowType=row.forecast_window_type,
            forecastWindowStart=row.forecast_window_start,
            forecastWindowEnd=row.forecast_window_end,
            forecastValue=float(row.forecast_value),
            thresholdValue=float(row.threshold_value),
            overallDeliveryStatus=row.overall_delivery_status,
            followUpReason=row.follow_up_reason,
            createdAt=row.created_at,
            deliveredAt=row.delivered_at,
            failedChannelCount=failed_count,
            channelAttempts=[
                NotificationChannelAttemptRead(
                    channelType=item.channel_type,
                    attemptNumber=item.attempt_number,
                    attemptedAt=item.attempted_at,
                    status=item.status,
                    failureReason=item.failure_reason,
                    providerReference=item.provider_reference,
                )
                for item in attempts
            ],
        )
