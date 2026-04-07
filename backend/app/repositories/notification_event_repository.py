from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.threshold_alert_models import NotificationChannelAttempt, NotificationEvent


class NotificationEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_event(
        self,
        *,
        threshold_evaluation_run_id: str,
        threshold_configuration_id: str,
        service_category: str,
        geography_type: str | None,
        geography_value: str | None,
        forecast_window_start: datetime,
        forecast_window_end: datetime,
        forecast_window_type: str,
        forecast_value: float,
        threshold_value: float,
        overall_delivery_status: str,
        follow_up_reason: str | None,
        delivered_at: datetime | None,
    ) -> NotificationEvent:
        event = NotificationEvent(
            threshold_evaluation_run_id=threshold_evaluation_run_id,
            threshold_configuration_id=threshold_configuration_id,
            service_category=service_category,
            geography_type=geography_type,
            geography_value=geography_value,
            forecast_window_start=forecast_window_start,
            forecast_window_end=forecast_window_end,
            forecast_window_type=forecast_window_type,
            forecast_value=forecast_value,
            threshold_value=threshold_value,
            overall_delivery_status=overall_delivery_status,
            follow_up_reason=follow_up_reason,
            delivered_at=delivered_at,
        )
        self.session.add(event)
        self.session.flush()
        return event

    def add_channel_attempt(
        self,
        *,
        notification_event_id: str,
        channel_type: str,
        attempt_number: int,
        status: str,
        failure_reason: str | None = None,
        provider_reference: str | None = None,
    ) -> NotificationChannelAttempt:
        row = NotificationChannelAttempt(
            notification_event_id=notification_event_id,
            channel_type=channel_type,
            attempt_number=attempt_number,
            status=status,
            failure_reason=failure_reason,
            provider_reference=provider_reference,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def list_events(
        self,
        *,
        service_category: str | None = None,
        geography_value: str | None = None,
        overall_delivery_status: str | None = None,
        forecast_window_type: str | None = None,
        forecast_window_start: datetime | None = None,
        forecast_window_end: datetime | None = None,
    ) -> list[NotificationEvent]:
        filters = []
        if service_category:
            filters.append(NotificationEvent.service_category == service_category)
        if geography_value:
            filters.append(NotificationEvent.geography_value == geography_value)
        if overall_delivery_status:
            filters.append(NotificationEvent.overall_delivery_status == overall_delivery_status)
        if forecast_window_type:
            filters.append(NotificationEvent.forecast_window_type == forecast_window_type)
        if forecast_window_start:
            filters.append(NotificationEvent.forecast_window_start >= forecast_window_start)
        if forecast_window_end:
            filters.append(NotificationEvent.forecast_window_end <= forecast_window_end)

        statement = select(NotificationEvent)
        if filters:
            statement = statement.where(and_(*filters))
        statement = statement.order_by(NotificationEvent.created_at.desc(), NotificationEvent.notification_event_id.desc())
        return list(self.session.scalars(statement))

    def get_event(self, notification_event_id: str) -> NotificationEvent | None:
        return self.session.get(NotificationEvent, notification_event_id)

    def list_channel_attempts(self, notification_event_id: str) -> list[NotificationChannelAttempt]:
        statement = (
            select(NotificationChannelAttempt)
            .where(NotificationChannelAttempt.notification_event_id == notification_event_id)
            .order_by(NotificationChannelAttempt.attempt_number.asc(), NotificationChannelAttempt.channel_type.asc())
        )
        return list(self.session.scalars(statement))
