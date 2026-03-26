from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository


class BaselineGenerationError(RuntimeError):
    pass


class BaselineComparisonRows(list[dict[str, object]]):
    def __init__(self, rows: list[dict[str, object]], *, excluded_scopes: list[str] | None = None) -> None:
        super().__init__(rows)
        self.excluded_scopes = excluded_scopes or []


@dataclass
class BaselineService:
    cleaned_dataset_repository: CleanedDatasetRepository
    settings: object

    def _aggregate_history(self, forecast_product: str, window_start, window_end) -> dict[tuple[str, str | None], list[tuple[object, float]]]:
        history_start = window_start - timedelta(days=28)
        history_records = self.cleaned_dataset_repository.list_current_cleaned_records(
            getattr(self.settings, "source_name", "edmonton_311"),
            start_time=history_start,
            end_time=window_start,
        )
        if not history_records:
            raise BaselineGenerationError("No historical actuals are available for baseline generation")

        aggregates: dict[tuple[str, str | None, object], float] = defaultdict(float)
        for record in history_records:
            service_category = str(record.get("category") or "Unknown")
            geography_key = record.get("geography_key") or record.get("ward") or record.get("neighbourhood")
            timestamp = str(record.get("requested_at") or "")
            if not timestamp:
                continue
            if forecast_product == "daily_1_day":
                time_key = timestamp[:13]
            else:
                time_key = timestamp[:10]
            aggregates[(service_category, geography_key, time_key)] += 1.0
            if geography_key is not None:
                aggregates[(service_category, None, time_key)] += 1.0

        grouped: dict[tuple[str, str | None], list[tuple[object, float]]] = defaultdict(list)
        for (service_category, geography_key, time_key), value in aggregates.items():
            grouped[(service_category, geography_key)].append((time_key, value))
        return grouped

    def generate_baselines(self, forecast_product: str, rows: list[dict[str, object]]) -> BaselineComparisonRows:
        if not rows:
            raise BaselineGenerationError("No aligned rows are available for baseline generation")
        history = self._aggregate_history(
            forecast_product,
            rows[0]["bucket_start"],
            rows[-1]["bucket_end"],
        )
        if not history:
            raise BaselineGenerationError("No historical baseline series available for the evaluated scope")
        enriched: list[dict[str, object]] = []
        excluded_scopes: list[str] = []
        for row in rows:
            scope_key = (str(row["service_category"]), row.get("geography_key"))
            series = [value for _time_key, value in history.get(scope_key, [])]
            if not series:
                if scope_key[0] not in excluded_scopes:
                    excluded_scopes.append(scope_key[0])
                continue
            seasonal_naive = float(series[-1])
            moving_average = float(sum(series[-min(len(series), 7):]) / min(len(series), 7))
            enriched.append({
                **row,
                "seasonal_naive": round(seasonal_naive, 4),
                "moving_average": round(moving_average, 4),
            })
        if not enriched:
            if len(excluded_scopes) == 1:
                raise BaselineGenerationError(
                    f"No historical baseline series available for scope {excluded_scopes[0]}"
                )
            raise BaselineGenerationError(
                f"No historical baseline series available for scopes {', '.join(excluded_scopes)}"
            )
        return BaselineComparisonRows(enriched, excluded_scopes=excluded_scopes)
