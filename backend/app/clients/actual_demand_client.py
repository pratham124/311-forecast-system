from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository


def _parse_requested_at(raw_value: str) -> datetime:
    return datetime.fromisoformat(raw_value.replace("Z", "+00:00")).astimezone(timezone.utc)


@dataclass
class ActualDemandClient:
    cleaned_dataset_repository: CleanedDatasetRepository
    source_name: str

    def list_actual_rows(
        self,
        *,
        time_range_start: datetime,
        time_range_end: datetime,
        service_category: str | None,
        comparison_granularity: str,
    ) -> list[dict[str, object]]:
        rows_by_key: dict[tuple[datetime, str], dict[str, object]] = {}
        records = self.cleaned_dataset_repository.list_current_cleaned_records(
            self.source_name,
            start_time=time_range_start,
            end_time=time_range_end,
        )
        for record in records:
            category = str(record.get("category") or "Unknown")
            if service_category and category != service_category:
                continue
            requested_at = _parse_requested_at(str(record.get("requested_at") or ""))
            if comparison_granularity == "daily":
                bucket_start = requested_at.replace(hour=0, minute=0, second=0, microsecond=0)
                bucket_end = bucket_start + timedelta(days=1)
            else:
                bucket_start = requested_at.replace(minute=0, second=0, microsecond=0)
                bucket_end = bucket_start + timedelta(hours=1)
            key = (bucket_start, category)
            row = rows_by_key.get(key)
            if row is None:
                rows_by_key[key] = {
                    "bucket_start": bucket_start,
                    "bucket_end": bucket_end,
                    "service_category": category,
                    "actual_value": 1.0,
                }
            else:
                row["actual_value"] = float(row["actual_value"]) + 1.0
        return list(rows_by_key.values())
