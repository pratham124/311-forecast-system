from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from app.pipelines.forecasting.feature_preparation import prepare_forecast_features
from app.pipelines.forecasting.hourly_demand_pipeline import HourlyDemandPipeline
from app.services.forecast_bucket_service import ForecastBucketService
from app.services.forecast_service import compute_forecast_horizon


@pytest.mark.unit
def test_feature_preparation_uses_category_only_when_geography_missing() -> None:
    horizon_start = datetime(2026, 3, 20, 1, tzinfo=timezone.utc)
    horizon_end = horizon_start + timedelta(hours=24)

    prepared = prepare_forecast_features(
        dataset_records=[{"category": "Roads", "requested_at": "2026-03-18T10:00:00Z"}],
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        weather_rows=[],
        holidays=[],
        max_history_hours=24,
    )

    assert prepared["geography_scope"] == "category_only"
    assert len(prepared["rows"]) == 24
    assert "lag_1h" in prepared["training_rows"][0]


@pytest.mark.unit
def test_feature_preparation_zero_fills_history_and_builds_lag_features() -> None:
    horizon_start = datetime(2026, 3, 20, 4, tzinfo=timezone.utc)
    horizon_end = horizon_start + timedelta(hours=2)

    prepared = prepare_forecast_features(
        dataset_records=[
            {"category": "Roads", "requested_at": "2026-03-20T01:00:00Z", "ward": "Ward 1"},
            {"category": "Roads", "requested_at": "2026-03-20T03:00:00Z", "ward": "Ward 1"},
        ],
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        weather_rows=[],
        holidays=[],
        max_history_hours=4,
    )

    assert len(prepared["training_rows"]) == 4
    zero_hour = next(row for row in prepared["training_rows"] if row["bucket_start"] == datetime(2026, 3, 20, 2, tzinfo=timezone.utc))
    latest_hour = next(row for row in prepared["training_rows"] if row["bucket_start"] == datetime(2026, 3, 20, 3, tzinfo=timezone.utc))

    assert zero_hour["observed_count"] == 0.0
    assert zero_hour["weather_temperature_c"] is None
    assert zero_hour["weather_precipitation_mm"] is None
    assert zero_hour["weather_snowfall_mm"] is None
    assert zero_hour["weather_precipitation_probability_pct"] is None
    assert zero_hour["weather_is_missing"] is True
    assert latest_hour["lag_1h"] == 0.0
    assert latest_hour["lag_24h"] == 0.0
    assert latest_hour["rolling_mean_24h"] == pytest.approx(1.0 / 24.0)


