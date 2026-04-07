from __future__ import annotations

import logging

from app.clients.notification_service import NotificationServiceClient
from app.core.logging import summarize_status
from app.repositories.notification_event_repository import NotificationEventRepository
from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository
from app.repositories.threshold_evaluation_repository import ThresholdEvaluationRepository
from app.repositories.threshold_state_repository import ThresholdStateRepository
from app.services.forecast_scope_service import ForecastScopeService
from app.services.notification_delivery_service import NotificationDeliveryService
from app.services.threshold_alert_service import ThresholdAlertService
from app.services.threshold_selection_service import ThresholdSelectionService


class ThresholdAlertEvaluationPipeline:
    def __init__(
        self,
        *,
        forecast_scope_service: ForecastScopeService,
        threshold_configuration_repository: ThresholdConfigurationRepository,
        threshold_evaluation_repository: ThresholdEvaluationRepository,
        threshold_state_repository: ThresholdStateRepository,
        notification_event_repository: NotificationEventRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        self.forecast_scope_service = forecast_scope_service
        self.threshold_configuration_repository = threshold_configuration_repository
        self.threshold_evaluation_repository = threshold_evaluation_repository
        self.threshold_state_repository = threshold_state_repository
        self.notification_event_repository = notification_event_repository
        self.threshold_selection_service = ThresholdSelectionService(threshold_configuration_repository)
        self.threshold_alert_service = ThresholdAlertService()
        self.notification_delivery_service = NotificationDeliveryService(NotificationServiceClient())
        self.logger = logger or logging.getLogger("threshold_alert.pipeline")

    def evaluate(
        self,
        *,
        forecast_reference_id: str,
        forecast_product: str,
        trigger_source: str,
        forecast_run_id: str | None = None,
        weekly_forecast_run_id: str | None = None,
    ) -> str:
        run = self.threshold_evaluation_repository.create_run(
            forecast_version_reference=forecast_reference_id,
            forecast_product=forecast_product,
            trigger_source=trigger_source,
            forecast_run_id=forecast_run_id,
            weekly_forecast_run_id=weekly_forecast_run_id,
        )

        scopes = self.forecast_scope_service.list_scopes(
            forecast_product=forecast_product,
            forecast_reference_id=forecast_reference_id,
        )
        alert_count = 0

        for scope in scopes:
            threshold = self.threshold_selection_service.resolve(
                service_category=scope.service_category,
                geography_value=scope.geography_value,
                forecast_window_type=scope.forecast_window_type,
            )
            if threshold is None:
                self.threshold_evaluation_repository.record_scope_evaluation(
                    threshold_evaluation_run_id=run.threshold_evaluation_run_id,
                    threshold_configuration_id=None,
                    service_category=scope.service_category,
                    geography_type=scope.geography_type,
                    geography_value=scope.geography_value,
                    forecast_window_type=scope.forecast_window_type,
                    forecast_window_start=scope.forecast_window_start,
                    forecast_window_end=scope.forecast_window_end,
                    forecast_bucket_value=scope.forecast_value,
                    threshold_value=None,
                    outcome="configuration_missing",
                    notification_event_id=None,
                )
                continue

            state = self.threshold_state_repository.find_state(
                service_category=scope.service_category,
                geography_value=scope.geography_value,
                forecast_window_type=scope.forecast_window_type,
                forecast_window_start=scope.forecast_window_start,
                forecast_window_end=scope.forecast_window_end,
            )
            decision = self.threshold_alert_service.evaluate(
                forecast_value=scope.forecast_value,
                threshold_value=float(threshold.threshold_value),
                current_state=state.current_state if state else None,
            )

            notification_event_id = None
            outcome = decision.outcome
            if decision.should_create_alert:
                channels = self.threshold_configuration_repository.parse_channels(threshold)
                delivery = self.notification_delivery_service.deliver(
                    channels=channels,
                    message=(
                        f"{scope.service_category} forecast {scope.forecast_value:.2f} exceeded "
                        f"threshold {float(threshold.threshold_value):.2f}"
                    ),
                )
                event = self.notification_event_repository.create_event(
                    threshold_evaluation_run_id=run.threshold_evaluation_run_id,
                    threshold_configuration_id=threshold.threshold_configuration_id,
                    service_category=scope.service_category,
                    geography_type=scope.geography_type,
                    geography_value=scope.geography_value,
                    forecast_window_start=scope.forecast_window_start,
                    forecast_window_end=scope.forecast_window_end,
                    forecast_window_type=scope.forecast_window_type,
                    forecast_value=scope.forecast_value,
                    threshold_value=float(threshold.threshold_value),
                    overall_delivery_status=delivery.overall_delivery_status,
                    follow_up_reason=delivery.follow_up_reason,
                    delivered_at=delivery.delivered_at,
                )
                for attempt in delivery.attempts:
                    self.notification_event_repository.add_channel_attempt(
                        notification_event_id=event.notification_event_id,
                        channel_type=str(attempt["channel_type"]),
                        attempt_number=int(attempt["attempt_number"]),
                        status=str(attempt["status"]),
                        failure_reason=str(attempt["failure_reason"]) if attempt["failure_reason"] else None,
                        provider_reference=str(attempt["provider_reference"]) if attempt["provider_reference"] else None,
                    )
                notification_event_id = event.notification_event_id
                alert_count += 1
                if delivery.overall_delivery_status in {"manual_review_required", "retry_pending"}:
                    outcome = "delivery_failed"

            self.threshold_state_repository.upsert_state(
                threshold_configuration_id=threshold.threshold_configuration_id,
                service_category=scope.service_category,
                geography_type=scope.geography_type,
                geography_value=scope.geography_value,
                forecast_window_type=scope.forecast_window_type,
                forecast_window_start=scope.forecast_window_start,
                forecast_window_end=scope.forecast_window_end,
                current_state=decision.next_state,
                last_forecast_bucket_value=scope.forecast_value,
                last_threshold_value=float(threshold.threshold_value),
                last_notification_event_id=notification_event_id,
            )

            self.threshold_evaluation_repository.record_scope_evaluation(
                threshold_evaluation_run_id=run.threshold_evaluation_run_id,
                threshold_configuration_id=threshold.threshold_configuration_id,
                service_category=scope.service_category,
                geography_type=scope.geography_type,
                geography_value=scope.geography_value,
                forecast_window_type=scope.forecast_window_type,
                forecast_window_start=scope.forecast_window_start,
                forecast_window_end=scope.forecast_window_end,
                forecast_bucket_value=scope.forecast_value,
                threshold_value=float(threshold.threshold_value),
                outcome=outcome,
                notification_event_id=notification_event_id,
            )

        self.threshold_evaluation_repository.complete_run(
            run.threshold_evaluation_run_id,
            evaluated_scope_count=len(scopes),
            alert_created_count=alert_count,
            status="completed",
        )
        self.logger.info(
            "%s",
            summarize_status(
                "threshold_alert.evaluation.completed",
                threshold_evaluation_run_id=run.threshold_evaluation_run_id,
                evaluated_scope_count=len(scopes),
                alert_created_count=alert_count,
                forecast_product=forecast_product,
            ),
        )
        return run.threshold_evaluation_run_id
