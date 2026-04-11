from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.pipelines.forecasting.hourly_demand_pipeline import HourlyDemandPipeline, TrainedHourlyDemandArtifact
from app.pipelines.forecasting.weekly_demand_pipeline import WeeklyDemandPipeline, TrainedWeeklyDemandArtifact
from app.repositories.alert_detail_repository import AlertDetailRepository
from app.schemas.alert_details import (
    AlertAnomaliesComponentRead,
    AlertDistributionComponentRead,
    AlertDriversComponentRead,
)
from app.services import alert_detail_service as service_module
from app.services.alert_detail_service import (
    AlertDetailService,
    _ComponentOutcome,
    _ResolvedAlertSource,
    _ensure_utc,
    _fetch_forecast_weather,
    _fetch_historical_weather,
    _merge_weather_rows,
)


pytestmark = pytest.mark.unit


class FakePointModel:
    def __init__(self, *, prediction: float = 4.0, contrib_rows: list[list[float]] | None = None) -> None:
        self.prediction = prediction
        self.contrib_rows = contrib_rows or [[0.0, 0.0]]

    def predict(self, frame, pred_contrib: bool = False):
        if pred_contrib:
            return self.contrib_rows
        return [self.prediction] * len(frame)


def _build_service(**overrides) -> AlertDetailService:
    defaults = {
        "alert_detail_repository": SimpleNamespace(
            create_load=lambda **kwargs: SimpleNamespace(alert_detail_load_id="load-1"),
            finalize_load=lambda *args, **kwargs: None,
            require_load=lambda alert_detail_load_id: SimpleNamespace(
                alert_detail_load_id=alert_detail_load_id,
                requested_by_subject="test-user",
                alert_source="threshold_alert",
                alert_id="alert-1",
                render_status=None,
            ),
            record_render_event=lambda *args, **kwargs: SimpleNamespace(
                alert_source="threshold_alert",
                alert_id="alert-1",
            ),
        ),
        "notification_event_repository": SimpleNamespace(get_event_bundle=lambda alert_id: None),
        "threshold_evaluation_repository": SimpleNamespace(get_run=lambda run_id: None),
        "surge_notification_event_repository": SimpleNamespace(get_event_bundle=lambda alert_id: None),
        "surge_evaluation_repository": SimpleNamespace(
            get_candidate_bundle=lambda candidate_id: None,
            list_candidate_bundles_for_window=lambda **kwargs: [],
        ),
        "forecast_repository": SimpleNamespace(
            get_forecast_version=lambda forecast_version_id: None,
            list_buckets=lambda forecast_version_id: [],
        ),
        "weekly_forecast_repository": SimpleNamespace(
            get_forecast_version=lambda forecast_version_id: None,
            list_buckets=lambda forecast_version_id: [],
        ),
        "cleaned_dataset_repository": SimpleNamespace(list_dataset_records=lambda cleaned_dataset_version_id: []),
        "forecast_model_repository": SimpleNamespace(find_current_model=lambda product_name: None),
        "forecast_training_service": SimpleNamespace(load_artifact_bundle=lambda artifact_path: None),
        "weekly_forecast_training_service": SimpleNamespace(load_artifact_bundle=lambda artifact_path: None),
        "geomet_client": SimpleNamespace(),
        "nager_date_client": SimpleNamespace(fetch_holidays=lambda year: []),
        "settings": SimpleNamespace(
            forecast_product_name="daily_1_day_demand",
            weekly_forecast_product_name="weekly_7_day_demand",
            forecast_training_lookback_days=7,
            weekly_forecast_timezone="America/Edmonton",
        ),
        "logger": SimpleNamespace(info=lambda *args, **kwargs: None),
    }
    defaults.update(overrides)
    return AlertDetailService(**defaults)


def _resolved(**overrides) -> _ResolvedAlertSource:
    defaults = {
        "alert_source": "threshold_alert",
        "alert_id": "alert-1",
        "correlation_id": "corr-1",
        "service_category": "Roads",
        "geography_type": None,
        "geography_value": None,
        "alert_triggered_at": datetime(2026, 4, 1, 10, tzinfo=timezone.utc),
        "overall_delivery_status": "delivered",
        "forecast_product": "daily",
        "forecast_reference_id": "forecast-1",
        "forecast_window_type": "hourly",
        "window_start": datetime(2026, 4, 1, 10, tzinfo=timezone.utc),
        "window_end": datetime(2026, 4, 1, 11, tzinfo=timezone.utc),
        "primary_metric_label": "Forecast",
        "primary_metric_value": 12.0,
        "secondary_metric_label": "Threshold",
        "secondary_metric_value": 8.0,
        "threshold_evaluation_run_id": "threshold-run-1",
        "surge_evaluation_run_id": None,
        "surge_candidate_id": None,
    }
    defaults.update(overrides)
    return _ResolvedAlertSource(**defaults)


