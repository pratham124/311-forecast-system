from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import SurgeDetectionConfiguration


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class SurgeRule:
    configuration: SurgeDetectionConfiguration
    notification_channels: list[str]


class SurgeConfigurationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_configuration(
        self,
        *,
        service_category: str,
        z_score_threshold: float,
        percent_above_forecast_floor: float,
        rolling_baseline_window_count: int,
        notification_channels: list[str],
        operational_manager_id: str,
        status: str = "active",
    ) -> SurgeDetectionConfiguration:
        configuration = SurgeDetectionConfiguration(
            service_category=service_category,
            forecast_product="daily",
            z_score_threshold=z_score_threshold,
            percent_above_forecast_floor=percent_above_forecast_floor,
            rolling_baseline_window_count=rolling_baseline_window_count,
            notification_channels_json=json.dumps(notification_channels),
            operational_manager_id=operational_manager_id,
            status=status,
            effective_from=_utcnow(),
        )
        self.session.add(configuration)
        self.session.flush()
        return configuration

    def find_active_configuration(self, *, service_category: str, at_time: datetime | None = None) -> SurgeRule | None:
        at_time = at_time or _utcnow()
        statement = (
            select(SurgeDetectionConfiguration)
            .where(
                SurgeDetectionConfiguration.service_category == service_category,
                SurgeDetectionConfiguration.forecast_product == "daily",
                SurgeDetectionConfiguration.status == "active",
                SurgeDetectionConfiguration.effective_from <= at_time,
                or_(SurgeDetectionConfiguration.effective_to.is_(None), SurgeDetectionConfiguration.effective_to > at_time),
            )
            .order_by(SurgeDetectionConfiguration.effective_from.desc())
        )
        row = self.session.scalar(statement)
        if row is None:
            return None
        return SurgeRule(configuration=row, notification_channels=json.loads(row.notification_channels_json))
