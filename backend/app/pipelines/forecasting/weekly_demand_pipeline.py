from __future__ import annotations

from dataclasses import dataclass
import math
from datetime import date


@dataclass
class TrainedWeeklyDemandArtifact:
    geography_scope: str
    scope_weekday_means: dict[tuple[str, str | None], dict[int, float]]
    scope_overall_means: dict[tuple[str, str | None], float]
    residual_q10_by_weekday: dict[int, float]
    residual_q90_by_weekday: dict[int, float]
    model_family: str
    baseline_method: str


class WeeklyDemandPipeline:
    model_family = "historical_weekday_global"
    baseline_method = "historical_daily_mean_with_weather_holiday_adjustments"
    feature_schema_version = "v1_weekly_scope_weekday_baseline"

    def fit(self, prepared: dict[str, object]) -> TrainedWeeklyDemandArtifact:
        category_counts = prepared["category_counts"]
        scope_counts = prepared["scope_counts"]
        scope_weekday_means: dict[tuple[str, str | None], dict[int, float]] = {}
        scope_overall_means: dict[tuple[str, str | None], float] = {}
        residuals_by_weekday: dict[int, list[float]] = {}

        for service_category, geography_key in prepared["scopes"]:
            scope_key = (service_category, geography_key)
            history = scope_counts.get(scope_key) or category_counts.get(service_category, {})
            history_values = [float(value) for value in history.values()]
            overall_mean = (sum(history_values) / len(history_values)) if history_values else 0.0
            weekday_groups: dict[int, list[float]] = {}
            for historical_date, count in history.items():
                weekday_groups.setdefault(historical_date.weekday(), []).append(float(count))
            weekday_means = {
                weekday: (sum(values) / len(values)) if values else overall_mean
                for weekday, values in weekday_groups.items()
            }
            scope_weekday_means[scope_key] = weekday_means
            scope_overall_means[scope_key] = overall_mean
            for historical_date, count in history.items():
                estimate = weekday_means.get(historical_date.weekday(), overall_mean)
                residuals_by_weekday.setdefault(historical_date.weekday(), []).append(float(count) - float(estimate))

        all_residuals = [residual for values in residuals_by_weekday.values() for residual in values]
        global_q10 = _quantile(all_residuals, 0.1) if all_residuals else 0.0
        global_q90 = _quantile(all_residuals, 0.9) if all_residuals else 0.0
        residual_q10_by_weekday = {
            weekday: _quantile(residuals_by_weekday.get(weekday, []), 0.1) if residuals_by_weekday.get(weekday) else global_q10
            for weekday in range(7)
        }
        residual_q90_by_weekday = {
            weekday: _quantile(residuals_by_weekday.get(weekday, []), 0.9) if residuals_by_weekday.get(weekday) else global_q90
            for weekday in range(7)
        }

        return TrainedWeeklyDemandArtifact(
            geography_scope=prepared["geography_scope"],
            scope_weekday_means=scope_weekday_means,
            scope_overall_means=scope_overall_means,
            residual_q10_by_weekday=residual_q10_by_weekday,
            residual_q90_by_weekday=residual_q90_by_weekday,
            model_family=self.model_family,
            baseline_method=self.baseline_method,
        )

    def predict(
        self,
        artifact: TrainedWeeklyDemandArtifact,
        prepared: dict[str, object],
    ) -> dict[str, object]:
        target_context = prepared.get("target_context", {})
        buckets: list[dict[str, object]] = []

        for service_category, geography_key in prepared["scopes"]:
            scope_key = (service_category, geography_key)
            weekday_means = artifact.scope_weekday_means.get(scope_key, {})
            overall_mean = artifact.scope_overall_means.get(scope_key, 0.0)

            for forecast_date in prepared["target_dates"]:
                base_estimate = self._estimate_for_date(
                    forecast_date=forecast_date,
                    weekday_means=weekday_means,
                    overall_mean=overall_mean,
                )
                context = target_context.get(forecast_date, {})
                point_forecast = self._apply_context_adjustments(base_estimate, context)
                q10_residual = artifact.residual_q10_by_weekday.get(forecast_date.weekday(), -0.2 * point_forecast)
                q90_residual = artifact.residual_q90_by_weekday.get(forecast_date.weekday(), 0.2 * point_forecast)
                spread = max(math.sqrt(max(point_forecast, 0.0)), 1.0)
                quantile_p10 = max(min(point_forecast + q10_residual, point_forecast - 0.1 * spread), 0.0)
                quantile_p50 = point_forecast
                quantile_p90 = max(max(point_forecast + q90_residual, point_forecast + 0.1 * spread), quantile_p50)
                buckets.append(
                    {
                        "forecast_date_local": forecast_date,
                        "service_category": service_category,
                        "geography_key": geography_key,
                        "point_forecast": round(max(point_forecast, 0.0), 2),
                        "quantile_p10": round(max(quantile_p10, 0.0), 2),
                        "quantile_p50": round(max(quantile_p50, 0.0), 2),
                        "quantile_p90": round(max(quantile_p90, quantile_p50), 2),
                        "baseline_value": round(max(overall_mean, 0.0), 2),
                    }
                )

        return {
            "model_family": artifact.model_family,
            "geography_scope": artifact.geography_scope,
            "baseline_method": artifact.baseline_method,
            "buckets": buckets,
        }

    def run(self, prepared: dict[str, object]) -> dict[str, object]:
        artifact = self.fit(prepared)
        return self.predict(artifact, prepared)

    def _estimate_for_date(
        self,
        *,
        forecast_date: date,
        weekday_means: dict[int, float],
        overall_mean: float,
    ) -> float:
        return float(weekday_means.get(forecast_date.weekday(), overall_mean))

    def _apply_context_adjustments(self, base_estimate: float, context: dict[str, object]) -> float:
        adjusted = float(base_estimate)
        if bool(context.get("is_holiday")):
            adjusted *= 0.85
        if bool(context.get("has_weather")):
            adjusted += max(float(context.get("total_precipitation_mm") or 0.0) * 0.05, 0.0)
            adjusted += float(context.get("avg_temperature_c") or 0.0) * 0.01
        return max(adjusted, 0.0)


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(float(value) for value in values)
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight
