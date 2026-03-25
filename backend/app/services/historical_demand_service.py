from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.schemas.forecast_visualization import VisualizationPoint


class HistoricalDemandService:
    def __init__(self, cleaned_dataset_repository: CleanedDatasetRepository, source_name: str) -> None:
        self.cleaned_dataset_repository = cleaned_dataset_repository
        self.source_name = source_name

    def build_series(
        self,
        *,
        boundary: datetime,
        granularity: str,
        service_categories: list[str] | None = None,
        excluded_service_categories: list[str] | None = None,
        service_category: str | None = None,
    ) -> tuple[list[VisualizationPoint], str | None, datetime, datetime]:
        boundary_utc = boundary.astimezone(timezone.utc) if boundary.tzinfo else boundary.replace(tzinfo=timezone.utc)
        start = boundary_utc - timedelta(days=7)
        records = self.cleaned_dataset_repository.list_current_cleaned_records(
            self.source_name,
            start_time=start,
            end_time=boundary_utc,
        )
        current_dataset = self.cleaned_dataset_repository.get_current_approved_dataset(self.source_name)
        selected_categories = service_categories or ([service_category] if service_category else [])
        excluded_categories = excluded_service_categories or []
        grouped: dict[datetime, float] = defaultdict(float)
        for record in records:
            category = str(record.get("category"))
            if selected_categories and category not in selected_categories:
                continue
            if excluded_categories and category in excluded_categories:
                continue
            timestamp = self._parse_timestamp(str(record.get("requested_at", "")))
            if timestamp is None:
                continue
            bucket_time = timestamp.replace(minute=0, second=0, microsecond=0)
            if granularity == "daily":
                bucket_time = bucket_time.replace(hour=0)
            grouped[bucket_time] += 1.0
        series = [VisualizationPoint(timestamp=key, value=value) for key, value in sorted(grouped.items())]
        dataset_version_id = current_dataset.dataset_version_id if current_dataset is not None else None
        return series, dataset_version_id, start, boundary_utc

    @staticmethod
    def _parse_timestamp(value: str) -> datetime | None:
        if not value:
            return None
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
