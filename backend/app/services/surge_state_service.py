from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.models import SurgeState


@dataclass
class SurgeStateTransition:
    current_state: str
    notification_armed: bool
    active_since: datetime | None
    returned_to_normal_at: datetime | None


class SurgeStateService:
    def transition(
        self,
        *,
        state: SurgeState | None,
        decision_outcome: str | None,
        evaluated_at: datetime,
    ) -> SurgeStateTransition:
        current_state = state.current_state if state is not None else "normal"
        active_since = state.active_since if state is not None else None
        returned_to_normal_at = state.returned_to_normal_at if state is not None else None
        if decision_outcome in {"confirmed", "suppressed_active_surge"}:
            return SurgeStateTransition(
                current_state="active_surge",
                notification_armed=False,
                active_since=active_since or evaluated_at,
                returned_to_normal_at=returned_to_normal_at,
            )
        return SurgeStateTransition(
            current_state="normal",
            notification_armed=True,
            active_since=None,
            returned_to_normal_at=evaluated_at,
        )
