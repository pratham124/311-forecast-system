from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from app.services.public_forecast_source_service import (
    PublicForecastSourceService,
    _as_utc,
    _format_day_window,
    _format_week_window,
)


@dataclass
class DummySettings:
    forecast_product_name: str = "daily_1_day_demand"
    weekly_forecast_product_name: str = "weekly_7_day_demand"


class FakeForecastRepository:
    def __init__(self, *, marker=None, version=None, buckets=None) -> None:
        self._marker = marker
        self._version = version
        self._buckets = buckets or []

    def get_current_marker(self, forecast_product_name: str):
        return self._marker

    def get_forecast_version(self, forecast_version_id: str):
        return self._version

    def list_buckets(self, forecast_version_id: str):
        return list(self._buckets)


class FakeWeeklyForecastRepository:
    def __init__(self, *, marker=None, version=None, buckets=None) -> None:
        self._marker = marker
        self._version = version
        self._buckets = buckets or []

    def get_current_marker(self, forecast_product_name: str):
        return self._marker

    def get_forecast_version(self, weekly_forecast_version_id: str):
        return self._version

    def list_buckets(self, weekly_forecast_version_id: str):
        return list(self._buckets)


def test_as_utc_handles_none_and_naive_values():
    none_value = _as_utc(None)
    naive_value = _as_utc(datetime(2026, 3, 20, 12, 0, 0))
    aware_value = _as_utc(datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone(timedelta(hours=-6))))

    assert none_value.tzinfo == timezone.utc
    assert naive_value.tzinfo == timezone.utc
    assert naive_value.hour == 12
    assert aware_value.tzinfo == timezone.utc
    assert aware_value.hour == 18


def test_format_window_helpers():
    start = datetime(2026, 3, 20, tzinfo=timezone.utc)
    end = datetime(2026, 3, 21, tzinfo=timezone.utc)

    assert _format_day_window(start, end) == "2026-03-20 to 2026-03-21"
    assert _format_week_window(start, end) == "2026-03-20 to 2026-03-21"


def test_resolve_daily_returns_none_for_missing_marker_version_and_buckets():
    service_missing_marker = PublicForecastSourceService(
        forecast_repository=FakeForecastRepository(marker=None),
        weekly_forecast_repository=FakeWeeklyForecastRepository(),
        settings=DummySettings(),
    )
    assert service_missing_marker.resolve_current_source("daily") is None

    marker = type("Marker", (), {"forecast_version_id": "forecast-1"})()
    service_missing_version = PublicForecastSourceService(
        forecast_repository=FakeForecastRepository(marker=marker, version=None),
        weekly_forecast_repository=FakeWeeklyForecastRepository(),
        settings=DummySettings(),
    )
    assert service_missing_version.resolve_current_source("daily") is None

    bad_version = type("Version", (), {"storage_status": "pending"})()
    service_pending_version = PublicForecastSourceService(
        forecast_repository=FakeForecastRepository(marker=marker, version=bad_version),
        weekly_forecast_repository=FakeWeeklyForecastRepository(),
        settings=DummySettings(),
    )
    assert service_pending_version.resolve_current_source("daily") is None

    stored_version = type(
        "Version",
        (),
        {
            "forecast_version_id": "forecast-1",
            "storage_status": "stored",
            "horizon_start": datetime(2026, 3, 20, tzinfo=timezone.utc),
            "horizon_end": datetime(2026, 3, 21, tzinfo=timezone.utc),
            "activated_at": None,
            "stored_at": datetime(2026, 3, 20, tzinfo=timezone.utc),
            "source_cleaned_dataset_version_id": "dataset-1",
        },
    )()
    service_no_buckets = PublicForecastSourceService(
        forecast_repository=FakeForecastRepository(marker=marker, version=stored_version, buckets=[]),
        weekly_forecast_repository=FakeWeeklyForecastRepository(),
        settings=DummySettings(),
    )
    assert service_no_buckets.resolve_current_source("daily") is None


def test_resolve_weekly_returns_none_for_missing_marker_version_and_buckets():
    service_missing_marker = PublicForecastSourceService(
        forecast_repository=FakeForecastRepository(),
        weekly_forecast_repository=FakeWeeklyForecastRepository(marker=None),
        settings=DummySettings(),
    )
    assert service_missing_marker.resolve_current_source("weekly") is None

    marker = type("Marker", (), {"weekly_forecast_version_id": "weekly-1"})()
    service_missing_version = PublicForecastSourceService(
        forecast_repository=FakeForecastRepository(),
        weekly_forecast_repository=FakeWeeklyForecastRepository(marker=marker, version=None),
        settings=DummySettings(),
    )
    assert service_missing_version.resolve_current_source("weekly") is None

    bad_version = type("Version", (), {"storage_status": "pending"})()
    service_pending_version = PublicForecastSourceService(
        forecast_repository=FakeForecastRepository(),
        weekly_forecast_repository=FakeWeeklyForecastRepository(marker=marker, version=bad_version),
        settings=DummySettings(),
    )
    assert service_pending_version.resolve_current_source("weekly") is None

    stored_version = type(
        "Version",
        (),
        {
            "weekly_forecast_version_id": "weekly-1",
            "storage_status": "stored",
            "week_start_local": datetime(2026, 3, 23, tzinfo=timezone.utc),
            "week_end_local": datetime(2026, 3, 30, tzinfo=timezone.utc),
            "activated_at": None,
            "stored_at": datetime(2026, 3, 23, tzinfo=timezone.utc),
            "source_cleaned_dataset_version_id": "dataset-1",
        },
    )()
    service_no_buckets = PublicForecastSourceService(
        forecast_repository=FakeForecastRepository(),
        weekly_forecast_repository=FakeWeeklyForecastRepository(marker=marker, version=stored_version, buckets=[]),
        settings=DummySettings(),
    )
    assert service_no_buckets.resolve_current_source("weekly") is None