def test_utc_and_weather_helpers_cover_all_client_paths() -> None:
    naive = datetime(2026, 4, 1, 10, 15)
    aware = datetime(2026, 4, 1, 4, 15, tzinfo=timezone(timedelta(hours=-6)))
    utc_naive = _ensure_utc(naive)
    utc_aware = _ensure_utc(aware)

    assert utc_naive.tzinfo == timezone.utc
    assert utc_naive.hour == 10
    assert utc_aware == datetime(2026, 4, 1, 10, 15, tzinfo=timezone.utc)

    start = datetime(2026, 4, 1, 10, tzinfo=timezone.utc)
    end = start + timedelta(hours=1)

    historical_client = SimpleNamespace(
        fetch_historical_hourly_conditions=lambda *_: [{"timestamp": start, "temperature": 1.0}],
    )
    forecast_client = SimpleNamespace(
        fetch_forecast_hourly_conditions=lambda *_: [{"timestamp": start + timedelta(minutes=30), "temperature": 1.5}],
    )
    fallback_client = SimpleNamespace(
        fetch_hourly_conditions=lambda *_: [{"timestamp": end, "temperature": 2.0}],
    )

    assert _fetch_historical_weather(historical_client, start, end) == [{"timestamp": start, "temperature": 1.0}]
    assert _fetch_historical_weather(fallback_client, start, end) == [{"timestamp": end, "temperature": 2.0}]
    assert _fetch_historical_weather(SimpleNamespace(), start, end) == []
    assert _fetch_forecast_weather(forecast_client, start, end) == [
        {"timestamp": start + timedelta(minutes=30), "temperature": 1.5}
    ]
    assert _fetch_forecast_weather(fallback_client, start, end) == [{"timestamp": end, "temperature": 2.0}]
    assert _fetch_forecast_weather(SimpleNamespace(), start, end) == []

    merged = _merge_weather_rows(
        [{"timestamp": start, "temperature": 1.0}, {"timestamp": "not-a-datetime", "temperature": 99.0}],
        [{"timestamp": start, "temperature": 5.0}, {"timestamp": end, "temperature": 2.0}],
    )
    assert merged == [
        {"timestamp": start, "temperature": 5.0},
        {"timestamp": end, "temperature": 2.0},
    ]


def test_alert_detail_repository_preserves_terminal_render_failure(session) -> None:
    repository = AlertDetailRepository(session)
    load = repository.create_load(
        alert_source="threshold_alert",
        alert_id="alert-1",
        requested_by_subject="owner",
    )

    repository.finalize_load(
        load.alert_detail_load_id,
        view_status="partial",
        distribution_status="available",
        drivers_status="unavailable",
        anomalies_status="unavailable",
        preparation_status="completed",
        failure_reason=None,
        source_forecast_version_id="forecast-1",
        source_threshold_evaluation_run_id="threshold-run-1",
        correlation_id="corr-1",
    )
    recorded = repository.record_render_event(
        load.alert_detail_load_id,
        render_status="render_failed",
        failure_reason="chart crashed",
    )
    unchanged = repository.record_render_event(load.alert_detail_load_id, render_status="rendered")

    assert recorded.source_forecast_version_id == "forecast-1"
    assert recorded.source_threshold_evaluation_run_id == "threshold-run-1"
    assert recorded.correlation_id == "corr-1"
    assert unchanged.render_status == "render_failed"
    assert unchanged.view_status == "error"
    assert unchanged.failure_reason == "chart crashed"

    weekly = repository.create_load(
        alert_source="surge_alert",
        alert_id="alert-2",
        requested_by_subject="owner",
    )
    repository.finalize_load(
        weekly.alert_detail_load_id,
        view_status="rendered",
        distribution_status="available",
        drivers_status="available",
        anomalies_status="available",
        preparation_status="completed",
        source_weekly_forecast_version_id="weekly-forecast-1",
        source_surge_evaluation_run_id="surge-run-1",
        source_surge_candidate_id="surge-candidate-1",
    )
    rendered = repository.record_render_event(weekly.alert_detail_load_id, render_status="rendered")

    assert rendered.source_weekly_forecast_version_id == "weekly-forecast-1"
    assert rendered.source_surge_evaluation_run_id == "surge-run-1"
    assert rendered.source_surge_candidate_id == "surge-candidate-1"
    assert rendered.render_status == "rendered"
    assert rendered.view_status == "rendered"

    with pytest.raises(LookupError):
        repository.require_load("missing-load")


