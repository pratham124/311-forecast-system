from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from app.repositories.forecast_repository import ForecastRepository


def _day_bucket_start(value: datetime) -> datetime:
    return value.replace(hour=0, minute=0, second=0, microsecond=0)


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass
class ForecastHistoryClient:
    forecast_repository: ForecastRepository

    def list_forecast_rows(
        self,
        *,
        time_range_start: datetime,
        time_range_end: datetime,
        service_category: str | None,
        comparison_granularity: str,
    ) -> tuple[list[dict[str, object]], str | None]:
        rows_by_key: dict[tuple[object, str], dict[str, object]] = {}
        source_forecast_version_id: str | None = None
        versions = self.forecast_repository.list_stored_versions_overlapping_range(
            range_start=time_range_start,
            range_end=time_range_end,
        )
        for version in versions:
            for bucket in self.forecast_repository.list_buckets(version.forecast_version_id):
                if service_category and bucket.service_category != service_category:
                    continue
                bucket_start = _to_utc(bucket.bucket_start)
                bucket_end = _to_utc(bucket.bucket_end)
                if not (time_range_start <= bucket_start < time_range_end):
                    continue
                if comparison_granularity == "daily":
                    bucket_key = (_day_bucket_start(bucket_start), bucket.service_category)
                    existing = rows_by_key.get(bucket_key)
                    if existing is None:
                        rows_by_key[bucket_key] = {
                            "bucket_start": _day_bucket_start(bucket_start),
                            "bucket_end": _day_bucket_start(bucket_start) + timedelta(days=1),
                            "service_category": bucket.service_category,
                            "forecast_value": float(bucket.point_forecast),
                        }
                    else:
                        existing["forecast_value"] = float(existing["forecast_value"]) + float(bucket.point_forecast)
                else:
                    bucket_key = (bucket_start, bucket.service_category)
                    if bucket_key in rows_by_key:
                        continue
                    rows_by_key[bucket_key] = {
                        "bucket_start": bucket_start,
                        "bucket_end": bucket_end,
                        "service_category": bucket.service_category,
                        "forecast_value": float(bucket.point_forecast),
                    }
                source_forecast_version_id = source_forecast_version_id or version.forecast_version_id
        return list(rows_by_key.values()), source_forecast_version_id
