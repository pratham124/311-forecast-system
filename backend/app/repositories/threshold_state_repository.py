from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ThresholdState


class ThresholdStateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

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

    def reconcile_state(
        self,
        *,
        threshold_configuration_id: str,
        service_category: str,
        geography_type: str | None,
        geography_value: str | None,
        forecast_window_type: str,
        forecast_window_start: datetime,
        forecast_window_end: datetime,
        current_state: str,
        last_forecast_bucket_value: float,
        last_threshold_value: float,
        last_evaluated_at: datetime,
        last_notification_event_id: str | None,
    ) -> ThresholdState:
        state = self.get_state(
            service_category=service_category,
            geography_type=geography_type,
            geography_value=geography_value,
            forecast_window_type=forecast_window_type,
            forecast_window_start=forecast_window_start,
            forecast_window_end=forecast_window_end,
        )
        if state is None:
            state = ThresholdState(
                threshold_configuration_id=threshold_configuration_id,
                service_category=service_category,
                geography_type=geography_type,
                geography_value=geography_value,
                forecast_window_type=forecast_window_type,
                forecast_window_start=forecast_window_start,
                forecast_window_end=forecast_window_end,
                current_state=current_state,
                last_forecast_bucket_value=last_forecast_bucket_value,
                last_threshold_value=last_threshold_value,
                last_evaluated_at=last_evaluated_at,
                last_notification_event_id=last_notification_event_id,
            )
            self.session.add(state)
        else:
            state.threshold_configuration_id = threshold_configuration_id
            state.current_state = current_state
            state.last_forecast_bucket_value = last_forecast_bucket_value
            state.last_threshold_value = last_threshold_value
            state.last_evaluated_at = last_evaluated_at
            state.last_notification_event_id = last_notification_event_id
        self.session.flush()
        return state
