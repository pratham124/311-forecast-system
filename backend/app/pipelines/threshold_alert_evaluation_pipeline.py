from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging

from app.core.logging import summarize_threshold_alert_event, summarize_threshold_alert_success, summarize_threshold_alert_warning
from app.repositories.notification_event_repository import NotificationEventRepository
from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository
from app.repositories.threshold_evaluation_repository import ThresholdEvaluationRepository
from app.repositories.threshold_state_repository import ThresholdStateRepository
from app.services.forecast_scope_service import ForecastScopeService
from app.services.notification_delivery_service import NotificationDeliveryService
from app.services.threshold_alert_service import ThresholdAlertService


@dataclass
class ThresholdAlertEvaluationPipeline:
    scope_service: ForecastScopeService
    configuration_repository: ThresholdConfigurationRepository
    evaluation_repository: ThresholdEvaluationRepository
    threshold_state_repository: ThresholdStateRepository
    notification_repository: NotificationEventRepository
    alert_service: ThresholdAlertService
    notification_delivery_service: NotificationDeliveryService
    logger: logging.Logger | None = None

    def __post_init__(self) -> None:
        self.logger = self.logger or logging.getLogger("forecast_alerts.pipeline")

    def run(self, *, forecast_reference_id: str, forecast_product: str, trigger_source: str, service_category: str | None = None):
        run = self.evaluation_repository.create_run(
            forecast_version_reference=forecast_reference_id,
            forecast_product=forecast_product,
            trigger_source=trigger_source,
        )
        self.logger.info(
            "%s",
            summarize_threshold_alert_success(
                "threshold_alerts.evaluation_started",
                threshold_evaluation_run_id=run.threshold_evaluation_run_id,
                forecast_product=forecast_product,
                trigger_source=trigger_source,
            ),
        )
        scopes = self.scope_service.list_scopes(
            forecast_reference_id=forecast_reference_id,
            forecast_product=forecast_product,
            service_category=service_category,
        )
        evaluated_scope_count = 0
        alert_created_count = 0
        for scope in scopes:
            evaluated_scope_count += 1
            rule = self.configuration_repository.find_active_threshold(
                service_category=scope.service_category,
                forecast_window_type=scope.forecast_window_type,
            )
            if rule is None:
                self.logger.info(
                    "%s",
                    summarize_threshold_alert_warning(
                        "threshold_alerts.configuration_missing",
                        threshold_evaluation_run_id=run.threshold_evaluation_run_id,
                        service_category=scope.service_category,
                        geography_value=scope.geography_value,
                        forecast_window_type=scope.forecast_window_type,
                    ),
                )
                self.evaluation_repository.record_scope_evaluation(
                    threshold_evaluation_run_id=run.threshold_evaluation_run_id,
                    threshold_configuration_id=None,
                    service_category=scope.service_category,
                    geography_type=scope.geography_type,
                    geography_value=scope.geography_value,
                    forecast_window_type=scope.forecast_window_type,
                    forecast_window_start=scope.forecast_window_start,
                    forecast_window_end=scope.forecast_window_end,
                    forecast_bucket_value=scope.forecast_bucket_value,
                    threshold_value=None,
                    outcome="configuration_missing",
                    notification_event_id=None,
                    recorded_at=datetime.utcnow(),
                )
                continue
            threshold_value = float(rule.configuration.threshold_value)
            state = self.threshold_state_repository.get_state(
                service_category=scope.service_category,
                geography_type=scope.geography_type,
                geography_value=scope.geography_value,
                forecast_window_type=scope.forecast_window_type,
                forecast_window_start=scope.forecast_window_start,
                forecast_window_end=scope.forecast_window_end,
            )
            current_state = state.current_state if state else None
            should_alert = self.alert_service.should_alert(
                current_state=current_state,
                forecast_value=scope.forecast_bucket_value,
                threshold_value=threshold_value,
            )
            is_exceeded = self.alert_service.is_exceeded(
                forecast_value=scope.forecast_bucket_value,
                threshold_value=threshold_value,
            )
            next_state = self.alert_service.next_state(
                forecast_value=scope.forecast_bucket_value,
                threshold_value=threshold_value,
            )
            notification_event_id = None
            outcome = "below_or_equal"
            last_notification_event_id = None
            if is_exceeded:
                outcome = "exceeded_suppressed"
            if should_alert:
                delivery = self.notification_delivery_service.deliver(
                    channels=rule.notification_channels,
                    payload={
                        "serviceCategory": scope.service_category,
                        "geographyValue": scope.geography_value,
                        "forecastValue": scope.forecast_bucket_value,
                        "thresholdValue": threshold_value,
                    },
                )
                event = self.notification_repository.create_event(
                    threshold_evaluation_run_id=run.threshold_evaluation_run_id,
                    threshold_configuration_id=rule.configuration.threshold_configuration_id,
                    service_category=scope.service_category,
                    geography_type=scope.geography_type,
                    geography_value=scope.geography_value,
                    forecast_window_start=scope.forecast_window_start,
                    forecast_window_end=scope.forecast_window_end,
                    forecast_window_type=scope.forecast_window_type,
                    forecast_value=scope.forecast_bucket_value,
                    threshold_value=threshold_value,
                    overall_delivery_status=delivery.overall_delivery_status,
                    created_at=datetime.utcnow(),
                    delivered_at=delivery.delivered_at,
                    follow_up_reason=delivery.follow_up_reason,
                )
                for index, attempt in enumerate(delivery.attempts, start=1):
                    self.notification_repository.add_attempt(
                        notification_event_id=event.notification_event_id,
                        channel_type=attempt.channel_type,
                        attempt_number=index,
                        attempted_at=datetime.utcnow(),
                        status=attempt.status,
                        failure_reason=attempt.failure_reason,
                        provider_reference=attempt.provider_reference,
                    )
                notification_event_id = event.notification_event_id
                last_notification_event_id = event.notification_event_id
                alert_created_count += 1
                outcome = (
                    "delivery_failed"
                    if delivery.overall_delivery_status in {"retry_pending", "manual_review_required"}
                    else "exceeded_alert_created"
                )
            self.threshold_state_repository.reconcile_state(
                threshold_configuration_id=rule.configuration.threshold_configuration_id,
                service_category=scope.service_category,
                geography_type=scope.geography_type,
                geography_value=scope.geography_value,
                forecast_window_type=scope.forecast_window_type,
                forecast_window_start=scope.forecast_window_start,
                forecast_window_end=scope.forecast_window_end,
                current_state=next_state,
                last_forecast_bucket_value=scope.forecast_bucket_value,
                last_threshold_value=threshold_value,
                last_evaluated_at=datetime.utcnow(),
                last_notification_event_id=last_notification_event_id,
            )
            self.evaluation_repository.record_scope_evaluation(
                threshold_evaluation_run_id=run.threshold_evaluation_run_id,
                threshold_configuration_id=rule.configuration.threshold_configuration_id,
                service_category=scope.service_category,
                geography_type=scope.geography_type,
                geography_value=scope.geography_value,
                forecast_window_type=scope.forecast_window_type,
                forecast_window_start=scope.forecast_window_start,
                forecast_window_end=scope.forecast_window_end,
                forecast_bucket_value=scope.forecast_bucket_value,
                threshold_value=threshold_value,
                outcome=outcome,
                notification_event_id=notification_event_id,
                recorded_at=datetime.utcnow(),
            )
            self.logger.info(
                "%s",
                summarize_threshold_alert_event(
                    "threshold_alerts.scope_evaluated",
                    threshold_evaluation_run_id=run.threshold_evaluation_run_id,
                    service_category=scope.service_category,
                    geography_value=scope.geography_value,
                    forecast_window_type=scope.forecast_window_type,
                    outcome=outcome,
                ),
            )
        completed_run = self.evaluation_repository.finalize_run(
            run.threshold_evaluation_run_id,
            status="completed",
            evaluated_scope_count=evaluated_scope_count,
            alert_created_count=alert_created_count,
        )
        self.logger.info(
            "%s",
            summarize_threshold_alert_success(
                "threshold_alerts.evaluation_completed",
                threshold_evaluation_run_id=run.threshold_evaluation_run_id,
                evaluated_scope_count=evaluated_scope_count,
                alert_created_count=alert_created_count,
            ),
        )
        return completed_run