def test_resolve_alert_source_covers_threshold_surge_and_errors() -> None:
    now = datetime(2026, 4, 1, 10, tzinfo=timezone.utc)
    threshold_bundle = SimpleNamespace(
        event=SimpleNamespace(
            notification_event_id="threshold-event-1",
            service_category="Roads",
            geography_type="ward",
            geography_value="Ward 1",
            created_at=now,
            overall_delivery_status="delivered",
            forecast_window_type="hourly",
            forecast_window_start=now,
            forecast_window_end=now + timedelta(hours=1),
            forecast_value=12,
            threshold_value=8,
            threshold_evaluation_run_id="threshold-run-1",
        )
    )
    threshold_run = SimpleNamespace(
        forecast_product="daily",
        forecast_version_reference="forecast-1",
    )
    surge_bundle = SimpleNamespace(
        event=SimpleNamespace(
            correlation_id="surge-corr-1",
            service_category="Waste",
            created_at=now + timedelta(minutes=5),
            overall_delivery_status="partial_delivery",
            forecast_product="daily",
            evaluation_window_start=now,
            evaluation_window_end=now + timedelta(hours=1),
            actual_demand_value=6,
            forecast_p50_value=2,
            surge_evaluation_run_id="surge-run-1",
            surge_candidate_id="surge-candidate-1",
        )
    )
    candidate_bundle = SimpleNamespace(candidate=SimpleNamespace(forecast_version_id="forecast-2"))

    service = _build_service(
        notification_event_repository=SimpleNamespace(
            get_event_bundle=lambda alert_id: threshold_bundle if alert_id == "threshold-event-1" else None,
        ),
        threshold_evaluation_repository=SimpleNamespace(get_run=lambda run_id: threshold_run),
        surge_notification_event_repository=SimpleNamespace(
            get_event_bundle=lambda alert_id: surge_bundle if alert_id == "surge-event-1" else None,
        ),
        surge_evaluation_repository=SimpleNamespace(
            get_candidate_bundle=lambda candidate_id: candidate_bundle if candidate_id == "surge-candidate-1" else None,
            list_candidate_bundles_for_window=lambda **kwargs: [],
        ),
    )

    threshold = service._resolve_alert_source(alert_source="threshold_alert", alert_id="threshold-event-1")
    surge = service._resolve_alert_source(alert_source="surge_alert", alert_id="surge-event-1")

    assert threshold.correlation_id == "threshold-event-1"
    assert threshold.geography_value == "Ward 1"
    assert threshold.forecast_reference_id == "forecast-1"
    assert surge.correlation_id == "surge-corr-1"
    assert surge.primary_metric_label == "Actual demand"
    assert surge.forecast_reference_id == "forecast-2"

    with pytest.raises(HTTPException) as threshold_missing:
        service._resolve_alert_source(alert_source="threshold_alert", alert_id="missing-threshold")
    assert threshold_missing.value.status_code == 404

    with pytest.raises(HTTPException) as surge_missing:
        service._resolve_alert_source(alert_source="surge_alert", alert_id="missing-surge")
    assert surge_missing.value.status_code == 404

    with pytest.raises(HTTPException) as unsupported:
        service._resolve_alert_source(alert_source="unsupported", alert_id="missing")
    assert unsupported.value.status_code == 422


