from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.threshold_alert_models import ThresholdState


class ThresholdStateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_state(
        self,
        *,
        service_category: str,
        geography_value: str | None,
        forecast_window_type: str,
        forecast_window_start: datetime,
        forecast_window_end: datetime,
    ) -> ThresholdState | None:
        statement = (
            select(ThresholdState)
            .where(
                ThresholdState.service_category == service_category,
                ThresholdState.geography_value == geography_value,
                ThresholdState.forecast_window_type == forecast_window_type,
                ThresholdState.forecast_window_start == forecast_window_start,
                ThresholdState.forecast_window_end == forecast_window_end,
            )
            .limit(1)
        )
        return self.session.scalar(statement)

    def upsert_state(
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
        last_notification_event_id: str | None,
    ) -> ThresholdState:
        existing = self.find_state(
            service_category=service_category,
            geography_value=geography_value,
            forecast_window_type=forecast_window_type,
            forecast_window_start=forecast_window_start,
            forecast_window_end=forecast_window_end,
        )
        if existing is None:
            existing = ThresholdState(
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
                last_notification_event_id=last_notification_event_id,
                last_evaluated_at=datetime.utcnow(),
            )
            self.session.add(existing)
        else:
            existing.threshold_configuration_id = threshold_configuration_id
            existing.service_category = service_category
            existing.geography_type = geography_type
            existing.geography_value = geography_value
            existing.forecast_window_type = forecast_window_type
            existing.forecast_window_start = forecast_window_start
            existing.forecast_window_end = forecast_window_end
            existing.current_state = current_state
            existing.last_forecast_bucket_value = last_forecast_bucket_value
            existing.last_threshold_value = last_threshold_value
            existing.last_notification_event_id = last_notification_event_id
            existing.last_evaluated_at = datetime.utcnow()
        self.session.flush()
        return existing
