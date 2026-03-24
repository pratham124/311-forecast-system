from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import lightgbm as lgb
import numpy as np
import pandas as pd


CALIBRATION_FRACTION = 0.2


def _clamp_non_negative(value: float) -> float:
    return max(round(value, 2), 0.0)


@dataclass
class TrainedHourlyDemandArtifact:
    geography_scope: str
    category_codes: dict[object, int]
    geography_codes: dict[object, int]
    feature_names: list[str]
    point_model: lgb.LGBMRegressor | None
    residual_q10_by_hour: dict[int, float]
    residual_q90_by_hour: dict[int, float]
    model_family: str
    baseline_method: str


class HourlyDemandPipeline:
    model_family = "lightgbm_global"
    baseline_method = "historical_hourly_mean"
    feature_schema_version = "v1_hourly_lagged_demand"
    lag_hours = (1, 24, 168)
    rolling_windows = (24, 168)

    def fit(self, prepared_features: dict[str, object]) -> TrainedHourlyDemandArtifact:
        training_rows = list(prepared_features.get("training_rows", []))
        geography_scope = str(prepared_features.get("geography_scope", "category_only"))
        feature_names = self._feature_names()
        category_codes = self._build_codes(training_rows, "service_category")
        geography_codes = self._build_codes(training_rows, "geography_key")
        positive_labels = int(sum(1 for row in training_rows if float(row.get("observed_count", 0.0)) > 0.0))
        print(
            "[debug][forecast] pipeline fit "
            f"training_rows={len(training_rows)} "
            f"positive_labels={positive_labels} "
            f"geography_scope={geography_scope}"
        )

        if not training_rows:
            print("[debug][forecast] pipeline fit residual_calibration=False reason=no_training_rows")
            return TrainedHourlyDemandArtifact(
                geography_scope=geography_scope,
                category_codes=category_codes,
                geography_codes=geography_codes,
                feature_names=feature_names,
                point_model=None,
                residual_q10_by_hour={},
                residual_q90_by_hour={},
                model_family=self.model_family,
                baseline_method=self.baseline_method,
            )

        x_train = pd.DataFrame(
            [self._encode_row(row, category_codes, geography_codes) for row in training_rows],
            columns=feature_names,
            dtype=float,
        )
        y_train = np.array([float(row["observed_count"]) for row in training_rows], dtype=float)

        point_model: lgb.LGBMRegressor | None = None
        residual_q10_by_hour: dict[int, float] = {}
        residual_q90_by_hour: dict[int, float] = {}

        if float(y_train.sum()) > 0.0:
            point_model = self._fit_model(objective="regression")
            calibration_row_count = max(1, int(np.ceil(len(training_rows) * CALIBRATION_FRACTION)))
            fit_rows = max(len(training_rows) - calibration_row_count, 1)
            x_fit = x_train.iloc[:fit_rows]
            y_fit = y_train[:fit_rows]
            point_model.fit(x_fit, y_fit)
            calibration_predictions = np.clip(point_model.predict(x_train), 0.0, None)
            residual_q10_by_hour, residual_q90_by_hour = self._build_residual_calibration(
                training_rows,
                calibration_predictions,
                calibration_start_index=fit_rows if fit_rows < len(training_rows) else 0,
            )
        print(
            "[debug][forecast] pipeline fit completed "
            f"point_model={'yes' if point_model is not None else 'no'} "
            f"calibrated_hours={len(residual_q10_by_hour)}"
        )

        return TrainedHourlyDemandArtifact(
            geography_scope=geography_scope,
            category_codes=category_codes,
            geography_codes=geography_codes,
            feature_names=feature_names,
            point_model=point_model,
            residual_q10_by_hour=residual_q10_by_hour,
            residual_q90_by_hour=residual_q90_by_hour,
            model_family=self.model_family,
            baseline_method=self.baseline_method,
        )

    def predict(
        self,
        artifact: TrainedHourlyDemandArtifact,
        prepared_features: dict[str, object],
    ) -> dict[str, object]:
        training_rows = list(prepared_features.get("training_rows", []))
        scoring_rows = list(prepared_features.get("rows", []))
        generated: list[dict[str, object]] = []
        print(
            "[debug][forecast] pipeline predict "
            f"scoring_rows={len(scoring_rows)} "
            f"point_model={'yes' if artifact.point_model is not None else 'no'} "
            f"calibrated_hours={len(artifact.residual_q10_by_hour)}"
        )

        if not scoring_rows:
            print("[debug][forecast] pipeline predict completed buckets=0")
            return {
                "model_family": artifact.model_family,
                "baseline_method": artifact.baseline_method,
                "geography_scope": artifact.geography_scope,
                "buckets": generated,
            }

        history_by_scope = self._history_from_training_rows(training_rows)
        sorted_rows = sorted(
            scoring_rows,
            key=lambda row: (
                row["bucket_start"],
                str(row.get("service_category") or ""),
                "" if row.get("geography_key") is None else str(row.get("geography_key")),
            ),
        )

        for row in sorted_rows:
            scope_key = self._scope_key(row)
            history = history_by_scope.setdefault(scope_key, {})
            dynamic_row = dict(row)
            dynamic_row.update(self._compute_dynamic_features(dynamic_row["bucket_start"], history))
            x_score = pd.DataFrame(
                [self._encode_row(dynamic_row, artifact.category_codes, artifact.geography_codes)],
                columns=artifact.feature_names,
                dtype=float,
            )

            if artifact.point_model is None:
                point_prediction = max(float(dynamic_row["historical_mean"]), 0.0)
            else:
                point_prediction = float(np.clip(artifact.point_model.predict(x_score)[0], 0.0, None))

            p10_prediction, p90_prediction = self._apply_residual_interval(dynamic_row, point_prediction, artifact)

            history[dynamic_row["bucket_start"]] = point_prediction

            baseline = _clamp_non_negative(float(dynamic_row["historical_mean"]))
            p50 = _clamp_non_negative(point_prediction)
            p10 = _clamp_non_negative(min(p10_prediction, point_prediction))
            p90 = _clamp_non_negative(max(p90_prediction, point_prediction))
            generated.append(
                {
                    "bucket_start": dynamic_row["bucket_start"],
                    "bucket_end": dynamic_row["bucket_end"],
                    "service_category": dynamic_row["service_category"],
                    "geography_key": dynamic_row["geography_key"],
                    "baseline_value": baseline,
                    "point_forecast": p50,
                    "quantile_p10": p10,
                    "quantile_p50": p50,
                    "quantile_p90": p90,
                }
            )
        print(
            "[debug][forecast] pipeline predict completed "
            f"buckets={len(generated)} "
            f"geography_scope={artifact.geography_scope}"
        )
        return {
            "model_family": artifact.model_family,
            "baseline_method": artifact.baseline_method,
            "geography_scope": artifact.geography_scope,
            "buckets": generated,
        }

    def run(self, prepared_features: dict[str, object]) -> dict[str, object]:
        artifact = self.fit(prepared_features)
        return self.predict(artifact, prepared_features)

    def _build_residual_calibration(
        self,
        training_rows: list[dict[str, object]],
        predictions: np.ndarray,
        *,
        calibration_start_index: int,
    ) -> tuple[dict[int, float], dict[int, float]]:
        calibration_rows = training_rows[calibration_start_index:] if calibration_start_index < len(training_rows) else training_rows
        calibration_predictions = predictions[calibration_start_index:] if calibration_start_index < len(predictions) else predictions
        residuals_by_hour: dict[int, list[float]] = {}

        for row, prediction in zip(calibration_rows, calibration_predictions):
            hour = int(row["hour_of_day"])
            residual = float(row["observed_count"]) - float(prediction)
            residuals_by_hour.setdefault(hour, []).append(residual)

        if not residuals_by_hour:
            return {}, {}

        all_residuals = np.array([residual for values in residuals_by_hour.values() for residual in values], dtype=float)
        global_q10 = float(np.quantile(all_residuals, 0.1))
        global_q90 = float(np.quantile(all_residuals, 0.9))

        residual_q10_by_hour: dict[int, float] = {}
        residual_q90_by_hour: dict[int, float] = {}
        for hour in range(24):
            hour_residuals = residuals_by_hour.get(hour)
            if not hour_residuals:
                residual_q10_by_hour[hour] = global_q10
                residual_q90_by_hour[hour] = global_q90
                continue
            residual_array = np.array(hour_residuals, dtype=float)
            residual_q10_by_hour[hour] = float(np.quantile(residual_array, 0.1))
            residual_q90_by_hour[hour] = float(np.quantile(residual_array, 0.9))
        return residual_q10_by_hour, residual_q90_by_hour

    def _apply_residual_interval(
        self,
        row: dict[str, object],
        point_prediction: float,
        artifact: TrainedHourlyDemandArtifact,
    ) -> tuple[float, float]:
        hour = int(row["hour_of_day"])
        q10_residual = artifact.residual_q10_by_hour.get(hour, -0.2 * point_prediction)
        q90_residual = artifact.residual_q90_by_hour.get(hour, 0.2 * point_prediction)
        p10_prediction = max(point_prediction + q10_residual, 0.0)
        p90_prediction = max(point_prediction + q90_residual, point_prediction)
        return p10_prediction, p90_prediction

    def _fit_model(self, *, objective: str, alpha: float | None = None) -> lgb.LGBMRegressor:
        kwargs: dict[str, object] = {
            "objective": objective,
            "n_estimators": 80,
            "learning_rate": 0.08,
            "num_leaves": 15,
            "min_child_samples": 8,
            "subsample": 0.9,
            "colsample_bytree": 0.9,
            "random_state": 42,
            "verbosity": -1,
        }
        return lgb.LGBMRegressor(**kwargs)

    def _feature_names(self) -> list[str]:
        return [
            "service_category_code",
            "geography_code",
            "hour_of_day",
            "day_of_week",
            "day_of_year",
            "month",
            "is_weekend",
            "is_holiday",
            "weather_temperature_c",
            "weather_precipitation_mm",
            "historical_mean",
            "lag_1h",
            "lag_24h",
            "lag_168h",
            "rolling_mean_24h",
            "rolling_mean_168h",
        ]

    def _build_codes(self, rows: list[dict[str, object]], key: str) -> dict[object, int]:
        values = sorted({row.get(key) for row in rows}, key=lambda value: "" if value is None else str(value))
        return {value: index for index, value in enumerate(values)}

    def _encode_row(self, row: dict[str, object], category_codes: dict[object, int], geography_codes: dict[object, int]) -> list[float]:
        return [
            float(category_codes.get(row.get("service_category"), 0)),
            float(geography_codes.get(row.get("geography_key"), 0)),
            float(row["hour_of_day"]),
            float(row["day_of_week"]),
            float(row["day_of_year"]),
            float(row["month"]),
            1.0 if row["is_weekend"] else 0.0,
            1.0 if row["is_holiday"] else 0.0,
            float(row["weather_temperature_c"]),
            float(row["weather_precipitation_mm"]),
            float(row["historical_mean"]),
            float(row.get("lag_1h", 0.0)),
            float(row.get("lag_24h", 0.0)),
            float(row.get("lag_168h", 0.0)),
            float(row.get("rolling_mean_24h", 0.0)),
            float(row.get("rolling_mean_168h", 0.0)),
        ]

    def _history_from_training_rows(self, training_rows: list[dict[str, object]]) -> dict[tuple[str, str | None], dict[datetime, float]]:
        history_by_scope: dict[tuple[str, str | None], dict[datetime, float]] = {}
        for row in training_rows:
            history = history_by_scope.setdefault(self._scope_key(row), {})
            history[row["bucket_start"]] = float(row.get("observed_count", 0.0))
        return history_by_scope

    def _compute_dynamic_features(self, bucket_start: datetime, history: dict[datetime, float]) -> dict[str, float]:
        features: dict[str, float] = {}
        for lag_hour in self.lag_hours:
            features[f"lag_{lag_hour}h"] = float(history.get(bucket_start - timedelta(hours=lag_hour), 0.0))
        for window in self.rolling_windows:
            total = 0.0
            for offset in range(1, window + 1):
                total += float(history.get(bucket_start - timedelta(hours=offset), 0.0))
            features[f"rolling_mean_{window}h"] = total / float(window)
        return features

    def _scope_key(self, row: dict[str, object]) -> tuple[str, str | None]:
        return str(row["service_category"]), row.get("geography_key") if row.get("geography_key") is None else str(row.get("geography_key"))
