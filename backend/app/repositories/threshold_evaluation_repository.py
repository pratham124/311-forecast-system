from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ThresholdEvaluationRun, ThresholdScopeEvaluation, ThresholdState


class ThresholdEvaluationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_run(self, threshold_evaluation_run_id: str) -> ThresholdEvaluationRun | None:
        return self.session.get(ThresholdEvaluationRun, threshold_evaluation_run_id)

    def create_run(
        self,
        *,
        forecast_version_reference: str,
        forecast_product: str,
        trigger_source: str,
        forecast_run_id: str | None = None,
    ) -> ThresholdEvaluationRun:
        run = ThresholdEvaluationRun(
            forecast_version_reference=forecast_version_reference,
            forecast_product=forecast_product,
            trigger_source=trigger_source,
            forecast_run_id=forecast_run_id,
            status="running",
        )
        self.session.add(run)
        self.session.flush()
        return run

    def record_scope_evaluation(self, **kwargs) -> ThresholdScopeEvaluation:
        evaluation = ThresholdScopeEvaluation(**kwargs)
        self.session.add(evaluation)
        self.session.flush()
        return evaluation

    def record_scope_evaluations_batch(self, evaluations: list[dict]) -> None:
        """Batch-insert all scope evaluations in a single flush."""
        if not evaluations:
            return
        self.session.add_all([ThresholdScopeEvaluation(**e) for e in evaluations])
        self.session.flush()

    def get_state(
        self,
        *,
        service_category: str,
        geography_type: str | None,
        geography_value: str | None,
        forecast_window_type: str,
        forecast_window_start: datetime,
        forecast_window_end: datetime,
    ) -> ThresholdState | None:
        statement = select(ThresholdState).where(
            ThresholdState.service_category == service_category,
            ThresholdState.geography_type == geography_type,
            ThresholdState.geography_value == geography_value,
            ThresholdState.forecast_window_type == forecast_window_type,
            ThresholdState.forecast_window_start == forecast_window_start,
            ThresholdState.forecast_window_end == forecast_window_end,
        )
        return self.session.scalar(statement)

    def upsert_state(self, **kwargs) -> ThresholdState:
        state = self.get_state(
            service_category=kwargs["service_category"],
            geography_type=kwargs["geography_type"],
            geography_value=kwargs["geography_value"],
            forecast_window_type=kwargs["forecast_window_type"],
            forecast_window_start=kwargs["forecast_window_start"],
            forecast_window_end=kwargs["forecast_window_end"],
        )
        if state is None:
            state = ThresholdState(**kwargs)
            self.session.add(state)
        else:
            state.threshold_configuration_id = kwargs["threshold_configuration_id"]
            state.current_state = kwargs["current_state"]
            state.last_forecast_bucket_value = kwargs["last_forecast_bucket_value"]
            state.last_threshold_value = kwargs["last_threshold_value"]
            state.last_evaluated_at = kwargs["last_evaluated_at"]
            state.last_notification_event_id = kwargs["last_notification_event_id"]
        self.session.flush()
        return state

    def finalize_run(
        self,
        run_id: str,
        *,
        status: str,
        evaluated_scope_count: int,
        alert_created_count: int,
        failure_summary: str | None = None,
    ) -> ThresholdEvaluationRun:
        run = self.session.get(ThresholdEvaluationRun, run_id)
        if run is None:
            raise ValueError("Threshold evaluation run not found")
        run.status = status
        run.evaluated_scope_count = evaluated_scope_count
        run.alert_created_count = alert_created_count
        run.failure_summary = failure_summary
        run.completed_at = datetime.utcnow()
        self.session.flush()
        return run
