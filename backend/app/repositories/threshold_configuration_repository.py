from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.threshold_alert_models import ThresholdConfiguration

DEFAULT_THRESHOLD_VALUE = 100.0
DEFAULT_NOTIFICATION_CHANNELS = ["dashboard"]
DEFAULT_MANAGER_ID = "system-default"
GLOBAL_THRESHOLD_SCOPE = "__GLOBAL__"
GLOBAL_FORECAST_WINDOW_TYPE = "global"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ThresholdConfigurationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_active_thresholds(self, *, at_time: datetime | None = None) -> list[ThresholdConfiguration]:
        current = at_time or _utc_now()
        statement = (
            select(ThresholdConfiguration)
            .where(
                ThresholdConfiguration.status == "active",
                ThresholdConfiguration.effective_from <= current,
                or_(ThresholdConfiguration.effective_to.is_(None), ThresholdConfiguration.effective_to > current),
            )
            .order_by(
                ThresholdConfiguration.service_category.asc(),
                ThresholdConfiguration.geography_value.asc(),
                ThresholdConfiguration.forecast_window_type.asc(),
            )
        )
        return list(self.session.scalars(statement))

    def find_active_threshold(
        self,
        *,
        service_category: str,
        geography_value: str | None,
        forecast_window_type: str,
        at_time: datetime | None = None,
        create_default_if_missing: bool = False,
    ) -> ThresholdConfiguration | None:
        current = at_time or _utc_now()
        base_filters = [
            ThresholdConfiguration.status == "active",
            ThresholdConfiguration.effective_from <= current,
            or_(ThresholdConfiguration.effective_to.is_(None), ThresholdConfiguration.effective_to > current),
        ]

        # FR-011a: category-plus-geography takes precedence over category-only
        if geography_value is not None:
            geo_match = self.session.scalar(
                select(ThresholdConfiguration)
                .where(
                    ThresholdConfiguration.service_category == service_category,
                    ThresholdConfiguration.geography_value == geography_value,
                    ThresholdConfiguration.forecast_window_type == forecast_window_type,
                    *base_filters,
                )
                .order_by(ThresholdConfiguration.effective_from.desc())
                .limit(1)
            )
            if geo_match is not None:
                return geo_match

        # Category-only match (geography_value IS NULL)
        cat_match = self.session.scalar(
            select(ThresholdConfiguration)
            .where(
                ThresholdConfiguration.service_category == service_category,
                ThresholdConfiguration.geography_value.is_(None),
                ThresholdConfiguration.forecast_window_type == forecast_window_type,
                *base_filters,
            )
            .order_by(ThresholdConfiguration.effective_from.desc())
            .limit(1)
        )
        if cat_match is not None:
            return cat_match

        if not create_default_if_missing:
            return None

        # Create a default category-level threshold
        return self.create_configuration(
            service_category=service_category,
            forecast_window_type=forecast_window_type,
            threshold_value=DEFAULT_THRESHOLD_VALUE,
            operational_manager_id=DEFAULT_MANAGER_ID,
            notification_channels=DEFAULT_NOTIFICATION_CHANNELS,
            geography_type=None,
            geography_value=None,
            effective_from=current,
        )

    @staticmethod
    def parse_channels(configuration: ThresholdConfiguration) -> list[str]:
        try:
            payload = json.loads(configuration.notification_channels_json)
        except json.JSONDecodeError:
            return []
        if not isinstance(payload, list):
            return []
        return [str(item) for item in payload if isinstance(item, str) and item]

    def create_configuration(
        self,
        *,
        service_category: str,
        forecast_window_type: str,
        threshold_value: float,
        operational_manager_id: str,
        notification_channels: list[str],
        geography_type: str | None = None,
        geography_value: str | None = None,
        effective_from: datetime | None = None,
    ) -> ThresholdConfiguration:
        configuration = ThresholdConfiguration(
            service_category=service_category,
            geography_type=geography_type,
            geography_value=geography_value,
            forecast_window_type=forecast_window_type,
            threshold_value=threshold_value,
            notification_channels_json=json.dumps(notification_channels),
            operational_manager_id=operational_manager_id,
            status="active",
            effective_from=effective_from or _utc_now(),
        )
        self.session.add(configuration)
        self.session.flush()
        return configuration

    def set_threshold_for_scope(
        self,
        *,
        service_category: str,
        forecast_window_type: str,
        threshold_value: float,
        operational_manager_id: str,
        geography_value: str | None = None,
        geography_type: str | None = None,
        notification_channels: list[str] | None = None,
    ) -> ThresholdConfiguration:
        current = _utc_now()
        existing = self.find_active_threshold(
            service_category=service_category,
            geography_value=geography_value,
            forecast_window_type=forecast_window_type,
            at_time=current,
        )
        channels = notification_channels
        if channels is None:
            channels = self.parse_channels(existing) if existing is not None else ["dashboard"]
        if not channels:
            channels = ["dashboard"]

        if existing is not None:
            existing.status = "inactive"
            existing.effective_to = current

        return self.create_configuration(
            service_category=service_category,
            forecast_window_type=forecast_window_type,
            threshold_value=threshold_value,
            operational_manager_id=operational_manager_id,
            notification_channels=channels,
            geography_type=geography_type,
            geography_value=geography_value,
            effective_from=current,
        )

    def get_global_threshold(
        self,
        *,
        create_default_if_missing: bool = False,
        at_time: datetime | None = None,
    ) -> ThresholdConfiguration | None:
        current = at_time or _utc_now()
        existing = self.session.scalar(
            select(ThresholdConfiguration)
            .where(
                ThresholdConfiguration.service_category == GLOBAL_THRESHOLD_SCOPE,
                ThresholdConfiguration.forecast_window_type == GLOBAL_FORECAST_WINDOW_TYPE,
                ThresholdConfiguration.geography_value.is_(None),
                ThresholdConfiguration.status == "active",
                ThresholdConfiguration.effective_from <= current,
                or_(ThresholdConfiguration.effective_to.is_(None), ThresholdConfiguration.effective_to > current),
            )
            .order_by(ThresholdConfiguration.effective_from.desc())
            .limit(1)
        )
        if existing is not None:
            return existing
        if not create_default_if_missing:
            return None
        return self.set_global_threshold(threshold_value=DEFAULT_THRESHOLD_VALUE, operational_manager_id=DEFAULT_MANAGER_ID)

    def set_global_threshold(self, *, threshold_value: float, operational_manager_id: str) -> ThresholdConfiguration:
        current = _utc_now()
        existing = self.get_global_threshold(create_default_if_missing=False, at_time=current)
        channels = DEFAULT_NOTIFICATION_CHANNELS
        if existing is not None:
            channels = self.parse_channels(existing) or DEFAULT_NOTIFICATION_CHANNELS
            existing.status = "inactive"
            existing.effective_to = current
        return self.create_configuration(
            service_category=GLOBAL_THRESHOLD_SCOPE,
            forecast_window_type=GLOBAL_FORECAST_WINDOW_TYPE,
            threshold_value=threshold_value,
            operational_manager_id=operational_manager_id,
            notification_channels=channels,
            geography_type=None,
            geography_value=None,
            effective_from=current,
        )

    def ensure_default_category_threshold(
        self,
        *,
        service_category: str,
        forecast_window_type: str,
        at_time: datetime | None = None,
    ) -> ThresholdConfiguration:
        current = at_time or _utc_now()
        # Deprecated in global-threshold mode. Keep signature for compatibility.
        _ = service_category, forecast_window_type
        return self.get_global_threshold(create_default_if_missing=True, at_time=current)  # type: ignore[return-value]

    def list_active_category_thresholds(self, *, forecast_window_type: str = "daily") -> list[ThresholdConfiguration]:
        _ = forecast_window_type
        current = _utc_now()
        global_row = self.get_global_threshold(create_default_if_missing=True, at_time=current)
        return [global_row] if global_row is not None else []