@pytest.mark.unit
def test_pipeline_scores_recursively_using_prior_predictions(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeModel:
        def __init__(self, **kwargs):
            self.objective = kwargs.get("objective")

        def fit(self, x_train, y_train):
            return self

        def predict(self, x_score):
            return np.array([float(x_score.iloc[0]["lag_1h"]) + 1.0])

    monkeypatch.setattr("app.pipelines.forecasting.hourly_demand_pipeline.lgb.LGBMRegressor", FakeModel)

    prepared = {
        "geography_scope": "category_only",
        "training_rows": [
            {
                "service_category": "Roads",
                "geography_key": None,
                "hour_of_day": 22,
                "day_of_week": 3,
                "day_of_year": 78,
                "month": 3,
                "is_weekend": False,
                "is_holiday": False,
                "weather_temperature_c": 5.0,
                "weather_precipitation_mm": 0.0,
                "weather_snowfall_mm": 0.0,
                "weather_precipitation_probability_pct": 0.0,
                "historical_mean": 1.5,
                "observed_count": 1.0,
                "bucket_start": datetime(2026, 3, 19, 22, tzinfo=timezone.utc),
                "bucket_end": datetime(2026, 3, 19, 23, tzinfo=timezone.utc),
            },
            {
                "service_category": "Roads",
                "geography_key": None,
                "hour_of_day": 23,
                "day_of_week": 3,
                "day_of_year": 78,
                "month": 3,
                "is_weekend": False,
                "is_holiday": False,
                "weather_temperature_c": 5.0,
                "weather_precipitation_mm": 0.0,
                "weather_snowfall_mm": 0.0,
                "weather_precipitation_probability_pct": 0.0,
                "historical_mean": 1.5,
                "observed_count": 2.0,
                "bucket_start": datetime(2026, 3, 19, 23, tzinfo=timezone.utc),
                "bucket_end": datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
            },
        ],
        "rows": [
            {
                "service_category": "Roads",
                "geography_key": None,
                "hour_of_day": 0,
                "day_of_week": 4,
                "day_of_year": 79,
                "month": 3,
                "is_weekend": False,
                "is_holiday": False,
                "weather_temperature_c": 4.0,
                "weather_precipitation_mm": 0.1,
                "weather_snowfall_mm": 0.2,
                "weather_precipitation_probability_pct": 25.0,
                "historical_mean": 1.5,
                "bucket_start": datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
                "bucket_end": datetime(2026, 3, 20, 1, tzinfo=timezone.utc),
            },
            {
                "service_category": "Roads",
                "geography_key": None,
                "hour_of_day": 1,
                "day_of_week": 4,
                "day_of_year": 79,
                "month": 3,
                "is_weekend": False,
                "is_holiday": False,
                "weather_temperature_c": 4.0,
                "weather_precipitation_mm": 0.1,
                "weather_snowfall_mm": 0.2,
                "weather_precipitation_probability_pct": 25.0,
                "historical_mean": 1.5,
                "bucket_start": datetime(2026, 3, 20, 1, tzinfo=timezone.utc),
                "bucket_end": datetime(2026, 3, 20, 2, tzinfo=timezone.utc),
            },
            {
                "service_category": "Roads",
                "geography_key": None,
                "hour_of_day": 2,
                "day_of_week": 4,
                "day_of_year": 79,
                "month": 3,
                "is_weekend": False,
                "is_holiday": False,
                "weather_temperature_c": 4.0,
                "weather_precipitation_mm": 0.1,
                "weather_snowfall_mm": 0.2,
                "weather_precipitation_probability_pct": 25.0,
                "historical_mean": 1.5,
                "bucket_start": datetime(2026, 3, 20, 2, tzinfo=timezone.utc),
                "bucket_end": datetime(2026, 3, 20, 3, tzinfo=timezone.utc),
            },
        ],
    }

    generated = HourlyDemandPipeline().run(prepared)

    assert [bucket["point_forecast"] for bucket in generated["buckets"]] == [3.0, 4.0, 5.0]


@pytest.mark.unit
def test_pipeline_predict_uses_residual_calibration_for_intervals(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeModel:
        def __init__(self, **kwargs):
            pass

        def fit(self, x_train, y_train):
            return self

        def predict(self, x_score):
            return np.array([10.0])

    monkeypatch.setattr("app.pipelines.forecasting.hourly_demand_pipeline.lgb.LGBMRegressor", FakeModel)

    prepared = {
        "geography_scope": "category_only",
        "training_rows": [
            {
                "service_category": "Roads",
                "geography_key": None,
                "hour_of_day": hour,
                "day_of_week": 1,
                "day_of_year": 70 + hour,
                "month": 3,
                "is_weekend": False,
                "is_holiday": False,
                "weather_temperature_c": 5.0,
                "weather_precipitation_mm": 0.0,
                "weather_snowfall_mm": 0.0,
                "weather_precipitation_probability_pct": 0.0,
                "historical_mean": 8.0,
                "observed_count": float(10 + hour),
                "bucket_start": datetime(2026, 3, 10, tzinfo=timezone.utc) + timedelta(hours=hour),
                "bucket_end": datetime(2026, 3, 10, tzinfo=timezone.utc) + timedelta(hours=hour + 1),
            }
            for hour in range(10)
        ],
        "rows": [
            {
                "service_category": "Roads",
                "geography_key": None,
                "hour_of_day": 3,
                "day_of_week": 2,
                "day_of_year": 90,
                "month": 3,
                "is_weekend": False,
                "is_holiday": False,
                "weather_temperature_c": 4.0,
                "weather_precipitation_mm": 0.1,
                "weather_snowfall_mm": 0.5,
                "weather_precipitation_probability_pct": 30.0,
                "historical_mean": 8.0,
                "bucket_start": datetime(2026, 3, 20, 3, tzinfo=timezone.utc),
                "bucket_end": datetime(2026, 3, 20, 4, tzinfo=timezone.utc),
            }
        ],
    }

    pipeline = HourlyDemandPipeline()
    artifact = pipeline.fit(prepared)
    artifact.residual_q10_by_hour[3] = -2.0
    artifact.residual_q90_by_hour[3] = 5.0

    generated = pipeline.predict(artifact, prepared)
    bucket = generated["buckets"][0]

    assert bucket["point_forecast"] == 10.0
    assert bucket["quantile_p10"] == 8.0
    assert bucket["quantile_p50"] == 10.0
    assert bucket["quantile_p90"] == 15.0


@pytest.mark.unit
def test_pipeline_outputs_ordered_quantiles_and_24_hour_materialization() -> None:
    horizon_start = datetime(2026, 3, 20, 1, tzinfo=timezone.utc)
    horizon_end = horizon_start + timedelta(hours=24)
    prepared = prepare_forecast_features(
        dataset_records=[
            {
                "category": "Roads",
                "requested_at": "2026-03-18T10:00:00Z",
                "ward": "Ward 1",
            }
        ],
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        weather_rows=[],
        holidays=[],
        max_history_hours=24,
    )

    generated = HourlyDemandPipeline().run(prepared)
    buckets, geography_scope = ForecastBucketService().build_buckets(generated)

    assert geography_scope == "category_and_geography"
    assert len(buckets) == 24
    assert all(bucket["quantile_p10"] <= bucket["quantile_p50"] <= bucket["quantile_p90"] for bucket in buckets)


@pytest.mark.unit
def test_hourly_pipeline_supports_scoring_with_older_artifact_feature_names() -> None:
    class FakeModel:
        def predict(self, x_score):
            return np.array([float(x_score.iloc[0]["weather_precipitation_mm"]) + 1.0])

    artifact = type(
        "Artifact",
        (),
        {
            "geography_scope": "category_only",
            "category_codes": {"Roads": 0},
            "geography_codes": {None: 0},
            "feature_names": [
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
            ],
            "point_model": FakeModel(),
            "residual_q10_by_hour": {},
            "residual_q90_by_hour": {},
            "model_family": "lightgbm_global",
            "baseline_method": "historical_hourly_mean",
        },
    )()

    generated = HourlyDemandPipeline().predict(
        artifact,
        {
            "training_rows": [],
            "rows": [
                {
                    "service_category": "Roads",
                    "geography_key": None,
                    "hour_of_day": 0,
                    "day_of_week": 4,
                    "day_of_year": 79,
                    "month": 3,
                    "is_weekend": False,
                    "is_holiday": False,
                    "weather_temperature_c": 4.0,
                    "weather_precipitation_mm": 0.25,
                    "weather_snowfall_mm": 0.5,
                    "weather_precipitation_probability_pct": 60.0,
                    "historical_mean": 1.5,
                    "bucket_start": datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
                    "bucket_end": datetime(2026, 3, 20, 1, tzinfo=timezone.utc),
                }
            ],
        },
    )

    assert generated["buckets"][0]["point_forecast"] == 1.25


@pytest.mark.unit
def test_compute_forecast_horizon_rounds_to_next_hour_window() -> None:
    start, end = compute_forecast_horizon(datetime(2026, 3, 20, 10, 23, tzinfo=timezone.utc))
    assert start == datetime(2026, 3, 20, 11, 0, tzinfo=timezone.utc)
    assert end - start == timedelta(hours=24)


@pytest.mark.unit
def test_pipeline_residual_calibration_returns_empty_maps_without_rows() -> None:
    from app.pipelines.forecasting.hourly_demand_pipeline import TrainedHourlyDemandArtifact

    pipeline = HourlyDemandPipeline()
    q10, q90 = pipeline._build_residual_calibration([], np.array([], dtype=float), calibration_start_index=0)

    assert q10 == {}
    assert q90 == {}
