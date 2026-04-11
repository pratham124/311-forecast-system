from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging

from app.core.logging import summarize_surge_alert_event, summarize_surge_alert_failure, summarize_surge_alert_success
from app.repositories.surge_configuration_repository import SurgeConfigurationRepository
from app.repositories.surge_evaluation_repository import SurgeEvaluationRepository
from app.repositories.surge_notification_event_repository import SurgeNotificationEventRepository
from app.repositories.surge_state_repository import SurgeStateRepository
from app.services.surge_confirmation_service import SurgeConfirmationService
from app.services.surge_detection_service import SurgeDetectionError, SurgeDetectionService
from app.services.surge_notification_delivery_service import SurgeNotificationDeliveryService
from app.services.surge_scope_service import SurgeScopeService
from app.services.surge_state_service import SurgeStateService


@dataclass
class SurgeAlertEvaluationPipeline:
    scope_service: SurgeScopeService
    configuration_repository: SurgeConfigurationRepository
    evaluation_repository: SurgeEvaluationRepository
    state_repository: SurgeStateRepository
    event_repository: SurgeNotificationEventRepository
    detection_service: SurgeDetectionService
    confirmation_service: SurgeConfirmationService
    state_service: SurgeStateService
    delivery_service: SurgeNotificationDeliveryService
    logger: logging.Logger | None = None

    def __post_init__(self) -> None:
        self.logger = self.logger or logging.getLogger("surge_alerts.pipeline")

    def run(self, *, ingestion_run_id: str, trigger_source: str):
        run = self.evaluation_repository.create_run(ingestion_run_id=ingestion_run_id, trigger_source=trigger_source)
        self.logger.info(
            "%s",
            summarize_surge_alert_success(
                "surge_alerts.evaluation_started",
                surge_evaluation_run_id=run.surge_evaluation_run_id,
                ingestion_run_id=ingestion_run_id,
                trigger_source=trigger_source,
            ),
        )
        evaluated_scope_count = 0
        candidate_count = 0
        confirmed_count = 0
        notification_created_count = 0
        failures: list[str] = []
        try:
            scopes = self.scope_service.list_scopes(ingestion_run_id=ingestion_run_id)

            for scope in scopes:
                evaluated_scope_count += 1
                rule = self.configuration_repository.find_active_configuration(service_category=scope.service_category)
                if rule is None:
                    continue
                state = self.state_repository.get_state(service_category=scope.service_category)
                correlation_id = f"{run.surge_evaluation_run_id}:{scope.service_category}:{int(scope.evaluation_window_start.timestamp())}"
                if scope.forecast_p50_value is None:
                    candidate = self.evaluation_repository.create_candidate(
                        surge_evaluation_run_id=run.surge_evaluation_run_id,
                        surge_detection_configuration_id=rule.configuration.surge_detection_configuration_id,
                        forecast_run_id=scope.forecast_run_id,
                        forecast_version_id=scope.forecast_version_id,
                        service_category=scope.service_category,
                        evaluation_window_start=scope.evaluation_window_start,
                        evaluation_window_end=scope.evaluation_window_end,
                        actual_demand_value=scope.actual_demand_value,
                        forecast_p50_value=None,
                        residual_value=None,
                        residual_z_score=None,
                        percent_above_forecast=None,
                        rolling_baseline_mean=None,
                        rolling_baseline_stddev=None,
                        candidate_status="detector_failed",
                        detected_at=datetime.utcnow(),
                        correlation_id=correlation_id,
                        failure_reason="No active forecast bucket matched the ingestion window",
                    )
                    candidate_count += 1
                    confirmation = self.evaluation_repository.create_confirmation_outcome(
                        surge_candidate_id=candidate.surge_candidate_id,
                        outcome="failed",
                        z_score_check_passed=None,
                        percent_floor_check_passed=None,
                        surge_notification_event_id=None,
                        confirmed_at=datetime.utcnow(),
                        failure_reason=candidate.failure_reason,
                    )
                    transition = self.state_service.transition(state=state, decision_outcome="failed", evaluated_at=datetime.utcnow())
                    self.state_repository.reconcile_state(
                        surge_detection_configuration_id=rule.configuration.surge_detection_configuration_id,
                        service_category=scope.service_category,
                        current_state=transition.current_state,
                        notification_armed=transition.notification_armed,
                        active_since=transition.active_since,
                        returned_to_normal_at=transition.returned_to_normal_at,
                        last_surge_candidate_id=candidate.surge_candidate_id,
                        last_confirmation_outcome_id=confirmation.surge_confirmation_outcome_id,
                        last_notification_event_id=None,
                        last_evaluated_at=datetime.utcnow(),
                    )
                    failures.append(f"{scope.service_category}: missing forecast bucket")
                    continue
                try:
                    metrics = self.detection_service.compute_metrics(
                        service_category=scope.service_category,
                        evaluation_window_start=scope.evaluation_window_start,
                        evaluation_window_end=scope.evaluation_window_end,
                        actual_demand_value=scope.actual_demand_value,
                        forecast_p50_value=scope.forecast_p50_value,
                        rolling_baseline_window_count=rule.configuration.rolling_baseline_window_count,
                    )
                    candidate_status = (
                        "flagged"
                        if metrics.residual_z_score >= float(rule.configuration.z_score_threshold)
                        else "below_candidate_threshold"
                    )
                    candidate = self.evaluation_repository.create_candidate(
                        surge_evaluation_run_id=run.surge_evaluation_run_id,
                        surge_detection_configuration_id=rule.configuration.surge_detection_configuration_id,
                        forecast_run_id=scope.forecast_run_id,
                        forecast_version_id=scope.forecast_version_id,
                        service_category=scope.service_category,
                        evaluation_window_start=scope.evaluation_window_start,
                        evaluation_window_end=scope.evaluation_window_end,
                        actual_demand_value=metrics.actual_demand_value,
                        forecast_p50_value=metrics.forecast_p50_value,
                        residual_value=metrics.residual_value,
                        residual_z_score=metrics.residual_z_score,
                        percent_above_forecast=metrics.percent_above_forecast,
                        rolling_baseline_mean=metrics.rolling_baseline_mean,
                        rolling_baseline_stddev=metrics.rolling_baseline_stddev,
                        candidate_status=candidate_status,
                        detected_at=datetime.utcnow(),
                        correlation_id=correlation_id,
                        failure_reason=None,
                    )
                    candidate_count += 1
                    notification_event = None
                    if candidate_status == "flagged":
                        decision = self.confirmation_service.evaluate(
                            metrics=metrics,
                            z_score_threshold=float(rule.configuration.z_score_threshold),
                            percent_above_forecast_floor=float(rule.configuration.percent_above_forecast_floor),
                            active_surge=state is not None and state.current_state == "active_surge" and not state.notification_armed,
                        )
                        if decision.outcome == "confirmed":
                            confirmed_count += 1
                            delivery = self.delivery_service.deliver(
                                channels=rule.notification_channels,
                                payload={
                                    "serviceCategory": scope.service_category,
                                    "actualDemandValue": metrics.actual_demand_value,
                                    "forecastP50Value": metrics.forecast_p50_value,
                                    "residualValue": metrics.residual_value,
                                    "residualZScore": metrics.residual_z_score,
                                    "percentAboveForecast": metrics.percent_above_forecast,
                                },
                            )
                            notification_event = self.event_repository.create_event(
                                surge_evaluation_run_id=run.surge_evaluation_run_id,
                                surge_candidate_id=candidate.surge_candidate_id,
                                surge_detection_configuration_id=rule.configuration.surge_detection_configuration_id,
                                service_category=scope.service_category,
                                forecast_product="daily",
                                evaluation_window_start=scope.evaluation_window_start,
                                evaluation_window_end=scope.evaluation_window_end,
                                actual_demand_value=metrics.actual_demand_value,
                                forecast_p50_value=metrics.forecast_p50_value,
                                residual_value=metrics.residual_value,
                                residual_z_score=metrics.residual_z_score,
                                percent_above_forecast=metrics.percent_above_forecast,
                                overall_delivery_status=delivery.overall_delivery_status,
                                created_at=datetime.utcnow(),
                                delivered_at=delivery.delivered_at,
                                follow_up_reason=delivery.follow_up_reason,
                                correlation_id=correlation_id,
                            )
                            for index, attempt in enumerate(delivery.attempts, start=1):
                                self.event_repository.add_attempt(
                                    surge_notification_event_id=notification_event.surge_notification_event_id,
                                    channel_type=attempt.channel_type,
                                    attempt_number=index,
                                    attempted_at=datetime.utcnow(),
                                    status=attempt.status,
                                    failure_reason=attempt.failure_reason,
                                    provider_reference=attempt.provider_reference,
                                )
                            notification_created_count += 1
                        confirmation = self.evaluation_repository.create_confirmation_outcome(
                            surge_candidate_id=candidate.surge_candidate_id,
                            outcome=decision.outcome,
                            z_score_check_passed=decision.z_score_check_passed,
                            percent_floor_check_passed=decision.percent_floor_check_passed,
                            surge_notification_event_id=None if notification_event is None else notification_event.surge_notification_event_id,
                            confirmed_at=datetime.utcnow(),
                            failure_reason=None,
                        )
                        transition = self.state_service.transition(
                            state=state,
                            decision_outcome=decision.outcome,
                            evaluated_at=datetime.utcnow(),
                        )
                        self.state_repository.reconcile_state(
                            surge_detection_configuration_id=rule.configuration.surge_detection_configuration_id,
                            service_category=scope.service_category,
                            current_state=transition.current_state,
                            notification_armed=transition.notification_armed,
                            active_since=transition.active_since,
                            returned_to_normal_at=transition.returned_to_normal_at,
                            last_surge_candidate_id=candidate.surge_candidate_id,
                            last_confirmation_outcome_id=confirmation.surge_confirmation_outcome_id,
                            last_notification_event_id=None if notification_event is None else notification_event.surge_notification_event_id,
                            last_evaluated_at=datetime.utcnow(),
                        )
                        self.logger.info(
                            "%s",
                            summarize_surge_alert_event(
                                "surge_alerts.scope_evaluated",
                                surge_evaluation_run_id=run.surge_evaluation_run_id,
                                service_category=scope.service_category,
                                outcome=decision.outcome,
                            ),
                        )
                    else:
                        transition = self.state_service.transition(
                            state=state,
                            decision_outcome="below_candidate_threshold",
                            evaluated_at=datetime.utcnow(),
                        )
                        self.state_repository.reconcile_state(
                            surge_detection_configuration_id=rule.configuration.surge_detection_configuration_id,
                            service_category=scope.service_category,
                            current_state=transition.current_state,
                            notification_armed=transition.notification_armed,
                            active_since=transition.active_since,
                            returned_to_normal_at=transition.returned_to_normal_at,
                            last_surge_candidate_id=candidate.surge_candidate_id,
                            last_confirmation_outcome_id=None,
                            last_notification_event_id=None,
                            last_evaluated_at=datetime.utcnow(),
                        )
                except SurgeDetectionError as exc:
                    candidate = self.evaluation_repository.create_candidate(
                        surge_evaluation_run_id=run.surge_evaluation_run_id,
                        surge_detection_configuration_id=rule.configuration.surge_detection_configuration_id,
                        forecast_run_id=scope.forecast_run_id,
                        forecast_version_id=scope.forecast_version_id,
                        service_category=scope.service_category,
                        evaluation_window_start=scope.evaluation_window_start,
                        evaluation_window_end=scope.evaluation_window_end,
                        actual_demand_value=scope.actual_demand_value,
                        forecast_p50_value=scope.forecast_p50_value,
                        residual_value=None,
                        residual_z_score=None,
                        percent_above_forecast=None,
                        rolling_baseline_mean=None,
                        rolling_baseline_stddev=None,
                        candidate_status="detector_failed",
                        detected_at=datetime.utcnow(),
                        correlation_id=correlation_id,
                        failure_reason=str(exc),
                    )
                    candidate_count += 1
                    confirmation = self.evaluation_repository.create_confirmation_outcome(
                        surge_candidate_id=candidate.surge_candidate_id,
                        outcome="failed",
                        z_score_check_passed=None,
                        percent_floor_check_passed=None,
                        surge_notification_event_id=None,
                        confirmed_at=datetime.utcnow(),
                        failure_reason=str(exc),
                    )
                    transition = self.state_service.transition(state=state, decision_outcome="failed", evaluated_at=datetime.utcnow())
                    self.state_repository.reconcile_state(
                        surge_detection_configuration_id=rule.configuration.surge_detection_configuration_id,
                        service_category=scope.service_category,
                        current_state=transition.current_state,
                        notification_armed=transition.notification_armed,
                        active_since=transition.active_since,
                        returned_to_normal_at=transition.returned_to_normal_at,
                        last_surge_candidate_id=candidate.surge_candidate_id,
                        last_confirmation_outcome_id=confirmation.surge_confirmation_outcome_id,
                        last_notification_event_id=None,
                        last_evaluated_at=datetime.utcnow(),
                    )
                    failures.append(f"{scope.service_category}: {exc}")
        except Exception as exc:  # noqa: BLE001
            failures.append(str(exc))
            self.logger.warning(
                "%s",
                summarize_surge_alert_failure(
                    "surge_alerts.evaluation_aborted",
                    surge_evaluation_run_id=run.surge_evaluation_run_id,
                    ingestion_run_id=ingestion_run_id,
                    failure_summary=str(exc),
                ),
            )

        completed = self.evaluation_repository.finalize_run(
            run.surge_evaluation_run_id,
            status="completed_with_failures" if failures else "completed",
            evaluated_scope_count=evaluated_scope_count,
            candidate_count=candidate_count,
            confirmed_count=confirmed_count,
            notification_created_count=notification_created_count,
            failure_summary="; ".join(failures) if failures else None,
        )
        self.logger.info(
            "%s",
            summarize_surge_alert_success(
                "surge_alerts.evaluation_completed",
                surge_evaluation_run_id=run.surge_evaluation_run_id,
                evaluated_scope_count=evaluated_scope_count,
                candidate_count=candidate_count,
                confirmed_count=confirmed_count,
                notification_created_count=notification_created_count,
            ),
        )
        if failures:
            self.logger.warning(
                "%s",
                summarize_surge_alert_failure(
                    "surge_alerts.evaluation_failures",
                    surge_evaluation_run_id=run.surge_evaluation_run_id,
                    failure_summary=completed.failure_summary,
                ),
            )
        return completed
