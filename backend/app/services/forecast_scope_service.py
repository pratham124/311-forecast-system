from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.repositories.forecast_repository import ForecastRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository


@dataclass
class ForecastScope:
    service_category: str
    geography_type: str | None
    geography_value: str | None
    forecast_window_type: str
    forecast_window_start: datetime
    forecast_window_end: datetime
    forecast_bucket_value: float


class ForecastScopeService:
    def __init__(
        self,
        *,
        forecast_repository: ForecastRepository,
        weekly_forecast_repository: WeeklyForecastRepository,
    ) -> None:
        self.forecast_repository = forecast_repository
        self.weekly_forecast_repository = weekly_forecast_repository

    def list_scopes(self, *, forecast_reference_id: str, forecast_product: str) -> list[ForecastScope]:
        if forecast_product == "daily":
            buckets = self.forecast_repository.list_buckets(forecast_reference_id)
            return [
                ForecastScope(
                    service_category=bucket.service_category,
                    geography_type=None,
                    geography_value=None,
                    forecast_window_type="hourly",
                    forecast_window_start=bucket.bucket_start,
                    forecast_window_end=bucket.bucket_end,
                    forecast_bucket_value=float(bucket.point_forecast),
                )
                for bucket in buckets
            ]
        buckets = self.weekly_forecast_repository.list_buckets(forecast_reference_id)
        scopes: list[ForecastScope] = []
        for bucket in buckets:
            start = datetime.combine(bucket.forecast_date_local, datetime.min.time(), tzinfo=timezone.utc)
            end = start.replace(hour=23, minute=59, second=59)
            scopes.append(
                ForecastScope(
                    service_category=bucket.service_category,
                    geography_type=None,
                    geography_value=None,
                    forecast_window_type="daily",
                    forecast_window_start=start,
                    forecast_window_end=end,
                    forecast_bucket_value=float(bucket.point_forecast),
                )
            )
        return scopes
