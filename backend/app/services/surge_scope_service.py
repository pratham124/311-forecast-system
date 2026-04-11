from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json

from app.core.config import get_settings
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.run_repository import RunRepository
from app.repositories.dataset_repository import DatasetRepository


@dataclass
class SurgeScope:
    service_category: str
    evaluation_window_start: datetime
    evaluation_window_end: datetime
    actual_demand_value: float
    forecast_run_id: str | None
    forecast_version_id: str | None
    forecast_p50_value: float | None


class SurgeScopeService:
    def __init__(
        self,
        *,
        run_repository: RunRepository,
        dataset_repository: DatasetRepository,
        forecast_repository: ForecastRepository,
    ) -> None:
        self.run_repository = run_repository
        self.dataset_repository = dataset_repository
        self.forecast_repository = forecast_repository

    def list_scopes(self, *, ingestion_run_id: str) -> list[SurgeScope]:
        run = self.run_repository.get_run(ingestion_run_id)
        if run is None or run.status not in {"success", "completed"} or not run.dataset_version_id:
            raise ValueError("A successful ingestion run with a stored dataset version is required")
        marker = self.forecast_repository.get_current_marker(get_settings().forecast_product_name)
        if marker is None:
            raise ValueError("No active daily forecast is available for surge evaluation")
        forecast_version = self.forecast_repository.get_forecast_version(marker.forecast_version_id)
        if forecast_version is None:
            raise ValueError("Active daily forecast version could not be resolved")

        records = self.dataset_repository.list_dataset_records(run.dataset_version_id)
        actual_counts: dict[tuple[str, datetime], float] = defaultdict(float)
        for row in records:
            normalized = self._normalize_record(row)
            service_category = str(normalized.get("category", "")).strip()
            requested_at = self._parse_timestamp(str(normalized.get("requested_at", "")))
            if not service_category or requested_at is None:
                continue
            hour_start = requested_at.replace(minute=0, second=0, microsecond=0)
            actual_counts[(service_category, hour_start)] += 1.0

        forecast_totals: dict[tuple[str, datetime], tuple[datetime, float]] = {}
        for bucket in self.forecast_repository.list_buckets(marker.forecast_version_id):
            key = (bucket.service_category, self._coerce_utc(bucket.bucket_start))
            bucket_end = self._coerce_utc(bucket.bucket_end)
            existing = forecast_totals.get(key)
            total = float(bucket.quantile_p50) + (existing[1] if existing else 0.0)
            forecast_totals[key] = (bucket_end, total)

        scopes: list[SurgeScope] = []
        for (service_category, hour_start), actual_value in sorted(actual_counts.items()):
            bucket_end, forecast_p50 = forecast_totals.get(
                (service_category, hour_start),
                (hour_start + timedelta(hours=1), None),
            )
            scopes.append(
                SurgeScope(
                    service_category=service_category,
                    evaluation_window_start=hour_start,
                    evaluation_window_end=bucket_end,
                    actual_demand_value=actual_value,
                    forecast_run_id=forecast_version.forecast_run_id,
                    forecast_version_id=forecast_version.forecast_version_id,
                    forecast_p50_value=forecast_p50,
                )
            )
        return scopes

    @staticmethod
    def _parse_timestamp(value: str) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    @staticmethod
    def _coerce_utc(value: datetime) -> datetime:
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)

    @staticmethod
    def _normalize_record(row: object) -> dict[str, object]:
        if isinstance(row, dict):
            return row
        payload = getattr(row, "record_payload", None)
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict):
                return parsed
        return {
            "requested_at": getattr(row, "requested_at", ""),
            "category": getattr(row, "category", ""),
        }
