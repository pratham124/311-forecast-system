from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.repositories.forecast_repository import ForecastRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository


@dataclass(slots=True)
class ForecastScope:
    service_category: str
    geography_type: str | None
    geography_value: str | None
    forecast_window_type: str
    forecast_window_start: datetime
    forecast_window_end: datetime
    forecast_value: float


class ForecastScopeService:
    def __init__(
        self,
        *,
        forecast_repository: ForecastRepository,
        weekly_forecast_repository: WeeklyForecastRepository,
    ) -> None:
        self.forecast_repository = forecast_repository
        self.weekly_forecast_repository = weekly_forecast_repository

    def list_scopes(self, *, forecast_product: str, forecast_reference_id: str) -> list[ForecastScope]:
        if forecast_product == "daily":
            return self._list_daily_scopes(forecast_reference_id)
        if forecast_product == "weekly":
            return self._list_weekly_scopes(forecast_reference_id)
        raise ValueError("Unsupported forecast product")

    def _list_daily_scopes(self, forecast_version_id: str) -> list[ForecastScope]:
        buckets = self.forecast_repository.list_buckets(forecast_version_id)
        scopes: list[ForecastScope] = []
        for bucket in buckets:
            scopes.append(
                ForecastScope(
                    service_category=bucket.service_category,
                    geography_type="ward" if bucket.geography_key else None,
                    geography_value=bucket.geography_key,
                    forecast_window_type="hourly",
                    forecast_window_start=bucket.bucket_start,
                    forecast_window_end=bucket.bucket_end,
                    forecast_value=float(bucket.point_forecast),
                )
            )
        return scopes

    def _list_weekly_scopes(self, weekly_forecast_version_id: str) -> list[ForecastScope]:
        buckets = self.weekly_forecast_repository.list_buckets(weekly_forecast_version_id)
        scopes: list[ForecastScope] = []
        for bucket in buckets:
            start = bucket.forecast_date_local
            end = start + timedelta(days=1)
            scopes.append(
                ForecastScope(
                    service_category=bucket.service_category,
                    geography_type="ward" if bucket.geography_key else None,
                    geography_value=bucket.geography_key,
                    forecast_window_type="daily",
                    forecast_window_start=start,
                    forecast_window_end=end,
                    forecast_value=float(bucket.point_forecast),
                )
            )
        return scopes
