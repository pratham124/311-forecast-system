from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SurgeState


class SurgeStateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_state(self, *, service_category: str, forecast_product: str = "daily") -> SurgeState | None:
        statement = select(SurgeState).where(
            SurgeState.service_category == service_category,
            SurgeState.forecast_product == forecast_product,
        )
        return self.session.scalar(statement)

    def reconcile_state(
        self,
        *,
        surge_detection_configuration_id: str,
        service_category: str,
        current_state: str,
        notification_armed: bool,
        active_since: datetime | None,
        returned_to_normal_at: datetime | None,
        last_surge_candidate_id: str | None,
        last_confirmation_outcome_id: str | None,
        last_notification_event_id: str | None,
        last_evaluated_at: datetime,
    ) -> SurgeState:
        state = self.get_state(service_category=service_category)
        if state is None:
            state = SurgeState(
                surge_detection_configuration_id=surge_detection_configuration_id,
                service_category=service_category,
                forecast_product="daily",
                current_state=current_state,
                notification_armed=notification_armed,
                active_since=active_since,
                returned_to_normal_at=returned_to_normal_at,
                last_surge_candidate_id=last_surge_candidate_id,
                last_confirmation_outcome_id=last_confirmation_outcome_id,
                last_notification_event_id=last_notification_event_id,
                last_evaluated_at=last_evaluated_at,
            )
            self.session.add(state)
        else:
            state.surge_detection_configuration_id = surge_detection_configuration_id
            state.current_state = current_state
            state.notification_armed = notification_armed
            state.active_since = active_since
            state.returned_to_normal_at = returned_to_normal_at
            state.last_surge_candidate_id = last_surge_candidate_id
            state.last_confirmation_outcome_id = last_confirmation_outcome_id
            state.last_notification_event_id = last_notification_event_id
            state.last_evaluated_at = last_evaluated_at
        self.session.flush()
        return state
