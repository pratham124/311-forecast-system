from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import ThresholdConfiguration


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ThresholdRule:
    configuration: ThresholdConfiguration
    notification_channels: list[str]


class ThresholdConfigurationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_configuration(
        self,
        *,
        service_category: str,
        forecast_window_type: str,
        threshold_value: float,
        notification_channels: list[str],
        operational_manager_id: str,
        status: str = "active",
        effective_from: datetime | None = None,
        effective_to: datetime | None = None,
    ) -> ThresholdConfiguration:
        configuration = ThresholdConfiguration(
            service_category=service_category,
            geography_type=None,
            geography_value=None,
            forecast_window_type=forecast_window_type,
            threshold_value=threshold_value,
            notification_channels_json=json.dumps(notification_channels),
            operational_manager_id=operational_manager_id,
            status=status,
            effective_from=effective_from or _utcnow(),
            effective_to=effective_to,
        )
        self.session.add(configuration)
        self.session.flush()
        return configuration

    def list_configurations(self, *, include_inactive: bool = False) -> list[ThresholdRule]:
        statement = select(ThresholdConfiguration)
        if not include_inactive:
            statement = statement.where(ThresholdConfiguration.status == "active")
        statement = statement.order_by(
            ThresholdConfiguration.service_category.asc(),
            ThresholdConfiguration.forecast_window_type.asc(),
            ThresholdConfiguration.effective_from.desc(),
        )
        return [
            ThresholdRule(configuration=row, notification_channels=json.loads(row.notification_channels_json))
            for row in self.session.scalars(statement)
        ]

    def list_active_configurations(self) -> list[ThresholdRule]:
        """Return all active configurations for bulk pre-loading."""
        return self.list_configurations(include_inactive=False)

    def get_configuration(self, threshold_configuration_id: str) -> ThresholdRule | None:
        configuration = self.session.get(ThresholdConfiguration, threshold_configuration_id)
        if configuration is None:
            return None
        return ThresholdRule(configuration=configuration, notification_channels=json.loads(configuration.notification_channels_json))

    def update_configuration(
        self,
        threshold_configuration_id: str,
        *,
        service_category: str,
        forecast_window_type: str,
        threshold_value: float,
        notification_channels: list[str],
    ) -> ThresholdConfiguration | None:
        configuration = self.session.get(ThresholdConfiguration, threshold_configuration_id)
        if configuration is None:
            return None
        configuration.service_category = service_category
        configuration.forecast_window_type = forecast_window_type
        configuration.threshold_value = threshold_value
        configuration.notification_channels_json = json.dumps(notification_channels)
        configuration.geography_type = None
        configuration.geography_value = None
        if configuration.status != "inactive":
            configuration.status = "active"
            configuration.effective_to = None
        self.session.flush()
        return configuration

    def deactivate_configuration(self, threshold_configuration_id: str) -> ThresholdConfiguration | None:
        configuration = self.session.get(ThresholdConfiguration, threshold_configuration_id)
        if configuration is None:
            return None
        configuration.status = "inactive"
        configuration.effective_to = configuration.effective_to or _utcnow()
        self.session.flush()
        return configuration

    def find_active_threshold(
        self,
        *,
        service_category: str,
        forecast_window_type: str,
        at_time: datetime | None = None,
    ) -> ThresholdRule | None:
        at_time = at_time or _utcnow()
        statement = (
            select(ThresholdConfiguration)
            .where(
                ThresholdConfiguration.service_category == service_category,
                ThresholdConfiguration.forecast_window_type == forecast_window_type,
                ThresholdConfiguration.status == "active",
                ThresholdConfiguration.effective_from <= at_time,
                or_(ThresholdConfiguration.effective_to.is_(None), ThresholdConfiguration.effective_to > at_time),
            )
            .order_by(ThresholdConfiguration.effective_from.desc())
        )
        rows = list(self.session.scalars(statement))
        for row in rows:
            if row.geography_value is None:
                return ThresholdRule(configuration=row, notification_channels=json.loads(row.notification_channels_json))
        return None
