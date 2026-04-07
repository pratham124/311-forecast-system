from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.threshold_alert_models import ThresholdEvaluationRun, ThresholdScopeEvaluation


class ThresholdEvaluationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_run(
        self,
        *,
        forecast_version_reference: str,
        forecast_product: str,
        trigger_source: str,
        forecast_run_id: str | None = None,
        weekly_forecast_run_id: str | None = None,
    ) -> ThresholdEvaluationRun:
        run = ThresholdEvaluationRun(
            forecast_version_reference=forecast_version_reference,
            forecast_product=forecast_product,
            trigger_source=trigger_source,
            forecast_run_id=forecast_run_id,
            weekly_forecast_run_id=weekly_forecast_run_id,
        )
        self.session.add(run)
        self.session.flush()
        return run

    def get_run(self, threshold_evaluation_run_id: str) -> ThresholdEvaluationRun | None:
        return self.session.get(ThresholdEvaluationRun, threshold_evaluation_run_id)

    def record_scope_evaluation(
        self,
        *,
        threshold_evaluation_run_id: str,
        threshold_configuration_id: str | None,
        service_category: str,
        geography_type: str | None,
        geography_value: str | None,
        forecast_window_type: str,
        forecast_window_start: datetime,
        forecast_window_end: datetime,
        forecast_bucket_value: float,
        threshold_value: float | None,
        outcome: str,
        notification_event_id: str | None,
    ) -> ThresholdScopeEvaluation:
        row = ThresholdScopeEvaluation(
            threshold_evaluation_run_id=threshold_evaluation_run_id,
            threshold_configuration_id=threshold_configuration_id,
            service_category=service_category,
            geography_type=geography_type,
            geography_value=geography_value,
            forecast_window_type=forecast_window_type,
            forecast_window_start=forecast_window_start,
            forecast_window_end=forecast_window_end,
            forecast_bucket_value=forecast_bucket_value,
            threshold_value=threshold_value,
            outcome=outcome,
            notification_event_id=notification_event_id,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def complete_run(
        self,
        threshold_evaluation_run_id: str,
        *,
        evaluated_scope_count: int,
        alert_created_count: int,
        status: str = "completed",
        failure_summary: str | None = None,
    ) -> ThresholdEvaluationRun:
        run = self.get_run(threshold_evaluation_run_id)
        if run is None:
            raise ValueError("Threshold evaluation run not found")
        run.status = status
        run.evaluated_scope_count = evaluated_scope_count
        run.alert_created_count = alert_created_count
        run.failure_summary = failure_summary
        run.completed_at = datetime.utcnow()
        self.session.flush()
        return run

    def list_scope_evaluations(self, threshold_evaluation_run_id: str) -> list[ThresholdScopeEvaluation]:
        statement = (
            select(ThresholdScopeEvaluation)
            .where(ThresholdScopeEvaluation.threshold_evaluation_run_id == threshold_evaluation_run_id)
            .order_by(
                ThresholdScopeEvaluation.forecast_window_start.asc(),
                ThresholdScopeEvaluation.service_category.asc(),
                ThresholdScopeEvaluation.geography_value.asc(),
            )
        )
        return list(self.session.scalars(statement))