def test_classification_execute_component_and_feature_group_branches() -> None:
    service = _build_service()

    assert service._classify_view_status(
        distribution_status="failed",
        drivers_status="available",
        anomalies_status="available",
        distribution_reason="distribution failed",
        drivers_reason=None,
        anomalies_reason=None,
    ) == ("error", "distribution failed")
    assert service._classify_view_status(
        distribution_status="unavailable",
        drivers_status="unavailable",
        anomalies_status="unavailable",
        distribution_reason="a",
        drivers_reason="b",
        anomalies_reason="c",
    ) == ("unavailable", "All detail components were unavailable for this alert.")
    assert service._classify_view_status(
        distribution_status="available",
        drivers_status="available",
        anomalies_status="available",
        distribution_reason=None,
        drivers_reason=None,
        anomalies_reason=None,
    ) == ("rendered", None)
    assert service._classify_view_status(
        distribution_status="available",
        drivers_status="unavailable",
        anomalies_status="available",
        distribution_reason=None,
        drivers_reason="x",
        anomalies_reason=None,
    ) == ("partial", None)

    success = service._execute_component(
        "load-1",
        "drivers",
        lambda: _ComponentOutcome(
            status="available",
            payload=AlertDriversComponentRead(status="available", drivers=[]),
        ),
    )
    distribution_failure = service._execute_component("load-1", "distribution", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    drivers_failure = service._execute_component("load-1", "drivers", lambda: (_ for _ in ()).throw(RuntimeError("pow")))
    anomalies_failure = service._execute_component("load-1", "anomalies", lambda: (_ for _ in ()).throw(RuntimeError("zap")))

    assert success.status == "available"
    assert isinstance(distribution_failure.payload, AlertDistributionComponentRead)
    assert distribution_failure.payload.status == "failed"
    assert isinstance(drivers_failure.payload, AlertDriversComponentRead)
    assert drivers_failure.payload.status == "failed"
    assert isinstance(anomalies_failure.payload, AlertAnomaliesComponentRead)
    assert anomalies_failure.payload.status == "failed"

    assert service._resolve_daily_feature_group("service_category_code") == "Service category"
    assert service._resolve_daily_feature_group("geography_code") == "Geography"
    assert service._resolve_daily_feature_group("hour_of_day") == "Hour of day"
    assert service._resolve_daily_feature_group("day_of_week") == "Calendar seasonality"
    assert service._resolve_daily_feature_group("is_weekend") == "Holiday / weekend"
    assert service._resolve_daily_feature_group("weather_temperature_c") == "Weather"
    assert service._resolve_daily_feature_group("historical_mean") == "Historical average"
    assert service._resolve_daily_feature_group("lag_1h") == "Recent demand"
    assert service._resolve_daily_feature_group("rolling_mean_24h") == "Rolling demand trend"
    assert service._resolve_daily_feature_group("custom_feature") == "custom_feature"

    assert service._resolve_weekly_feature_group("service_category_code") == "Service category"
    assert service._resolve_weekly_feature_group("geography_code") == "Geography"
    assert service._resolve_weekly_feature_group("day_of_week") == "Calendar seasonality"
    assert service._resolve_weekly_feature_group("is_holiday") == "Holiday / weekend"
    assert service._resolve_weekly_feature_group("avg_temperature_c") == "Weather"
    assert service._resolve_weekly_feature_group("total_precipitation_mm") == "Weather"
    assert service._resolve_weekly_feature_group("total_snowfall_mm") == "Weather"
    assert service._resolve_weekly_feature_group("weather_is_missing") == "Weather"
    assert service._resolve_weekly_feature_group("historical_mean") == "Historical average"
    assert service._resolve_weekly_feature_group("lag_7d") == "Recent demand"
    assert service._resolve_weekly_feature_group("rolling_mean_7d") == "Rolling demand trend"
    assert service._resolve_weekly_feature_group("custom_feature") == "custom_feature"


def test_distribution_context_covers_daily_weekly_and_unlinked_paths() -> None:
    start = datetime(2026, 4, 1, 10, tzinfo=timezone.utc)
    daily_version = SimpleNamespace(
        source_cleaned_dataset_version_id="dataset-1",
        horizon_start=start,
        horizon_end=start + timedelta(hours=2),
    )
    daily_buckets = [
        SimpleNamespace(
            service_category="Roads",
            geography_key="Ward 1",
            bucket_start=start,
            bucket_end=start + timedelta(hours=1),
            quantile_p10=0.5,
            quantile_p50=1.0,
            quantile_p90=1.5,
        ),
        SimpleNamespace(
            service_category="Roads",
            geography_key="Ward 1",
            bucket_start=start,
            bucket_end=start + timedelta(hours=1),
            quantile_p10=1.0,
            quantile_p50=2.0,
            quantile_p90=3.0,
        ),
        SimpleNamespace(
            service_category="Roads",
            geography_key="Ward 2",
            bucket_start=start + timedelta(hours=1),
            bucket_end=start + timedelta(hours=2),
            quantile_p10=5.0,
            quantile_p50=6.0,
            quantile_p90=7.0,
        ),
        SimpleNamespace(
            service_category="Waste",
            geography_key="Ward 1",
            bucket_start=start,
            bucket_end=start + timedelta(hours=1),
            quantile_p10=9.0,
            quantile_p50=10.0,
            quantile_p90=11.0,
        ),
    ]
    weekly_version = SimpleNamespace(
        source_cleaned_dataset_version_id="dataset-1",
        week_start_local=start,
        week_end_local=start + timedelta(days=3),
    )
    weekly_buckets = [
        SimpleNamespace(
            forecast_date_local=date(2026, 4, 1),
            service_category="Roads",
            geography_key="Ward 1",
            quantile_p10=1.0,
            quantile_p50=1.5,
            quantile_p90=2.0,
        ),
        SimpleNamespace(
            forecast_date_local=date(2026, 4, 1),
            service_category="Roads",
            geography_key="Ward 1",
            quantile_p10=4.0,
            quantile_p50=5.0,
            quantile_p90=6.0,
        ),
        SimpleNamespace(
            forecast_date_local=date(2026, 4, 2),
            service_category="Roads",
            geography_key="Ward 1",
            quantile_p10=6.0,
            quantile_p50=7.0,
            quantile_p90=8.0,
        ),
        SimpleNamespace(
            forecast_date_local=date(2026, 4, 2),
            service_category="Waste",
            geography_key="Ward 1",
            quantile_p10=9.0,
            quantile_p50=10.0,
            quantile_p90=11.0,
        ),
    ]

    daily_service = _build_service(
        forecast_repository=SimpleNamespace(
            get_forecast_version=lambda forecast_version_id: daily_version if forecast_version_id == "forecast-1" else None,
            list_buckets=lambda forecast_version_id: daily_buckets,
        ),
        weekly_forecast_repository=SimpleNamespace(
            get_forecast_version=lambda forecast_version_id: weekly_version if forecast_version_id == "weekly-1" else None,
            list_buckets=lambda forecast_version_id: weekly_buckets,
        ),
    )

    daily_available = daily_service._build_distribution_context(
        _resolved(
            geography_value="Ward 1",
            forecast_product="daily",
            forecast_reference_id="forecast-1",
            window_start=start,
            window_end=start + timedelta(hours=1),
        )
    )
    daily_missing = daily_service._build_distribution_context(
        _resolved(forecast_product="daily", forecast_reference_id="missing-forecast")
    )
    daily_no_points = daily_service._build_distribution_context(
        _resolved(
            geography_value="Ward 9",
            forecast_product="daily",
            forecast_reference_id="forecast-1",
        )
    )
    weekly_available = daily_service._build_distribution_context(
        _resolved(
            forecast_product="weekly",
            forecast_reference_id="weekly-1",
            geography_value="Ward 1",
            window_start=start,
            window_end=start + timedelta(days=1),
        )
    )
    weekly_missing = daily_service._build_distribution_context(
        _resolved(forecast_product="weekly", forecast_reference_id="missing-weekly")
    )
    weekly_no_points = daily_service._build_distribution_context(
        _resolved(
            forecast_product="weekly",
            forecast_reference_id="weekly-1",
            geography_value="Ward 9",
        )
    )
    unlinked = daily_service._build_distribution_context(_resolved(forecast_product=None, forecast_reference_id=None))

    assert daily_available.status == "available"
    assert daily_available.payload.summary_value == 3.0
    assert [point.p50 for point in daily_available.payload.points] == [3.0]
    assert daily_missing.status == "failed"
    assert daily_missing.reason == "Forecast version not found."
    assert daily_no_points.status == "unavailable"
    assert weekly_available.status == "available"
    assert weekly_available.payload.granularity == "daily"
    assert [point.p50 for point in weekly_available.payload.points] == [6.5, 7.0]
    assert weekly_missing.status == "failed"
    assert weekly_missing.reason == "Weekly forecast version not found."
    assert weekly_no_points.status == "unavailable"
    assert unlinked.status == "unavailable"


def test_daily_driver_context_covers_all_branch_outcomes(monkeypatch: pytest.MonkeyPatch) -> None:
    start = datetime(2026, 4, 1, 10, tzinfo=timezone.utc)
    version = SimpleNamespace(
        source_cleaned_dataset_version_id="dataset-1",
        horizon_start=start,
        horizon_end=start + timedelta(hours=2),
    )
    stored_model = SimpleNamespace(
        source_cleaned_dataset_version_id="dataset-1",
        feature_schema_version=HourlyDemandPipeline.feature_schema_version,
        artifact_path="artifact.bin",
    )
    artifact_without_point = TrainedHourlyDemandArtifact(
        geography_scope="citywide",
        category_codes={"Roads": 0},
        geography_codes={"Ward 1": 0, "Ward 2": 1},
        feature_names=["service_category_code"],
        point_model=None,
        residual_q10_by_hour={},
        residual_q90_by_hour={},
        model_family="lightgbm",
        baseline_method="historical",
    )
    artifact_with_point = TrainedHourlyDemandArtifact(
        geography_scope="citywide",
        category_codes={"Roads": 0},
        geography_codes={"Ward 1": 0, "Ward 2": 1},
        feature_names=[
            "service_category_code",
            "month",
            "weather_temperature_c",
            "historical_mean",
            "lag_1h",
            "rolling_mean_24h",
        ],
        point_model=FakePointModel(
            prediction=4.0,
            contrib_rows=[[0.25, 0.2, 1.5, 0.1, -2.0, 0.3, 0.0]],
        ),
        residual_q10_by_hour={},
        residual_q90_by_hour={},
        model_family="lightgbm",
        baseline_method="historical",
    )
    prepared_rows = {
        "training_rows": [
            {
                "bucket_start": start - timedelta(hours=1),
                "service_category": "Roads",
                "geography_key": "Ward 1",
                "observed_count": 2.0,
            }
        ],
        "rows": [
            {
                "bucket_start": start,
                "bucket_end": start + timedelta(hours=1),
                "service_category": "Waste",
                "geography_key": "Ward 1",
                "hour_of_day": 10,
                "day_of_week": 2,
                "day_of_year": 91,
                "month": 4,
                "is_weekend": False,
                "is_holiday": False,
                "weather_is_missing": False,
                "weather_temperature_c": 1.0,
                "weather_precipitation_mm": 0.0,
                "weather_snowfall_mm": 0.0,
                "weather_precipitation_probability_pct": 15.0,
                "historical_mean": 2.0,
            },
            {
                "bucket_start": start,
                "bucket_end": start + timedelta(hours=2),
                "service_category": "Roads",
                "geography_key": "Ward 1",
                "hour_of_day": 10,
                "day_of_week": 2,
                "day_of_year": 91,
                "month": 4,
                "is_weekend": False,
                "is_holiday": False,
                "weather_is_missing": False,
                "weather_temperature_c": 2.5,
                "weather_precipitation_mm": 0.0,
                "weather_snowfall_mm": 0.0,
                "weather_precipitation_probability_pct": 8.0,
                "historical_mean": 3.5,
            },
            {
                "bucket_start": start,
                "bucket_end": start + timedelta(hours=1),
                "service_category": "Roads",
                "geography_key": "Ward 2",
                "hour_of_day": 10,
                "day_of_week": 2,
                "day_of_year": 91,
                "month": 4,
                "is_weekend": False,
                "is_holiday": False,
                "weather_is_missing": False,
                "weather_temperature_c": 2.0,
                "weather_precipitation_mm": 0.0,
                "weather_snowfall_mm": 0.0,
                "weather_precipitation_probability_pct": 10.0,
                "historical_mean": 3.0,
            },
            {
                "bucket_start": start,
                "bucket_end": start + timedelta(hours=1),
                "service_category": "Roads",
                "geography_key": "Ward 1",
                "hour_of_day": 10,
                "day_of_week": 2,
                "day_of_year": 91,
                "month": 4,
                "is_weekend": False,
                "is_holiday": False,
                "weather_is_missing": False,
                "weather_temperature_c": 3.0,
                "weather_precipitation_mm": 0.0,
                "weather_snowfall_mm": 0.0,
                "weather_precipitation_probability_pct": 5.0,
                "historical_mean": 4.0,
            },
        ],
    }
    original_rows = list(prepared_rows["rows"])
    monkeypatch.setattr(service_module, "_fetch_historical_weather", lambda *args, **kwargs: [])
    monkeypatch.setattr(service_module, "_fetch_forecast_weather", lambda *args, **kwargs: [])
    monkeypatch.setattr(service_module, "prepare_forecast_features", lambda **kwargs: prepared_rows)

    resolved = _resolved(
        forecast_product="daily",
        geography_value="Ward 1",
        forecast_reference_id="forecast-1",
        window_start=start,
        window_end=start + timedelta(hours=1),
    )

    missing_version_service = _build_service(
        forecast_repository=SimpleNamespace(get_forecast_version=lambda forecast_version_id: None),
    )
    no_model_service = _build_service(
        forecast_repository=SimpleNamespace(get_forecast_version=lambda forecast_version_id: version),
    )
    mismatch_lineage_service = _build_service(
        forecast_repository=SimpleNamespace(get_forecast_version=lambda forecast_version_id: version),
        forecast_model_repository=SimpleNamespace(
            find_current_model=lambda product_name: SimpleNamespace(
                source_cleaned_dataset_version_id="dataset-2",
                feature_schema_version=HourlyDemandPipeline.feature_schema_version,
                artifact_path="artifact.bin",
            )
        ),
    )
    mismatch_schema_service = _build_service(
        forecast_repository=SimpleNamespace(get_forecast_version=lambda forecast_version_id: version),
        forecast_model_repository=SimpleNamespace(
            find_current_model=lambda product_name: SimpleNamespace(
                source_cleaned_dataset_version_id="dataset-1",
                feature_schema_version="legacy-schema",
                artifact_path="artifact.bin",
            )
        ),
    )
    artifact_missing_point_service = _build_service(
        forecast_repository=SimpleNamespace(get_forecast_version=lambda forecast_version_id: version),
        forecast_model_repository=SimpleNamespace(find_current_model=lambda product_name: stored_model),
        forecast_training_service=SimpleNamespace(load_artifact_bundle=lambda artifact_path: artifact_without_point),
    )
    no_rows_service = _build_service(
        forecast_repository=SimpleNamespace(get_forecast_version=lambda forecast_version_id: version),
        forecast_model_repository=SimpleNamespace(find_current_model=lambda product_name: stored_model),
        forecast_training_service=SimpleNamespace(load_artifact_bundle=lambda artifact_path: artifact_with_point),
        cleaned_dataset_repository=SimpleNamespace(list_dataset_records=lambda cleaned_dataset_version_id: []),
    )
    available_service = _build_service(
        forecast_repository=SimpleNamespace(get_forecast_version=lambda forecast_version_id: version),
        forecast_model_repository=SimpleNamespace(find_current_model=lambda product_name: stored_model),
        forecast_training_service=SimpleNamespace(load_artifact_bundle=lambda artifact_path: artifact_with_point),
        cleaned_dataset_repository=SimpleNamespace(list_dataset_records=lambda cleaned_dataset_version_id: []),
    )

    missing_version = missing_version_service._build_daily_driver_context(resolved)
    no_model = no_model_service._build_daily_driver_context(resolved)
    mismatch_lineage = mismatch_lineage_service._build_daily_driver_context(resolved)
    mismatch_schema = mismatch_schema_service._build_daily_driver_context(resolved)
    missing_point = artifact_missing_point_service._build_daily_driver_context(resolved)

    prepared_rows["rows"] = []
    no_rows = no_rows_service._build_daily_driver_context(resolved)

    prepared_rows["rows"] = original_rows
    available = available_service._build_daily_driver_context(resolved)

    assert missing_version.status == "failed"
    assert no_model.status == "unavailable"
    assert mismatch_lineage.status == "unavailable"
    assert mismatch_schema.status == "unavailable"
    assert missing_point.status == "unavailable"
    assert no_rows.status == "unavailable"
    assert available.status == "available"
    assert [driver.label for driver in available.payload.drivers] == [
        "Recent demand",
        "Weather",
        "Rolling demand trend",
        "Service category",
        "Calendar seasonality",
    ]

    no_model_artifact = TrainedHourlyDemandArtifact(
        geography_scope="citywide",
        category_codes={"Roads": 0},
        geography_codes={"Ward 1": 0},
        feature_names=["service_category_code"],
        point_model=None,
        residual_q10_by_hour={},
        residual_q90_by_hour={},
        model_family="lightgbm",
        baseline_method="historical",
    )
    assert available_service._top_grouped_drivers(
        rows=prepared_rows["rows"][:1],
        artifact=no_model_artifact,
        group_resolver=available_service._resolve_daily_feature_group,
    ) == []


def test_weekly_driver_context_covers_all_branch_outcomes(monkeypatch: pytest.MonkeyPatch) -> None:
    week_start = datetime(2026, 4, 1, tzinfo=timezone.utc)
    version = SimpleNamespace(
        source_cleaned_dataset_version_id="dataset-1",
        week_start_local=week_start,
        week_end_local=week_start + timedelta(days=3),
    )
    stored_model = SimpleNamespace(
        source_cleaned_dataset_version_id="dataset-1",
        feature_schema_version=WeeklyDemandPipeline.feature_schema_version,
        artifact_path="weekly-artifact.bin",
    )
    artifact_without_point = TrainedWeeklyDemandArtifact(
        geography_scope="citywide",
        category_codes={"Roads": 0},
        geography_codes={None: 0},
        feature_names=["service_category_code"],
        point_model=None,
        residual_q10_by_weekday={},
        residual_q90_by_weekday={},
        model_family="weekly",
        baseline_method="historical",
    )
    artifact_with_point = TrainedWeeklyDemandArtifact(
        geography_scope="citywide",
        category_codes={"Roads": 0},
        geography_codes={None: 0},
        feature_names=[
            "service_category_code",
            "day_of_week",
            "avg_temperature_c",
            "historical_mean",
            "lag_7d",
            "rolling_mean_7d",
        ],
        point_model=FakePointModel(
            prediction=8.0,
            contrib_rows=[[0.4, 0.2, 1.4, 0.3, -1.8, 0.5, 0.0]],
        ),
        residual_q10_by_weekday={},
        residual_q90_by_weekday={},
        model_family="weekly",
        baseline_method="historical",
    )
    prepared = {
        "training_rows": [],
        "rows": [
            {
                "forecast_date_local": date(2026, 4, 1),
                "service_category": "Roads",
                "geography_key": None,
                "day_of_week": 2,
                "day_of_year": 91,
                "month": 4,
                "is_weekend": False,
                "is_holiday": False,
                "weather_is_missing": False,
                "avg_temperature_c": 1.0,
                "total_precipitation_mm": 0.0,
                "total_snowfall_mm": 0.0,
                "avg_precipitation_probability_pct": 5.0,
                "historical_mean": 4.0,
                "lag_7d": 2.0,
                "rolling_mean_7d": 3.0,
                "rolling_mean_28d": 3.5,
            }
        ],
    }
    monkeypatch.setattr(service_module, "_fetch_forecast_weather", lambda *args, **kwargs: [])
    monkeypatch.setattr(service_module, "prepare_weekly_forecast_features", lambda **kwargs: prepared)

    resolved = _resolved(
        forecast_product="weekly",
        forecast_reference_id="weekly-1",
        window_start=week_start,
        window_end=week_start + timedelta(days=1),
    )

    missing_version_service = _build_service(
        weekly_forecast_repository=SimpleNamespace(get_forecast_version=lambda forecast_version_id: None),
    )
    no_model_service = _build_service(
        weekly_forecast_repository=SimpleNamespace(get_forecast_version=lambda forecast_version_id: version),
    )
    mismatch_lineage_service = _build_service(
        weekly_forecast_repository=SimpleNamespace(get_forecast_version=lambda forecast_version_id: version),
        forecast_model_repository=SimpleNamespace(
            find_current_model=lambda product_name: SimpleNamespace(
                source_cleaned_dataset_version_id="dataset-9",
                feature_schema_version=WeeklyDemandPipeline.feature_schema_version,
                artifact_path="weekly-artifact.bin",
            )
        ),
    )
    mismatch_schema_service = _build_service(
        weekly_forecast_repository=SimpleNamespace(get_forecast_version=lambda forecast_version_id: version),
        forecast_model_repository=SimpleNamespace(
            find_current_model=lambda product_name: SimpleNamespace(
                source_cleaned_dataset_version_id="dataset-1",
                feature_schema_version="legacy-weekly",
                artifact_path="weekly-artifact.bin",
            )
        ),
    )
    missing_point_service = _build_service(
        weekly_forecast_repository=SimpleNamespace(get_forecast_version=lambda forecast_version_id: version),
        forecast_model_repository=SimpleNamespace(find_current_model=lambda product_name: stored_model),
        weekly_forecast_training_service=SimpleNamespace(load_artifact_bundle=lambda artifact_path: artifact_without_point),
    )
    no_rows_service = _build_service(
        weekly_forecast_repository=SimpleNamespace(get_forecast_version=lambda forecast_version_id: version),
        forecast_model_repository=SimpleNamespace(find_current_model=lambda product_name: stored_model),
        weekly_forecast_training_service=SimpleNamespace(load_artifact_bundle=lambda artifact_path: artifact_with_point),
        cleaned_dataset_repository=SimpleNamespace(list_dataset_records=lambda cleaned_dataset_version_id: []),
    )
    available_service = _build_service(
        weekly_forecast_repository=SimpleNamespace(get_forecast_version=lambda forecast_version_id: version),
        forecast_model_repository=SimpleNamespace(find_current_model=lambda product_name: stored_model),
        weekly_forecast_training_service=SimpleNamespace(load_artifact_bundle=lambda artifact_path: artifact_with_point),
        cleaned_dataset_repository=SimpleNamespace(list_dataset_records=lambda cleaned_dataset_version_id: []),
    )

    missing_version = missing_version_service._build_weekly_driver_context(resolved)
    no_model = no_model_service._build_weekly_driver_context(resolved)
    mismatch_lineage = mismatch_lineage_service._build_weekly_driver_context(resolved)
    mismatch_schema = mismatch_schema_service._build_weekly_driver_context(resolved)
    missing_point = missing_point_service._build_weekly_driver_context(resolved)

    prepared["rows"] = []
    no_rows = no_rows_service._build_weekly_driver_context(resolved)

    prepared["rows"] = [
        {
            "forecast_date_local": date(2026, 4, 1),
            "service_category": "Roads",
            "geography_key": None,
            "day_of_week": 2,
            "day_of_year": 91,
            "month": 4,
            "is_weekend": False,
            "is_holiday": False,
            "weather_is_missing": False,
            "avg_temperature_c": 1.0,
            "total_precipitation_mm": 0.0,
            "total_snowfall_mm": 0.0,
            "avg_precipitation_probability_pct": 5.0,
            "historical_mean": 4.0,
            "lag_7d": 2.0,
            "rolling_mean_7d": 3.0,
            "rolling_mean_28d": 3.5,
        }
    ]
    available = available_service._build_weekly_driver_context(resolved)

    assert missing_version.status == "failed"
    assert no_model.status == "unavailable"
    assert mismatch_lineage.status == "unavailable"
    assert mismatch_schema.status == "unavailable"
    assert missing_point.status == "unavailable"
    assert no_rows.status == "unavailable"
    assert available.status == "available"
    assert [driver.label for driver in available.payload.drivers] == [
        "Recent demand",
        "Weather",
        "Rolling demand trend",
        "Service category",
        "Historical average",
    ]


def test_build_driver_context_wrapper_covers_weekly_and_unlinked_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    service = _build_service()
    weekly_outcome = _ComponentOutcome(
        status="available",
        payload=AlertDriversComponentRead(status="available", drivers=[]),
    )
    monkeypatch.setattr(service, "_build_weekly_driver_context", lambda resolved: weekly_outcome)

    wrapped_weekly = service._build_driver_context(
        _resolved(forecast_product="weekly", forecast_reference_id="weekly-1")
    )
    unlinked = service._build_driver_context(_resolved(forecast_product=None, forecast_reference_id=None))

    assert wrapped_weekly is weekly_outcome
    assert unlinked.status == "unavailable"


def test_anomaly_context_load_holidays_and_render_events_cover_remaining_paths() -> None:
    start = datetime(2026, 4, 8, 10, tzinfo=timezone.utc)
    threshold_bundle = SimpleNamespace(
        candidate=SimpleNamespace(
            surge_candidate_id="candidate-1",
            evaluation_window_start=start - timedelta(days=2),
            evaluation_window_end=start - timedelta(days=2) + timedelta(hours=1),
            actual_demand_value=6.0,
            forecast_p50_value=2.0,
            residual_z_score=3.5,
            percent_above_forecast=200.0,
            candidate_status="flagged",
            detected_at=start - timedelta(days=2),
        ),
        confirmation=SimpleNamespace(
            surge_notification_event_id="surge-event-1",
            outcome="confirmed",
        ),
    )
    selected_bundle = SimpleNamespace(
        candidate=SimpleNamespace(
            surge_candidate_id="candidate-selected",
            evaluation_window_start=start,
            evaluation_window_end=start + timedelta(hours=1),
            actual_demand_value=8.0,
            forecast_p50_value=3.0,
            residual_z_score=4.2,
            percent_above_forecast=180.0,
            candidate_status="flagged",
            detected_at=start,
        ),
        confirmation=SimpleNamespace(
            surge_notification_event_id="surge-event-selected",
            outcome="confirmed",
        ),
    )
    holiday_years: list[int] = []
    service = _build_service(
        surge_evaluation_repository=SimpleNamespace(
            list_candidate_bundles_for_window=lambda **kwargs: [threshold_bundle],
            get_candidate_bundle=lambda candidate_id: selected_bundle if candidate_id == "candidate-selected" else None,
        ),
        nager_date_client=SimpleNamespace(
            fetch_holidays=lambda year: holiday_years.append(year) or [{"date": f"{year}-01-01"}],
        ),
        alert_detail_repository=SimpleNamespace(
            require_load=lambda alert_detail_load_id: SimpleNamespace(
                requested_by_subject="owner",
                alert_source="threshold_alert",
                alert_id="alert-1",
                render_status=None,
            ),
            record_render_event=lambda *args, **kwargs: SimpleNamespace(
                alert_source="threshold_alert",
                alert_id="alert-1",
            ),
        ),
    )
    no_anomaly_service = _build_service()
    missing_selected_service = _build_service(
        surge_evaluation_repository=SimpleNamespace(
            list_candidate_bundles_for_window=lambda **kwargs: [],
            get_candidate_bundle=lambda candidate_id: None,
        ),
    )

    threshold_anomalies = service._build_anomaly_context(_resolved(alert_triggered_at=start, alert_source="threshold_alert"))
    surge_anomalies = service._build_anomaly_context(
        _resolved(
            alert_source="surge_alert",
            alert_triggered_at=start,
            surge_candidate_id="candidate-selected",
            surge_evaluation_run_id="surge-run-1",
        )
    )
    unavailable_anomalies = no_anomaly_service._build_anomaly_context(_resolved(alert_triggered_at=start))
    missing_selected = missing_selected_service._build_anomaly_context(
        _resolved(
            alert_source="surge_alert",
            alert_triggered_at=start,
            surge_candidate_id="missing-selected",
        )
    )
    holidays = service._load_holidays(
        datetime(2025, 12, 31, tzinfo=timezone.utc),
        datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    assert threshold_anomalies.status == "available"
    assert threshold_anomalies.payload.items[0].is_selected_alert is False
    assert surge_anomalies.status == "available"
    assert [item.surge_candidate_id for item in surge_anomalies.payload.items] == [
        "candidate-1",
        "candidate-selected",
    ]
    assert surge_anomalies.payload.items[-1].is_selected_alert is True
    assert unavailable_anomalies.status == "unavailable"
    assert missing_selected.status == "unavailable"
    assert holiday_years == [2025, 2026]
    assert holidays == [{"date": "2025-01-01"}, {"date": "2026-01-01"}]

    with pytest.raises(HTTPException) as missing_load:
        _build_service(
            alert_detail_repository=SimpleNamespace(require_load=lambda alert_detail_load_id: (_ for _ in ()).throw(LookupError("missing"))),
        ).record_render_event(
            alert_detail_load_id="missing-load",
            payload=SimpleNamespace(render_status="rendered", failure_reason=None),
            claims={"sub": "owner", "roles": ["CityPlanner"]},
        )
    assert missing_load.value.status_code == 404

    with pytest.raises(HTTPException) as forbidden:
        service.record_render_event(
            alert_detail_load_id="load-1",
            payload=SimpleNamespace(render_status="rendered", failure_reason=None),
            claims={"sub": "intruder", "roles": ["CityPlanner"]},
        )
    assert forbidden.value.status_code == 403

    owner_rendered = service.record_render_event(
        alert_detail_load_id="load-1",
        payload=SimpleNamespace(render_status="rendered", failure_reason=None),
        claims={"sub": "owner", "roles": ["CityPlanner"]},
    )
    manager_failed = service.record_render_event(
        alert_detail_load_id="load-1",
        payload=SimpleNamespace(render_status="render_failed", failure_reason="chart failed"),
        claims={"sub": "manager", "roles": ["OperationalManager"]},
    )

    assert owner_rendered.recorded_outcome_status == "rendered"
    assert manager_failed.recorded_outcome_status == "render_failed"
