from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

from app.core.config import Settings
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository


@dataclass(frozen=True)
class PublicForecastBucketRow:
    service_category: str
    forecast_demand_value: float
    geography_key: str | None = None


@dataclass(frozen=True)
class ResolvedPublicForecastSource:
    forecast_product: str
    approved_forecast_version_id: str
    forecast_window_label: str
    published_at: datetime
    source_cleaned_dataset_version_id: str | None
    category_rows: list[PublicForecastBucketRow]
    source_category_count: int


def _as_utc(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _format_day_window(start: datetime, end: datetime) -> str:
    return f"{start.date().isoformat()} to {end.date().isoformat()}"


def _format_week_window(start: datetime, end: datetime) -> str:
    return f"{start.date().isoformat()} to {end.date().isoformat()}"


class PublicForecastSourceService:
    def __init__(
        self,
        *,
        forecast_repository: ForecastRepository,
        weekly_forecast_repository: WeeklyForecastRepository,
        settings: Settings,
    ) -> None:
        self.forecast_repository = forecast_repository
        self.weekly_forecast_repository = weekly_forecast_repository
        self.settings = settings

    def resolve_current_source(self, forecast_product: str = "daily") -> ResolvedPublicForecastSource | None:
        if forecast_product == "weekly":
            return self._resolve_weekly()
        return self._resolve_daily()

    def _resolve_daily(self) -> ResolvedPublicForecastSource | None:
        marker = self.forecast_repository.get_current_marker(self.settings.forecast_product_name)
        if marker is None:
            return None
        version = self.forecast_repository.get_forecast_version(marker.forecast_version_id)
        if version is None or version.storage_status != "stored":
            return None
        buckets = self.forecast_repository.list_buckets(version.forecast_version_id)
        if not buckets:
            return None
        totals: dict[tuple[str, str | None], float] = {}
        categories: set[str] = set()
        for bucket in buckets:
            categories.add(bucket.service_category)
            key = (bucket.service_category, bucket.geography_key)
            totals[key] = totals.get(key, 0.0) + float(bucket.point_forecast)
        rows = [
            PublicForecastBucketRow(
                service_category=service_category,
                geography_key=geography_key,
                forecast_demand_value=value,
            )
            for (service_category, geography_key), value in sorted(totals.items())
        ]
        return ResolvedPublicForecastSource(
            forecast_product="daily",
            approved_forecast_version_id=version.forecast_version_id,
            forecast_window_label=_format_day_window(_as_utc(version.horizon_start), _as_utc(version.horizon_end)),
            published_at=_as_utc(version.activated_at or version.stored_at),
            source_cleaned_dataset_version_id=version.source_cleaned_dataset_version_id,
            category_rows=rows,
            source_category_count=len(categories),
        )

    def _resolve_weekly(self) -> ResolvedPublicForecastSource | None:
        marker = self.weekly_forecast_repository.get_current_marker(self.settings.weekly_forecast_product_name)
        if marker is None:
            return None
        version = self.weekly_forecast_repository.get_forecast_version(marker.weekly_forecast_version_id)
        if version is None or version.storage_status != "stored":
            return None
        buckets = self.weekly_forecast_repository.list_buckets(version.weekly_forecast_version_id)
        if not buckets:
            return None
        totals: dict[tuple[str, str | None], float] = {}
        categories: set[str] = set()
        for bucket in buckets:
            categories.add(bucket.service_category)
            key = (bucket.service_category, bucket.geography_key)
            totals[key] = totals.get(key, 0.0) + float(bucket.point_forecast)
        rows = [
            PublicForecastBucketRow(
                service_category=service_category,
                geography_key=geography_key,
                forecast_demand_value=value,
            )
            for (service_category, geography_key), value in sorted(totals.items())
        ]
        return ResolvedPublicForecastSource(
            forecast_product="weekly",
            approved_forecast_version_id=version.weekly_forecast_version_id,
            forecast_window_label=_format_week_window(_as_utc(version.week_start_local), _as_utc(version.week_end_local)),
            published_at=_as_utc(version.activated_at or version.stored_at),
            source_cleaned_dataset_version_id=version.source_cleaned_dataset_version_id,
            category_rows=rows,
            source_category_count=len(categories),
        )
