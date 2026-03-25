from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import pytest

from app.pipelines.forecasting.weekly_feature_preparation import prepare_weekly_forecast_features
from app.pipelines.forecasting.weekly_demand_pipeline import WeeklyDemandPipeline
from app.services.week_window_service import WeekWindowService
from app.services.weekly_forecast_bucket_service import WeeklyForecastBucketService
from app.services.weekly_forecast_service import WeeklyForecastService


def _fake_geomet_client(weather_rows=None):
    rows = weather_rows or []
    return SimpleNamespace(fetch_forecast_hourly_conditions=lambda start, end: list(rows))


def _fake_nager_client(holidays=None):
    rows = holidays or []
    return SimpleNamespace(fetch_holidays=lambda year: list(rows))


@pytest.mark.unit
def test_week_window_service_returns_monday_start_and_sunday_end() -> None:
    window = WeekWindowService("America/Edmonton").get_week_window(datetime(2026, 3, 25, 18, tzinfo=timezone.utc))

    assert window.week_start_local.weekday() == 0
    assert window.week_start_local.hour == 0
    assert window.week_end_local.weekday() == 6
    assert window.week_end_local.hour == 23


@pytest.mark.unit
def test_weekly_feature_preparation_uses_category_only_when_geography_missing() -> None:
    week_start = datetime(2026, 3, 23, 0, 0, tzinfo=timezone.utc)
    prepared = prepare_weekly_forecast_features(
        dataset_records=[{"category": "Roads", "requested_at": "2026-03-18T10:00:00Z"}],
        week_start_local=week_start,
        week_end_local=week_start + timedelta(days=6, hours=23, minutes=59, seconds=59),
        timezone_name="America/Edmonton",
    )

    assert prepared["geography_scope"] == "category_only"
    assert prepared["scopes"] == [("Roads", None)]


@pytest.mark.unit
def test_weekly_pipeline_outputs_ordered_quantiles_and_seven_days() -> None:
    week_start = datetime(2026, 3, 23, 0, 0, tzinfo=timezone.utc)
    prepared = prepare_weekly_forecast_features(
        dataset_records=[
            {"category": "Roads", "requested_at": "2026-03-16T10:00:00Z", "ward": "Ward 1"},
            {"category": "Roads", "requested_at": "2026-03-17T11:00:00Z", "ward": "Ward 1"},
        ],
        week_start_local=week_start,
        week_end_local=week_start + timedelta(days=6, hours=23, minutes=59, seconds=59),
        timezone_name="America/Edmonton",
    )

    generated = WeeklyDemandPipeline().run(prepared)
    buckets, geography_scope = WeeklyForecastBucketService().build_buckets(generated)

    assert geography_scope == "category_and_geography"
    assert len(buckets) == 7
    assert all(bucket["quantile_p10"] <= bucket["quantile_p50"] <= bucket["quantile_p90"] for bucket in buckets)


@pytest.mark.unit
def test_weekly_pipeline_uses_weather_and_holiday_context() -> None:
    week_start = datetime(2026, 3, 23, 0, 0, tzinfo=timezone.utc)
    prepared = prepare_weekly_forecast_features(
        dataset_records=[
            {"category": "Roads", "requested_at": "2026-03-16T10:00:00Z"},
            {"category": "Roads", "requested_at": "2026-03-17T10:00:00Z"},
        ],
        week_start_local=week_start,
        week_end_local=week_start + timedelta(days=6, hours=23, minutes=59, seconds=59),
        timezone_name="America/Edmonton",
        weather_rows=[
            {"timestamp": datetime(2026, 3, 23, 12, tzinfo=timezone.utc), "temperature_c": 10.0, "precipitation_mm": 4.0},
        ],
        holidays=[{"date": "2026-03-23", "name": "Holiday"}],
    )

    bucket = WeeklyDemandPipeline().run(prepared)["buckets"][0]
    assert prepared["target_context"][week_start.date()]["is_holiday"] is True
    assert prepared["target_context"][week_start.date()]["has_weather"] is True
    assert bucket["point_forecast"] != bucket["baseline_value"]


@pytest.mark.unit
def test_weekly_pipeline_leaves_uncovered_days_without_weather_adjustment() -> None:
    week_start = datetime(2026, 3, 23, 0, 0, tzinfo=timezone.utc)
    prepared = prepare_weekly_forecast_features(
        dataset_records=[
            {"category": "Roads", "requested_at": "2026-03-16T10:00:00Z"},
            {"category": "Roads", "requested_at": "2026-03-17T10:00:00Z"},
        ],
        week_start_local=week_start,
        week_end_local=week_start + timedelta(days=6, hours=23, minutes=59, seconds=59),
        timezone_name="America/Edmonton",
        weather_rows=[
            {"timestamp": datetime(2026, 3, 23, 12, tzinfo=timezone.utc), "temperature_c": 10.0, "precipitation_mm": 4.0},
        ],
    )

    monday_context = prepared["target_context"][week_start.date()]
    tuesday_context = prepared["target_context"][(week_start + timedelta(days=1)).date()]
    buckets = WeeklyDemandPipeline().run(prepared)["buckets"]

    assert monday_context["has_weather"] is True
    assert tuesday_context["has_weather"] is False
    assert tuesday_context["avg_temperature_c"] is None
    assert tuesday_context["total_precipitation_mm"] is None
    assert buckets[1]["point_forecast"] == buckets[1]["baseline_value"]


@pytest.mark.unit
def test_start_run_deduplicates_same_week_in_progress() -> None:
    class FakeRunRepository:
        def __init__(self):
            self.created = None

        def find_in_progress_run(self, **kwargs):
            return self.created

        def create_run(self, **kwargs):
            self.created = SimpleNamespace(weekly_forecast_run_id="run-1", status="running", **kwargs)
            return self.created

    repository = FakeRunRepository()
    service = WeeklyForecastService(
        cleaned_dataset_repository=SimpleNamespace(get_current_approved_dataset=lambda _source_name: None),
        weekly_forecast_run_repository=repository,
        weekly_forecast_repository=SimpleNamespace(),
        settings=SimpleNamespace(source_name="edmonton_311", weekly_forecast_timezone="America/Edmonton"),
        geomet_client=_fake_geomet_client(),
        nager_date_client=_fake_nager_client(),
    )
    now = datetime(2026, 3, 25, 18, tzinfo=timezone.utc)

    first_run, first_created = service.start_run("on_demand", now=now)
    second_run, second_created = service.start_run("on_demand", now=now)

    assert first_created is True
    assert second_created is False
    assert second_run.weekly_forecast_run_id == first_run.weekly_forecast_run_id
