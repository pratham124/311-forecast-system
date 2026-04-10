from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import NotificationChannelAttempt, NotificationEvent


@dataclass
class NotificationEventBundle:
    event: NotificationEvent
    attempts: list[NotificationChannelAttempt]


class NotificationEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_event(self, **kwargs) -> NotificationEvent:
        event = NotificationEvent(**kwargs)
        self.session.add(event)
        self.session.flush()
        return event

    def add_attempt(self, **kwargs) -> NotificationChannelAttempt:
        attempt = NotificationChannelAttempt(**kwargs)
        self.session.add(attempt)
        self.session.flush()
        return attempt

    def list_events(
        self,
        *,
        service_category: str | None = None,
        geography_value: str | None = None,
        overall_delivery_status: str | None = None,
        forecast_window_type: str | None = None,
    ) -> list[NotificationEvent]:
        statement = select(NotificationEvent).order_by(NotificationEvent.created_at.desc())
        if service_category:
            statement = statement.where(NotificationEvent.service_category == service_category)
        if geography_value:
            statement = statement.where(NotificationEvent.geography_value == geography_value)
        if overall_delivery_status:
            statement = statement.where(NotificationEvent.overall_delivery_status == overall_delivery_status)
        if forecast_window_type:
            statement = statement.where(NotificationEvent.forecast_window_type == forecast_window_type)
        return list(self.session.scalars(statement))

    def get_event_bundle(self, notification_event_id: str) -> NotificationEventBundle | None:
        event = self.session.get(NotificationEvent, notification_event_id)
        if event is None:
            return None
        attempts = list(
            self.session.scalars(
                select(NotificationChannelAttempt)
                .where(NotificationChannelAttempt.notification_event_id == notification_event_id)
                .order_by(NotificationChannelAttempt.attempted_at.asc(), NotificationChannelAttempt.channel_type.asc())
            )
        )
        return NotificationEventBundle(event=event, attempts=attempts)
