from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd


def _clamp_non_negative(value: float) -> float:
    return max(round(value, 2), 0.0)


@dataclass
class TrainedWeeklyDemandArtifact:
    geography_scope: str
    category_codes: dict[object, int]
    geography_codes: dict[object, int]
    feature_names: list[str]
    point_model: lgb.LGBMRegressor | None
    residual_q10_by_weekday: dict[int, float]
    residual_q90_by_weekday: dict[int, float]
    model_family: str
    baseline_method: str


class WeeklyDemandPipeline:
    model_family = "lightgbm_weekly_global"
    baseline_method = "historical_daily_mean_with_lightgbm_weather_holiday_features"
    feature_schema_version = "wk_lgbm_v4_wx_holiday"

    def fit(self, prepared: dict[str, object]) -> TrainedWeeklyDemandArtifact:
        training_rows = list(prepared.get("training_rows", []))
        geography_scope = str(prepared.get("geography_scope", "category_only"))
        feature_names = self._feature_names()
        category_codes = self._build_codes(training_rows, "service_category")
        geography_codes = self._build_codes(training_rows, "geography_key")

        if not training_rows:
            return TrainedWeeklyDemandArtifact(
                geography_scope=geography_scope,
                category_codes=category_codes,
                geography_codes=geography_codes,
                feature_names=feature_names,
                point_model=None,
                residual_q10_by_weekday={},
                residual_q90_by_weekday={},
                model_family=self.model_family,
                baseline_method=self.baseline_method,
            )

        x_train = pd.DataFrame(
            [self._encode_row(row, category_codes, geography_codes, feature_names) for row in training_rows],
            columns=feature_names,
            dtype=float,
        )
        y_train = np.array([float(row.get("observed_count", 0.0)) for row in training_rows], dtype=float)

        point_model: lgb.LGBMRegressor | None = None
        residual_q10_by_weekday: dict[int, float] = {}
        residual_q90_by_weekday: dict[int, float] = {}

        if float(y_train.sum()) > 0.0:
            point_model = self._fit_model()
            point_model.fit(x_train, y_train)
            predictions = np.clip(point_model.predict(x_train), 0.0, None)
            residual_q10_by_weekday, residual_q90_by_weekday = self._build_residual_calibration(training_rows, predictions)

        return TrainedWeeklyDemandArtifact(
            geography_scope=geography_scope,
            category_codes=category_codes,
            geography_codes=geography_codes,
            feature_names=feature_names,
            point_model=point_model,
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
        scoring_rows = list(prepared.get("rows", []))
        buckets: list[dict[str, object]] = []

        if not scoring_rows:
            return {
                "model_family": artifact.model_family,
                "geography_scope": artifact.geography_scope,
                "baseline_method": artifact.baseline_method,
                "buckets": buckets,
            }

        for row in scoring_rows:
            x_score = pd.DataFrame(
                [self._encode_row(row, artifact.category_codes, artifact.geography_codes, artifact.feature_names)],
                columns=artifact.feature_names,
                dtype=float,
            )
            if artifact.point_model is None:
                point_prediction = max(float(row.get("historical_mean", 0.0)), 0.0)
            else:
                point_prediction = float(np.clip(artifact.point_model.predict(x_score)[0], 0.0, None))

            weekday = int(row["day_of_week"])
            q10_residual = artifact.residual_q10_by_weekday.get(weekday, -0.2 * point_prediction)
            q90_residual = artifact.residual_q90_by_weekday.get(weekday, 0.2 * point_prediction)
            p10 = _clamp_non_negative(min(point_prediction + q10_residual, point_prediction))
            p50 = _clamp_non_negative(point_prediction)
            p90 = _clamp_non_negative(max(point_prediction + q90_residual, point_prediction))
            baseline = _clamp_non_negative(float(row.get("historical_mean", 0.0)))
            buckets.append(
                {
                    "forecast_date_local": row["forecast_date_local"],
                    "service_category": row["service_category"],
                    "geography_key": row["geography_key"],
                    "point_forecast": p50,
                    "quantile_p10": p10,
                    "quantile_p50": p50,
                    "quantile_p90": max(p90, p50),
                    "baseline_value": baseline,
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

    def _feature_names(self) -> list[str]:
        return [
            "service_category_code",
            "geography_code",
            "day_of_week",
            "day_of_year",
            "month",
            "is_weekend",
            "is_holiday",
            "weather_is_missing",
            "avg_temperature_c",
            "total_precipitation_mm",
            "total_snowfall_mm",
            "avg_precipitation_probability_pct",
            "historical_mean",
            "lag_7d",
            "rolling_mean_7d",
            "rolling_mean_28d",
        ]

    def _fit_model(self) -> lgb.LGBMRegressor:
        return lgb.LGBMRegressor(
            objective="regression",
            n_estimators=80,
            learning_rate=0.08,
            num_leaves=15,
            min_child_samples=8,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            verbosity=-1,
        )

    def _build_codes(self, rows: list[dict[str, object]], key: str) -> dict[object, int]:
        values = sorted({row.get(key) for row in rows}, key=lambda value: "" if value is None else str(value))
        return {value: index for index, value in enumerate(values)}

    def _encode_row(
        self,
        row: dict[str, object],
        category_codes: dict[object, int],
        geography_codes: dict[object, int],
        feature_names: list[str] | None = None,
    ) -> list[float]:
        values = {
            "service_category_code": float(category_codes.get(row.get("service_category"), 0)),
            "geography_code": float(geography_codes.get(row.get("geography_key"), 0)),
            "day_of_week": float(row["day_of_week"]),
            "day_of_year": float(row["day_of_year"]),
            "month": float(row["month"]),
            "is_weekend": 1.0 if row["is_weekend"] else 0.0,
            "is_holiday": 1.0 if row["is_holiday"] else 0.0,
            "weather_is_missing": 1.0 if bool(row.get("weather_is_missing")) else 0.0,
            "avg_temperature_c": self._coerce_feature_value(row.get("avg_temperature_c")),
            "total_precipitation_mm": self._coerce_feature_value(row.get("total_precipitation_mm")),
            "total_snowfall_mm": self._coerce_feature_value(row.get("total_snowfall_mm")),
            "avg_precipitation_probability_pct": self._coerce_feature_value(
                row.get("avg_precipitation_probability_pct")
            ),
            "historical_mean": float(row.get("historical_mean", 0.0)),
            "lag_7d": float(row.get("lag_7d", 0.0)),
            "rolling_mean_7d": float(row.get("rolling_mean_7d", 0.0)),
            "rolling_mean_28d": float(row.get("rolling_mean_28d", 0.0)),
        }
        ordered_feature_names = feature_names or self._feature_names()
        return [float(values.get(name, 0.0)) for name in ordered_feature_names]

    @staticmethod
    def _coerce_feature_value(value: Any) -> float:
        if value is None:
            return float("nan")
        return float(value)

    def _build_residual_calibration(
        self,
        training_rows: list[dict[str, object]],
        predictions: np.ndarray,
    ) -> tuple[dict[int, float], dict[int, float]]:
        residuals_by_weekday: dict[int, list[float]] = {}
        for row, prediction in zip(training_rows, predictions):
            weekday = int(row["day_of_week"])
            residual = float(row.get("observed_count", 0.0)) - float(prediction)
            residuals_by_weekday.setdefault(weekday, []).append(residual)

        if not residuals_by_weekday:
            return {}, {}

        all_residuals = np.array([residual for values in residuals_by_weekday.values() for residual in values], dtype=float)
        global_q10 = float(np.quantile(all_residuals, 0.1))
        global_q90 = float(np.quantile(all_residuals, 0.9))
        residual_q10_by_weekday: dict[int, float] = {}
        residual_q90_by_weekday: dict[int, float] = {}
        for weekday in range(7):
            weekday_residuals = residuals_by_weekday.get(weekday)
            if not weekday_residuals:
                residual_q10_by_weekday[weekday] = global_q10
                residual_q90_by_weekday[weekday] = global_q90
                continue
            residual_array = np.array(weekday_residuals, dtype=float)
            residual_q10_by_weekday[weekday] = float(np.quantile(residual_array, 0.1))
            residual_q90_by_weekday[weekday] = float(np.quantile(residual_array, 0.9))
        return residual_q10_by_weekday, residual_q90_by_weekday


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
