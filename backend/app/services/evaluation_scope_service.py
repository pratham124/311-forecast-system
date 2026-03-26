from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.services.forecast_service import compute_forecast_horizon
from app.services.week_window_service import WeekWindowService


class MissingForecastScopeError(RuntimeError):
    pass


class ActualsNotReadyError(RuntimeError):
    pass


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass
class EvaluationScope:
    forecast_product_name: str
    source_cleaned_dataset_version_id: str | None
    source_forecast_version_id: str | None
    source_weekly_forecast_version_id: str | None
    evaluation_window_start: datetime
    evaluation_window_end: datetime


@dataclass
class EvaluationScopeService:
    cleaned_dataset_repository: CleanedDatasetRepository
    forecast_repository: ForecastRepository
    weekly_forecast_repository: WeeklyForecastRepository
    settings: object

    def resolve_scope(self, forecast_product_name: str, now: datetime | None = None) -> EvaluationScope:
        approved_dataset = self.cleaned_dataset_repository.get_current_approved_dataset(getattr(self.settings, "source_name", "edmonton_311"))
        source_cleaned_dataset_version_id = approved_dataset.dataset_version_id if approved_dataset is not None else None
        latest_actual_at = self._get_latest_actual_at()

        if forecast_product_name == "daily_1_day":
            selected_version = None
            find_completed = getattr(self.forecast_repository, "find_latest_stored_version_ending_by", None)
            if latest_actual_at is not None and callable(find_completed):
                selected_version = find_completed(latest_actual_at)
            find_latest = getattr(self.forecast_repository, "find_latest_stored_version", None)
            if selected_version is None and callable(find_latest):
                selected_version = find_latest()
            if selected_version is not None:
                return EvaluationScope(
                    forecast_product_name=forecast_product_name,
                    source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
                    source_forecast_version_id=selected_version.forecast_version_id,
                    source_weekly_forecast_version_id=None,
                    evaluation_window_start=selected_version.horizon_start,
                    evaluation_window_end=selected_version.horizon_end,
                )
            marker = self.forecast_repository.get_current_marker(getattr(self.settings, "forecast_product_name", "daily_1_day_demand"))
            if marker is not None:
                return EvaluationScope(
                    forecast_product_name=forecast_product_name,
                    source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
                    source_forecast_version_id=marker.forecast_version_id,
                    source_weekly_forecast_version_id=None,
                    evaluation_window_start=marker.horizon_start,
                    evaluation_window_end=marker.horizon_end,
                )
            start, end = compute_forecast_horizon(now)
            return EvaluationScope(forecast_product_name, source_cleaned_dataset_version_id, None, None, start, end)

        selected_version = None
        find_completed = getattr(self.weekly_forecast_repository, "find_latest_stored_version_ending_by", None)
        if latest_actual_at is not None and callable(find_completed):
            selected_version = find_completed(latest_actual_at)
        find_latest = getattr(self.weekly_forecast_repository, "find_latest_stored_version", None)
        if selected_version is None and callable(find_latest):
            selected_version = find_latest()
        if selected_version is not None:
            return EvaluationScope(
                forecast_product_name=forecast_product_name,
                source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
                source_forecast_version_id=None,
                source_weekly_forecast_version_id=selected_version.weekly_forecast_version_id,
                evaluation_window_start=selected_version.week_start_local,
                evaluation_window_end=selected_version.week_end_local,
            )
        marker = self.weekly_forecast_repository.get_current_marker(getattr(self.settings, "weekly_forecast_product_name", "weekly_7_day_demand"))
        if marker is not None:
            return EvaluationScope(
                forecast_product_name=forecast_product_name,
                source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
                source_forecast_version_id=None,
                source_weekly_forecast_version_id=marker.weekly_forecast_version_id,
                evaluation_window_start=marker.week_start_local,
                evaluation_window_end=marker.week_end_local,
            )
        week_window = WeekWindowService(getattr(self.settings, "weekly_forecast_timezone", "America/Edmonton")).get_week_window(now)
        return EvaluationScope(forecast_product_name, source_cleaned_dataset_version_id, None, None, week_window.week_start_local, week_window.week_end_local)

    def resolve_scope_from_run(self, run) -> EvaluationScope:
        return EvaluationScope(
            forecast_product_name=run.forecast_product_name,
            source_cleaned_dataset_version_id=run.source_cleaned_dataset_version_id,
            source_forecast_version_id=run.source_forecast_version_id,
            source_weekly_forecast_version_id=run.source_weekly_forecast_version_id,
            evaluation_window_start=run.evaluation_window_start,
            evaluation_window_end=run.evaluation_window_end,
        )

    def ensure_actuals_ready(self, scope: EvaluationScope) -> None:
        latest_actual_at = self._get_latest_actual_at()
        if latest_actual_at is None:
            raise ActualsNotReadyError("Observed demand is not yet available for the selected forecast window")

        required_latest_actual_at = _ensure_utc(scope.evaluation_window_end)
        if scope.forecast_product_name == "daily_1_day":
            required_latest_actual_at -= timedelta(hours=1)
        else:
            required_latest_actual_at -= timedelta(days=1)

        if latest_actual_at < required_latest_actual_at:
            raise ActualsNotReadyError("Observed demand is not yet available for the selected forecast window")

    def list_engine_rows(self, scope: EvaluationScope) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        if scope.forecast_product_name == "daily_1_day":
            if scope.source_forecast_version_id is None:
                raise MissingForecastScopeError("Current daily forecast output is not available")
            for bucket in self.forecast_repository.list_buckets(scope.source_forecast_version_id):
                rows.append(
                    {
                        "bucket_start": _ensure_utc(bucket.bucket_start),
                        "bucket_end": _ensure_utc(bucket.bucket_end),
                        "service_category": bucket.service_category,
                        "geography_key": bucket.geography_key,
                        "forecast_engine": float(bucket.point_forecast),
                        "time_period_key": bucket.bucket_start.isoformat(),
                    }
                )
            return rows
        if scope.source_weekly_forecast_version_id is None:
            raise MissingForecastScopeError("Current weekly forecast output is not available")
        for bucket in self.weekly_forecast_repository.list_buckets(scope.source_weekly_forecast_version_id):
            bucket_start = datetime.combine(bucket.forecast_date_local, time.min, tzinfo=timezone.utc)
            bucket_end = bucket_start + timedelta(days=1)
            rows.append(
                {
                    "bucket_start": bucket_start,
                    "bucket_end": bucket_end,
                    "service_category": bucket.service_category,
                    "geography_key": bucket.geography_key,
                    "forecast_engine": float(bucket.point_forecast),
                    "time_period_key": bucket.forecast_date_local.isoformat(),
                }
            )
        return rows

    def list_actual_rows(self, scope: EvaluationScope) -> dict[tuple[datetime, str, str | None], float]:
        records = self.cleaned_dataset_repository.list_current_cleaned_records(
            getattr(self.settings, "source_name", "edmonton_311"),
            start_time=scope.evaluation_window_start,
            end_time=scope.evaluation_window_end,
        )
        actuals: dict[tuple[datetime, str, str | None], float] = defaultdict(float)
        for record in records:
            raw_requested_at = str(record.get("requested_at") or "")
            if not raw_requested_at:
                continue
            requested_at = datetime.fromisoformat(raw_requested_at.replace("Z", "+00:00"))
            service_category = str(record.get("category") or "Unknown")
            geography_key = record.get("geography_key") or record.get("ward") or record.get("neighbourhood")
            if scope.forecast_product_name == "daily_1_day":
                bucket_start = requested_at.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
            else:
                bucket_day = requested_at.astimezone(timezone.utc).date()
                bucket_start = datetime.combine(bucket_day, time.min, tzinfo=timezone.utc)
            actuals[(bucket_start, service_category, geography_key)] += 1.0
        return actuals

    def build_aligned_rows(self, scope: EvaluationScope, engine_rows: list[dict[str, object]], actual_rows: dict[tuple[datetime, str, str | None], float]) -> list[dict[str, object]]:
        aligned: list[dict[str, object]] = []
        collapse_geography = self._uses_category_only_geography(scope)
        for row in engine_rows:
            if collapse_geography and row.get("geography_key") is None:
                actual_value = sum(
                    value
                    for (bucket_start, service_category, _geography_key), value in actual_rows.items()
                    if bucket_start == row["bucket_start"] and service_category == row["service_category"]
                )
            else:
                actual_key = (row["bucket_start"], row["service_category"], row.get("geography_key"))
                actual_value = actual_rows.get(actual_key, 0.0)
            aligned.append({**row, "actual": float(actual_value)})
        if not aligned:
            raise MissingForecastScopeError("No forecast comparison rows are available")
        return aligned

    def fair_comparison_metadata(self, scope: EvaluationScope, segments: list[dict[str, object]]) -> dict[str, object]:
        return {
            "evaluationWindowStart": scope.evaluation_window_start,
            "evaluationWindowEnd": scope.evaluation_window_end,
            "productScope": scope.forecast_product_name,
            "segmentCoverage": [segment["segment_key"] for segment in segments],
        }

    def _uses_category_only_geography(self, scope: EvaluationScope) -> bool:
        if scope.forecast_product_name == "daily_1_day":
            if scope.source_forecast_version_id is None:
                return False
            getter = getattr(self.forecast_repository, "get_forecast_version", None)
            if not callable(getter):
                return False
            version = getter(scope.source_forecast_version_id)
            return bool(version is not None and getattr(version, "geography_scope", None) == "category_only")
        if scope.source_weekly_forecast_version_id is None:
            return False
        getter = getattr(self.weekly_forecast_repository, "get_forecast_version", None)
        if not callable(getter):
            return False
        version = getter(scope.source_weekly_forecast_version_id)
        return bool(version is not None and getattr(version, "geography_scope", None) == "category_only")

    def _get_latest_actual_at(self) -> datetime | None:
        getter = getattr(self.cleaned_dataset_repository, "get_latest_current_requested_at", None)
        if not callable(getter):
            return None
        return getter(getattr(self.settings, "source_name", "edmonton_311"))
