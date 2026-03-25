from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.schemas.forecast_visualization import UncertaintyBands, UncertaintyPoint, VisualizationForecastPoint, VisualizationPoint
from app.services.forecast_visualization_service import ForecastVisualizationService
from app.services.forecast_visualization_sources import NormalizedForecastSource


class StubVisualizationRepository:
    def __init__(self):
        self.records = {}
        self.counter = 0

    def create_load_record(self, **kwargs):
        self.counter += 1
        record = type('LoadRecord', (), {'visualization_load_id': f'load-{self.counter}', **kwargs})()
        self.records[record.visualization_load_id] = record
        return record

    def complete_load(self, visualization_load_id, **kwargs):
        record = self.records[visualization_load_id]
        for key, value in kwargs.items():
            setattr(record, key, value)
        return record

    def report_render_event(self, visualization_load_id, **kwargs):
        if visualization_load_id not in self.records:
            raise LookupError('Visualization load not found')
        record = self.records[visualization_load_id]
        for key, value in kwargs.items():
            setattr(record, key, value)
        return record


class StubHistoricalDemandService:
    def __init__(self, history):
        self.history = history

    def build_series(self, **kwargs):
        return self.history, 'dataset-1', kwargs['boundary'] - timedelta(days=7), kwargs['boundary']


class StubSnapshotService:
    def __init__(self, fallback=None):
        self.fallback = fallback
        self.stored = []

    def store_snapshot(self, **kwargs):
        self.stored.append(kwargs)
        return type('Snapshot', (), {'visualization_snapshot_id': 'snapshot-1'})()

    def get_fallback_visualization(self, **kwargs):
        return self.fallback


class StubSourceService:
    def __init__(self, source=None):
        self.source = source

    def normalize_daily(self, **kwargs):
        return self.source

    def normalize_weekly(self, **kwargs):
        return self.source

    def list_daily_categories(self, buckets):
        return ['Roads', 'Waste']

    def list_weekly_categories(self, buckets):
        return ['Roads', 'Waste']


class StubForecastRepository:
    def __init__(self, has_marker=True):
        self.has_marker = has_marker

    def get_current_marker(self, _name):
        if not self.has_marker:
            return None
        return type('Marker', (), {'forecast_version_id': 'forecast-version-1'})()

    def get_forecast_version(self, _version_id):
        return type('Version', (), {'storage_status': 'stored'})()

    def list_buckets(self, _forecast_version_id):
        return []


class StubWeeklyForecastRepository:
    def get_current_marker(self, _name):
        return None

    def get_forecast_version(self, _version_id):
        return None

    def list_buckets(self, _forecast_version_id):
        return []


class StubSettings:
    forecast_product_name = 'daily_1_day_demand'
    weekly_forecast_product_name = 'weekly_7_day_demand'
    source_name = 'edmonton_311'
    visualization_fallback_age_hours = 24


def _build_service(source, history, fallback=None):
    return ForecastVisualizationService(
        cleaned_dataset_repository=None,
        forecast_repository=StubForecastRepository(has_marker=source is not None),
        weekly_forecast_repository=StubWeeklyForecastRepository(),
        visualization_repository=StubVisualizationRepository(),
        historical_demand_service=StubHistoricalDemandService(history),
        source_service=StubSourceService(source),
        snapshot_service=StubSnapshotService(fallback=fallback),
        settings=StubSettings(),
        logger=__import__('logging').getLogger('test.visualization.unit'),
    )


def test_success_response_uses_history_and_uncertainty():
    source = NormalizedForecastSource(
        forecast_product='daily_1_day',
        forecast_granularity='hourly',
        source_forecast_version_id='forecast-version-1',
        source_weekly_forecast_version_id=None,
        source_forecast_run_id='run-1',
        source_weekly_forecast_run_id=None,
        source_cleaned_dataset_version_id='dataset-1',
        forecast_window_start=datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
        forecast_window_end=datetime(2026, 3, 21, 0, tzinfo=timezone.utc),
        forecast_boundary=datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
        last_updated_at=datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
        forecast_series=[VisualizationForecastPoint(timestamp=datetime(2026, 3, 20, 0, tzinfo=timezone.utc), pointForecast=12)],
        uncertainty_bands=UncertaintyBands(labels=['P10', 'P50', 'P90'], points=[UncertaintyPoint(timestamp=datetime(2026, 3, 20, 0, tzinfo=timezone.utc), p10=10, p50=12, p90=14)]),
    )
    history = [VisualizationPoint(timestamp=datetime(2026, 3, 19, 0, tzinfo=timezone.utc), value=3)]
    service = _build_service(source, history)
    response = service.get_current_visualization(forecast_product='daily_1_day', service_categories=['Roads', 'Waste'])
    assert response.view_status == 'success'
    assert len(response.historical_series) == 1
    assert response.uncertainty_bands is not None
    assert response.category_filter.selected_categories == ['Roads', 'Waste']


def test_degraded_response_when_history_missing():
    source = NormalizedForecastSource(
        forecast_product='daily_1_day',
        forecast_granularity='hourly',
        source_forecast_version_id='forecast-version-1',
        source_weekly_forecast_version_id=None,
        source_forecast_run_id='run-1',
        source_weekly_forecast_run_id=None,
        source_cleaned_dataset_version_id='dataset-1',
        forecast_window_start=datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
        forecast_window_end=datetime(2026, 3, 21, 0, tzinfo=timezone.utc),
        forecast_boundary=datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
        last_updated_at=datetime(2026, 3, 20, 0, tzinfo=timezone.utc),
        forecast_series=[VisualizationForecastPoint(timestamp=datetime(2026, 3, 20, 0, tzinfo=timezone.utc), pointForecast=12)],
        uncertainty_bands=UncertaintyBands(labels=['P10', 'P50', 'P90'], points=[UncertaintyPoint(timestamp=datetime(2026, 3, 20, 0, tzinfo=timezone.utc), p10=10, p50=12, p90=14)]),
    )
    service = _build_service(source, [])
    response = service.get_current_visualization(forecast_product='daily_1_day', service_categories=['Roads'])
    assert response.view_status == 'degraded'
    assert response.degradation_type == 'history_missing'


def test_unavailable_without_source_or_fallback():
    service = _build_service(None, [])
    response = service.get_current_visualization(forecast_product='daily_1_day', service_categories=['Roads'])
    assert response.view_status == 'unavailable'


def test_list_service_categories_returns_available_values():
    service = _build_service('present', [])
    response = service.list_service_categories(forecast_product='daily_1_day')
    assert response.categories == ['Roads', 'Waste']



def test_unavailable_when_source_buckets_are_malformed():
    class MalformedSourceService(StubSourceService):
        def normalize_daily(self, **kwargs):
            return None

    service = ForecastVisualizationService(
        cleaned_dataset_repository=None,
        forecast_repository=StubForecastRepository(has_marker=True),
        weekly_forecast_repository=StubWeeklyForecastRepository(),
        visualization_repository=StubVisualizationRepository(),
        historical_demand_service=StubHistoricalDemandService([]),
        source_service=MalformedSourceService(),
        snapshot_service=StubSnapshotService(fallback=None),
        settings=StubSettings(),
        logger=__import__('logging').getLogger('test.visualization.unit'),
    )

    response = service.get_current_visualization(forecast_product='daily_1_day')
    assert response.view_status == 'unavailable'
