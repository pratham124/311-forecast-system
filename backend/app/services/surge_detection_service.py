from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import isclose, sqrt

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository


@dataclass
class SurgeMetrics:
    actual_demand_value: float
    forecast_p50_value: float
    residual_value: float
    residual_z_score: float
    percent_above_forecast: float | None
    rolling_baseline_mean: float
    rolling_baseline_stddev: float


class SurgeDetectionError(RuntimeError):
    pass


class SurgeDetectionService:
    def __init__(self, cleaned_dataset_repository: CleanedDatasetRepository, source_name: str) -> None:
        self.cleaned_dataset_repository = cleaned_dataset_repository
        self.source_name = source_name

    def compute_metrics(
        self,
        *,
        service_category: str,
        evaluation_window_start: datetime,
        evaluation_window_end: datetime,
        actual_demand_value: float,
        forecast_p50_value: float,
        rolling_baseline_window_count: int,
    ) -> SurgeMetrics:
        if rolling_baseline_window_count < 2:
            raise SurgeDetectionError("Rolling baseline window count must be at least 2")
        previous_counts = self._load_previous_counts(
            service_category=service_category,
            evaluation_window_start=evaluation_window_start,
            evaluation_window_end=evaluation_window_end,
            rolling_baseline_window_count=rolling_baseline_window_count,
        )
        if len(previous_counts) < 2:
            raise SurgeDetectionError("Insufficient historical observations for surge baseline")
        residual_value = actual_demand_value - forecast_p50_value
        residual_history = [count - forecast_p50_value for count in previous_counts]
        mean = sum(residual_history) / len(residual_history)
        variance = sum((value - mean) ** 2 for value in residual_history) / len(residual_history)
        stddev = sqrt(variance)
        if isclose(stddev, 0.0):
            z_score = 0.0 if residual_value <= mean else 999.0
        else:
            z_score = (residual_value - mean) / stddev
        if forecast_p50_value <= 0:
            percent_above_forecast = None
        else:
            percent_above_forecast = ((actual_demand_value - forecast_p50_value) / forecast_p50_value) * 100.0
        return SurgeMetrics(
            actual_demand_value=actual_demand_value,
            forecast_p50_value=forecast_p50_value,
            residual_value=residual_value,
            residual_z_score=z_score,
            percent_above_forecast=percent_above_forecast,
            rolling_baseline_mean=mean,
            rolling_baseline_stddev=stddev,
        )

    def _load_previous_counts(
        self,
        *,
        service_category: str,
        evaluation_window_start: datetime,
        evaluation_window_end: datetime,
        rolling_baseline_window_count: int,
    ) -> list[float]:
        window_start = evaluation_window_start.astimezone(timezone.utc) if evaluation_window_start.tzinfo else evaluation_window_start.replace(tzinfo=timezone.utc)
        window_end = evaluation_window_end.astimezone(timezone.utc) if evaluation_window_end.tzinfo else evaluation_window_end.replace(tzinfo=timezone.utc)
        bucket_size = window_end - window_start
        history_start = window_start - (bucket_size * rolling_baseline_window_count)
        records = self.cleaned_dataset_repository.list_current_cleaned_records(
            self.source_name,
            start_time=history_start,
            end_time=window_start,
        )
        if not records:
            raise SurgeDetectionError("Insufficient historical observations for surge baseline")
        counts: list[float] = []
        for index in range(rolling_baseline_window_count):
            bucket_start = history_start + (bucket_size * index)
            bucket_end = bucket_start + bucket_size
            count = 0.0
            for record in records:
                if str(record.get("category", "")).strip() != service_category:
                    continue
                timestamp = self._parse_timestamp(str(record.get("requested_at", "")))
                if timestamp is None:
                    continue
                if bucket_start <= timestamp < bucket_end:
                    count += 1.0
            counts.append(count)
        return counts

    @staticmethod
    def _parse_timestamp(value: str) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
