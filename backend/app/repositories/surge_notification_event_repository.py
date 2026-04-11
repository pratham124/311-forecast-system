from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SurgeNotificationChannelAttempt, SurgeNotificationEvent


@dataclass
class SurgeNotificationEventBundle:
    event: SurgeNotificationEvent
    attempts: list[SurgeNotificationChannelAttempt]


class SurgeNotificationEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_event(self, **kwargs) -> SurgeNotificationEvent:
        event = SurgeNotificationEvent(**kwargs)
        self.session.add(event)
        self.session.flush()
        return event

    def add_attempt(self, **kwargs) -> SurgeNotificationChannelAttempt:
        attempt = SurgeNotificationChannelAttempt(**kwargs)
        self.session.add(attempt)
        self.session.flush()
        return attempt

    def list_events(
        self,
        *,
        service_category: str | None = None,
        overall_delivery_status: str | None = None,
    ) -> list[SurgeNotificationEvent]:
        statement = select(SurgeNotificationEvent).order_by(SurgeNotificationEvent.created_at.desc())
        if service_category:
            statement = statement.where(SurgeNotificationEvent.service_category == service_category)
        if overall_delivery_status:
            statement = statement.where(SurgeNotificationEvent.overall_delivery_status == overall_delivery_status)
        return list(self.session.scalars(statement))

    def get_event_bundle(self, surge_notification_event_id: str) -> SurgeNotificationEventBundle | None:
        event = self.session.get(SurgeNotificationEvent, surge_notification_event_id)
        if event is None:
            return None
        attempts = list(
            self.session.scalars(
                select(SurgeNotificationChannelAttempt)
                .where(SurgeNotificationChannelAttempt.surge_notification_event_id == surge_notification_event_id)
                .order_by(
                    SurgeNotificationChannelAttempt.attempted_at.asc(),
                    SurgeNotificationChannelAttempt.channel_type.asc(),
                )
            )
        )
        return SurgeNotificationEventBundle(event=event, attempts=attempts)
