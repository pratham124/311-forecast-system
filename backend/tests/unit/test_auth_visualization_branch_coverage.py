from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, Response

from app.api.routes import auth as auth_routes
from app.api.routes import forecast_visualizations as visualization_routes
from app.core import auth as auth_core
from app.repositories.auth_repository import AuthRepository
from app.repositories.visualization_repository import VisualizationRepository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.forecast_visualization import CategoryFilter, ForecastVisualizationRead, UncertaintyBands, UncertaintyPoint, VisualizationForecastPoint, VisualizationPoint, VisualizationRenderEvent
from app.services.auth_service import (
    AuthBootstrapService,
    AuthService,
    AuthenticationError,
    RegistrationError,
     _verify_password,
    _hash_refresh_token,
)
from app.services.forecast_visualization_service import ForecastVisualizationService
from app.services.forecast_visualization_sources import ForecastVisualizationSourceService, NormalizedForecastSource, _aggregate_daily, _aggregate_weekly, _as_utc, _coerce_float, _coerce_timestamp
from app.services.historical_demand_service import HistoricalDemandService
from app.services import visualization_snapshot_service
from app.services.visualization_snapshot_service import VisualizationSnapshotService
from tests.conftest import build_token


class Creds:
    def __init__(self, token: str) -> None:
        self.credentials = token


class _HistoryRepo:
    def __init__(self, records, current_dataset=None):
        self.records = records
        self.current_dataset = current_dataset

    def list_current_cleaned_records(self, _source_name, start_time=None, end_time=None):
        return self.records

    def get_current_approved_dataset(self, _source_name):
        return self.current_dataset


class _StubSourceService:
    def __init__(self, *, daily=None, weekly=None):
        self.daily = daily
        self.weekly = weekly

    def normalize_daily(self, **kwargs):
        return self.daily

    def normalize_weekly(self, **kwargs):
        return self.weekly


class _StubVisualizationRepository:
    def __init__(self):
        self.created = []
        self.completed = []
        self.events = []

    def create_load_record(self, **kwargs):
        record = SimpleNamespace(visualization_load_id=f"load-{len(self.created) + 1}", **kwargs)
        self.created.append(record)
        return record

    def complete_load(self, visualization_load_id, **kwargs):
        self.completed.append((visualization_load_id, kwargs))

    def report_render_event(self, visualization_load_id, **kwargs):
        self.events.append((visualization_load_id, kwargs))


class _StubSnapshotService:
    def __init__(self):
        self.stored = []

    def store_snapshot(self, **kwargs):
        self.stored.append(kwargs)

    def get_fallback_visualization(self, **kwargs):
        return None


class _StubDailyForecastRepository:
    def __init__(self, marker=None, version=None):
        self.marker = marker
        self.version = version

    def get_current_marker(self, _name):
        return self.marker

    def get_forecast_version(self, _version_id):
        return self.version

    def list_buckets(self, _version_id):
        return []


class _StubWeeklyForecastRepository:
    def __init__(self, marker=None, version=None):
        self.marker = marker
        self.version = version

    def get_current_marker(self, _name):
        return self.marker

    def get_forecast_version(self, _version_id):
        return self.version

    def list_buckets(self, _version_id):
        return []


class _StubHistoryService:
    def __init__(self, history):
        self.history = history

    def build_series(self, **kwargs):
        return self.history


def _visualization_service(*, daily_repo=None, weekly_repo=None, source_service=None, history=None):
    return ForecastVisualizationService(
        cleaned_dataset_repository=None,
        forecast_repository=daily_repo or _StubDailyForecastRepository(),
        weekly_forecast_repository=weekly_repo or _StubWeeklyForecastRepository(),
        visualization_repository=_StubVisualizationRepository(),
        historical_demand_service=_StubHistoryService(history or ([], None, datetime(2026, 3, 1, tzinfo=timezone.utc), datetime(2026, 3, 8, tzinfo=timezone.utc))),
        source_service=source_service or _StubSourceService(),
        snapshot_service=_StubSnapshotService(),
        settings=SimpleNamespace(forecast_product_name='daily_1_day_demand', weekly_forecast_product_name='weekly_7_day_demand'),
        logger=__import__('logging').getLogger('test.branch.visualization'),
    )


@pytest.mark.unit
def test_auth_core_rejects_non_dict_payload_and_non_access_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth_core, 'get_settings', lambda: SimpleNamespace(jwt_secret='test-secret-key-311-forecast-system-32b', jwt_audience='311-forecast-system', jwt_issuer='311-forecast-system', jwt_access_token_expires_minutes=60))
    with monkeypatch.context() as ctx:
        ctx.setattr(auth_core.jwt, 'decode', lambda *args, **kwargs: 'bad-payload')

        with pytest.raises(HTTPException) as invalid_payload:
            auth_core._decode_jwt_payload('token')
        assert invalid_payload.value.status_code == 401

    non_access = build_token(['CityPlanner'])
    claims = auth_core._decode_jwt_payload(non_access)
    claims['token_type'] = 'refresh'
    monkeypatch.setattr(auth_core, '_decode_jwt_payload', lambda token: claims)

    with pytest.raises(HTTPException) as invalid_type:
        auth_core.get_current_claims(Creds('token'))
    assert invalid_type.value.status_code == 401


@pytest.mark.unit
def test_auth_routes_cover_logout_and_me_error_paths(session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth_routes, 'get_settings', lambda: SimpleNamespace(auth_refresh_cookie_name='forecast_refresh_token', auth_cookie_secure=False, auth_cookie_samesite='lax', jwt_refresh_token_expires_days=14))

    logout_response = auth_routes.logout(Response(), refresh_token=None, session=session)
    assert logout_response.status_code == 202

    with pytest.raises(HTTPException) as invalid_subject:
        auth_routes.get_me(claims={'sub': None}, session=session)
    assert invalid_subject.value.status_code == 401

    with pytest.raises(HTTPException) as missing_user:
        auth_routes.get_me(claims={'sub': 'missing-user'}, session=session)
    assert missing_user.value.status_code == 401


@pytest.mark.unit
def test_auth_routes_cover_register_conflict_and_refresh_invalid_token(session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth_routes, 'get_settings', lambda: SimpleNamespace(auth_refresh_cookie_name='forecast_refresh_token', auth_cookie_secure=False, auth_cookie_samesite='lax', jwt_refresh_token_expires_days=14))
    repository = AuthRepository(session)
    repository.upsert_allowlist_entry('planner@example.com', ['CityPlanner'])
    session.commit()
    AuthService(repository).register('planner@example.com', 'super-secret-password')

    with pytest.raises(HTTPException) as conflict:
        auth_routes.register(RegisterRequest(email='planner@example.com', password='super-secret-password'), Response(), session)
    assert conflict.value.status_code == 409

    with pytest.raises(HTTPException) as invalid_refresh:
        auth_routes.refresh(Response(), refresh_token='missing-refresh-token', session=session)
    assert invalid_refresh.value.status_code == 401


@pytest.mark.unit
def test_auth_service_and_repository_cover_remaining_paths(session) -> None:
    repository = AuthRepository(session)
    repository.upsert_allowlist_entry('planner@example.com', ['CityPlanner'])
    session.commit()
    service = AuthService(repository)
    service.register('planner@example.com', 'super-secret-password')

    with pytest.raises(RegistrationError):
        service.register('planner@example.com', 'super-secret-password')
    with pytest.raises(AuthenticationError):
        service.refresh('missing-refresh-token')
    service.logout('missing-refresh-token')
    with pytest.raises(AuthenticationError):
        service.get_user('missing-user')
    with pytest.raises(RegistrationError):
        service.register('new@example.com', 'short')

    entry = repository.upsert_allowlist_entry('planner@example.com', ['OperationalManager'], enabled=False)
    assert json.loads(entry.roles_json) == ['OperationalManager']
    assert entry.is_enabled is False

    bootstrap = AuthBootstrapService(repository)
    bootstrap.sync_allowlist([])

    assert _verify_password('super-secret-password', 'argon$1$bad$hash') is False
    assert _verify_password('super-secret-password', 'not-even-a-hash') is False


@pytest.mark.unit
def test_auth_service_rejects_expired_refresh_token(session) -> None:
    repository = AuthRepository(session)
    repository.upsert_allowlist_entry('manager@example.com', ['OperationalManager'])
    session.commit()
    service = AuthService(repository)
    registered = service.register('manager@example.com', 'super-secret-password')
    refresh_session = repository.get_refresh_session_by_hash(_hash_refresh_token(registered.refresh_token))
    assert refresh_session is not None
    refresh_session.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    session.commit()

    with pytest.raises(AuthenticationError):
        service.refresh(registered.refresh_token)


@pytest.mark.unit
def test_visualization_route_record_render_event_covers_success_and_not_found(session, monkeypatch: pytest.MonkeyPatch) -> None:
    class StubService:
        def __init__(self):
            self.calls = []

        def record_render_event(self, visualization_load_id, payload):
            self.calls.append((visualization_load_id, payload.render_status))

    stub = StubService()
    monkeypatch.setattr(visualization_routes, 'build_visualization_service', lambda session: stub)
    payload = VisualizationRenderEvent(renderStatus='rendered')
    response = visualization_routes.record_visualization_render_event('load-1', payload, session, {})
    assert response.status_code == 202
    assert stub.calls == [('load-1', 'rendered')]

    class MissingService:
        def record_render_event(self, visualization_load_id, payload):
            raise LookupError('missing')

    monkeypatch.setattr(visualization_routes, 'build_visualization_service', lambda session: MissingService())
    with pytest.raises(HTTPException) as missing:
        visualization_routes.record_visualization_render_event('missing', VisualizationRenderEvent(renderStatus='render_failed', failureReason='boom'), session, {})
    assert missing.value.status_code == 404


@pytest.mark.unit
def test_visualization_schema_requires_failure_reason_for_failed_render() -> None:
    with pytest.raises(ValueError):
        VisualizationRenderEvent.validate_failure_reason(None, SimpleNamespace(data={'render_status': 'render_failed'}))
    assert VisualizationRenderEvent.validate_failure_reason(None, SimpleNamespace(data={'render_status': 'rendered'})) is None


@pytest.mark.unit
def test_visualization_repository_covers_remaining_paths(session) -> None:
    repository = VisualizationRepository(session)
    now = datetime(2026, 3, 24, tzinfo=timezone.utc)
    record = repository.create_load_record(
        requested_by_actor='planner',
        forecast_product_name='daily_1_day',
        forecast_granularity='hourly',
        service_category_filter='Roads',
        history_window_start=now - timedelta(days=7),
        history_window_end=now,
        forecast_window_start=now,
        forecast_window_end=now + timedelta(hours=1),
    )
    repository.complete_load(
        record.visualization_load_id,
        status='success',
        source_weekly_forecast_version_id='weekly-version-1',
    )
    repository.report_render_event(record.visualization_load_id, render_status='rendered', failure_reason=None)
    repository.report_render_event(record.visualization_load_id, render_status='render_failed', failure_reason='chart failed')
    stored = repository.require_load_record(record.visualization_load_id)
    assert stored.status == 'render_failed'
    assert stored.failure_reason == 'chart failed'
    assert stored.render_reported_at is not None

    with pytest.raises(LookupError):
        repository.require_load_record('missing-load')

    category_mismatch = repository.create_snapshot(
        forecast_product_name='daily_1_day',
        forecast_granularity='hourly',
        service_category_filter='Transit',
        source_cleaned_dataset_version_id='dataset-1',
        source_forecast_version_id='forecast-1',
        source_weekly_forecast_version_id=None,
        source_forecast_run_id='run-1',
        source_weekly_forecast_run_id=None,
        history_window_start=now - timedelta(days=7),
        history_window_end=now,
        forecast_window_start=now,
        forecast_window_end=now + timedelta(hours=1),
        payload={'ok': True},
        created_from_load_id=record.visualization_load_id,
        expires_in_hours=1,
    )
    expired = repository.create_snapshot(
        forecast_product_name='daily_1_day',
        forecast_granularity='hourly',
        service_category_filter='Roads',
        source_cleaned_dataset_version_id='dataset-1',
        source_forecast_version_id='forecast-1',
        source_weekly_forecast_version_id=None,
        source_forecast_run_id='run-1',
        source_weekly_forecast_run_id=None,
        history_window_start=now - timedelta(days=7),
        history_window_end=now,
        forecast_window_start=now,
        forecast_window_end=now + timedelta(hours=1),
        payload={'ok': True},
        created_from_load_id=record.visualization_load_id,
        expires_in_hours=1,
    )
    category_mismatch.created_at = now - timedelta(minutes=30)
    expired.created_at = now - timedelta(minutes=20)
    expired.expires_at = (now - timedelta(minutes=1)).replace(tzinfo=None)
    session.commit()

    assert repository.get_latest_eligible_snapshot(forecast_product_name='daily_1_day', service_category_filter='Roads', now=now.replace(tzinfo=None)) is None
    assert expired.snapshot_status == 'expired'


@pytest.mark.unit
def test_visualization_source_service_covers_daily_weekly_and_uncertainty_branches() -> None:
    service = ForecastVisualizationSourceService()
    assert service.normalize_daily(
        marker=SimpleNamespace(source_cleaned_dataset_version_id='dataset-1', updated_at=datetime(2026, 3, 24, tzinfo=timezone.utc)),
        version=SimpleNamespace(forecast_version_id='forecast-1', forecast_run_id='run-1', horizon_start=datetime(2026, 3, 24, tzinfo=timezone.utc), horizon_end=datetime(2026, 3, 25, tzinfo=timezone.utc)),
        buckets=[SimpleNamespace(service_category='Roads', bucket_start=datetime(2026, 3, 24, tzinfo=timezone.utc), point_forecast=3.0, quantile_p10=1.0, quantile_p50=3.0, quantile_p90=5.0)],
        service_category='Transit',
    ) is None

    weekly = service.normalize_weekly(
        marker=SimpleNamespace(source_cleaned_dataset_version_id='dataset-2', updated_at=datetime(2026, 3, 24)),
        version=SimpleNamespace(weekly_forecast_version_id='weekly-1', weekly_forecast_run_id='weekly-run-1', week_start_local=datetime(2026, 3, 24), week_end_local=datetime(2026, 3, 31)),
        buckets=[SimpleNamespace(service_category='Roads', forecast_date_local=date(2026, 3, 24), point_forecast=7.0, quantile_p10=5.0, quantile_p50=7.0, quantile_p90=9.0)],
        service_category='Roads',
    )
    assert weekly is not None
    assert weekly.forecast_granularity == 'daily'
    assert weekly.forecast_series[0].point_forecast == 7.0

    assert service._build_uncertainty_daily([
        SimpleNamespace(bucket_start=datetime(2026, 3, 24, tzinfo=timezone.utc), quantile_p10=None, quantile_p50=2.0, quantile_p90=3.0)
    ]) is None
    assert service._build_uncertainty_weekly([
        SimpleNamespace(forecast_date_local=date(2026, 3, 24), quantile_p10=1.0, quantile_p50=None, quantile_p90=3.0)
    ]) is None
    assert _as_utc(datetime(2026, 3, 24)).tzinfo == timezone.utc


@pytest.mark.unit
def test_historical_demand_service_covers_filtering_daily_grouping_and_parse_failures() -> None:
    repo = _HistoryRepo(
        records=[
            {'requested_at': '2026-03-20T05:15:00Z', 'category': 'Roads'},
            {'requested_at': '2026-03-20T08:20:00Z', 'category': 'Roads'},
            {'requested_at': '2026-03-20T08:20:00Z', 'category': 'Transit'},
            {'requested_at': 'bad-value', 'category': 'Roads'},
            {'requested_at': '', 'category': 'Roads'},
        ],
        current_dataset=None,
    )
    service = HistoricalDemandService(repo, 'edmonton_311')
    series, dataset_version_id, start, end = service.build_series(
        boundary=datetime(2026, 3, 24),
        granularity='daily',
        service_category='Roads',
    )
    assert dataset_version_id is None
    assert start.tzinfo == timezone.utc
    assert end.tzinfo == timezone.utc
    assert len(series) == 1
    assert series[0].value == 2.0
    assert HistoricalDemandService._parse_timestamp('') is None
    assert HistoricalDemandService._parse_timestamp('not-a-date') is None


@pytest.mark.unit
def test_forecast_visualization_service_covers_weekly_and_uncertainty_missing_branches() -> None:
    weekly_source = SimpleNamespace(
        forecast_product='weekly_7_day',
        forecast_granularity='daily',
        source_forecast_version_id=None,
        source_weekly_forecast_version_id='weekly-version-1',
        source_forecast_run_id=None,
        source_weekly_forecast_run_id='weekly-run-1',
        source_cleaned_dataset_version_id='dataset-1',
        forecast_window_start=datetime(2026, 3, 24, tzinfo=timezone.utc),
        forecast_window_end=datetime(2026, 3, 31, tzinfo=timezone.utc),
        forecast_boundary=datetime(2026, 3, 24, tzinfo=timezone.utc),
        last_updated_at=datetime(2026, 3, 24, tzinfo=timezone.utc),
        forecast_series=[],
        uncertainty_bands=None,
    )
    service = _visualization_service(
        weekly_repo=_StubWeeklyForecastRepository(
            marker=SimpleNamespace(weekly_forecast_version_id='weekly-version-1'),
            version=SimpleNamespace(storage_status='stored', weekly_forecast_version_id='weekly-version-1'),
        ),
        source_service=_StubSourceService(weekly=weekly_source),
        history=([{'timestamp': datetime(2026, 3, 23, tzinfo=timezone.utc), 'value': 1.0}], None, datetime(2026, 3, 17, tzinfo=timezone.utc), datetime(2026, 3, 24, tzinfo=timezone.utc)),
    )
    loaded = service._load_source(forecast_product='weekly_7_day', service_category='Roads')
    assert loaded is weekly_source

    degraded = service.get_current_visualization(forecast_product='weekly_7_day', service_category='Roads')
    assert degraded.degradation_type == 'uncertainty_missing'
    assert degraded.alerts[0].code == 'uncertainty_missing'
    assert degraded.summary == 'Visualization is available without uncertainty bands.'

    missing_daily = _visualization_service(
        daily_repo=_StubDailyForecastRepository(
            marker=SimpleNamespace(forecast_version_id='forecast-1'),
            version=SimpleNamespace(storage_status='pending'),
        ),
    )
    assert missing_daily._load_source(forecast_product='daily_1_day', service_category=None) is None
    missing_weekly = _visualization_service(weekly_repo=_StubWeeklyForecastRepository(marker=SimpleNamespace(weekly_forecast_version_id='weekly-1'), version=None))
    assert missing_weekly._load_source(forecast_product='weekly_7_day', service_category=None) is None

    payload = VisualizationRenderEvent(renderStatus='render_failed', failureReason='boom')
    service.record_render_event('load-9', payload)
    assert service.visualization_repository.events == [('load-9', {'render_status': 'render_failed', 'failure_reason': 'boom'})]


@pytest.mark.unit
def test_logging_and_main_cover_remaining_small_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.logging import summarize_visualization_event
    from app import main as main_module

    summary = summarize_visualization_event('rendered', token='secret-token')
    assert summary['message'] == 'rendered'
    assert summary['token'] != 'secret-token'

    assert main_module._parse_allowlist('missing-colon,, :CityPlanner,valid@example.com: ') == []


@pytest.mark.unit
def test_auth_service_logout_noops_for_already_revoked_session(session) -> None:
    repository = AuthRepository(session)
    repository.upsert_allowlist_entry('manager2@example.com', ['OperationalManager'])
    session.commit()
    service = AuthService(repository)
    registered = service.register('manager2@example.com', 'super-secret-password')
    refresh_session = repository.get_refresh_session_by_hash(_hash_refresh_token(registered.refresh_token))
    assert refresh_session is not None
    refresh_session.revoked_at = datetime.now(timezone.utc)
    session.commit()

    service.logout(registered.refresh_token)

    assert refresh_session.revoked_at is not None


@pytest.mark.unit
def test_visualization_repository_render_failed_preserves_existing_completed_at_and_tz_aware_snapshot(session) -> None:
    repository = VisualizationRepository(session)
    now = datetime(2026, 3, 24, tzinfo=timezone.utc)

    failed_record = repository.create_load_record(
        requested_by_actor='planner',
        forecast_product_name='daily_1_day',
        forecast_granularity='hourly',
        service_category_filter='Roads',
        history_window_start=now - timedelta(days=7),
        history_window_end=now,
        forecast_window_start=now,
        forecast_window_end=now + timedelta(hours=1),
    )
    repository.report_render_event(failed_record.visualization_load_id, render_status='render_failed', failure_reason='created')
    assert repository.require_load_record(failed_record.visualization_load_id).completed_at is not None

    record = repository.create_load_record(
        requested_by_actor='planner',
        forecast_product_name='daily_1_day',
        forecast_granularity='hourly',
        service_category_filter='Roads',
        history_window_start=now - timedelta(days=7),
        history_window_end=now,
        forecast_window_start=now,
        forecast_window_end=now + timedelta(hours=1),
    )
    original_completed_at = datetime(2026, 3, 24, 12, tzinfo=timezone.utc)
    record.completed_at = original_completed_at
    session.commit()

    repository.report_render_event(record.visualization_load_id, render_status='render_failed', failure_reason='kept')
    assert repository.require_load_record(record.visualization_load_id).completed_at == original_completed_at.replace(tzinfo=None)

    mismatch = repository.create_snapshot(
        forecast_product_name='daily_1_day',
        forecast_granularity='hourly',
        service_category_filter='Transit',
        source_cleaned_dataset_version_id='dataset-1',
        source_forecast_version_id='forecast-1',
        source_weekly_forecast_version_id=None,
        source_forecast_run_id='run-1',
        source_weekly_forecast_run_id=None,
        history_window_start=now - timedelta(days=7),
        history_window_end=now,
        forecast_window_start=now,
        forecast_window_end=now + timedelta(hours=1),
        payload={'ok': True},
        created_from_load_id=record.visualization_load_id,
        expires_in_hours=1,
    )
    mismatch.created_at = now + timedelta(minutes=10)

    eligible = repository.create_snapshot(
        forecast_product_name='daily_1_day',
        forecast_granularity='hourly',
        service_category_filter='Roads',
        source_cleaned_dataset_version_id='dataset-1',
        source_forecast_version_id='forecast-1',
        source_weekly_forecast_version_id=None,
        source_forecast_run_id='run-1',
        source_weekly_forecast_run_id=None,
        history_window_start=now - timedelta(days=7),
        history_window_end=now,
        forecast_window_start=now,
        forecast_window_end=now + timedelta(hours=1),
        payload={'ok': True},
        created_from_load_id=record.visualization_load_id,
        expires_in_hours=1,
    )
    eligible.created_at = now
    eligible.expires_at = now + timedelta(minutes=30)
    session.commit()

    assert repository.get_latest_eligible_snapshot(
        forecast_product_name='daily_1_day',
        service_category_filter='Roads',
        now=now,
    ) == eligible


@pytest.mark.unit
def test_visualization_source_service_and_service_cover_final_weekly_none_branches() -> None:
    source_service = ForecastVisualizationSourceService()
    assert source_service.normalize_weekly(
        marker=SimpleNamespace(source_cleaned_dataset_version_id='dataset-2', updated_at=datetime(2026, 3, 24)),
        version=SimpleNamespace(weekly_forecast_version_id='weekly-1', weekly_forecast_run_id='weekly-run-1', week_start_local=datetime(2026, 3, 24), week_end_local=datetime(2026, 3, 31)),
        buckets=[SimpleNamespace(service_category='Roads', forecast_date_local=date(2026, 3, 24), point_forecast=7.0, quantile_p10=5.0, quantile_p50=7.0, quantile_p90=9.0)],
        service_category='Transit',
    ) is None

    service = _visualization_service(weekly_repo=_StubWeeklyForecastRepository(marker=None, version=None))
    assert service._load_source(forecast_product='weekly_7_day', service_category='Roads') is None


@pytest.mark.unit
def test_visualization_repository_get_latest_eligible_snapshot_accepts_tz_aware_expiry_without_normalization() -> None:
    aware_snapshot = SimpleNamespace(
        service_category_filter='Roads',
        expires_at=datetime(2026, 3, 24, 13, tzinfo=timezone.utc),
        created_at=datetime(2026, 3, 24, 12, tzinfo=timezone.utc),
        snapshot_status='stored',
    )

    class FakeSession:
        def scalars(self, statement):
            return [aware_snapshot]

        def flush(self):
            return None

    repository = VisualizationRepository(FakeSession())

    resolved = repository.get_latest_eligible_snapshot(
        forecast_product_name='daily_1_day',
        service_category_filter='Roads',
        now=datetime(2026, 3, 24, 12, tzinfo=timezone.utc),
    )

    assert resolved is aware_snapshot
    assert aware_snapshot.snapshot_status == 'stored'


@pytest.mark.unit
def test_visualization_route_rejects_invalid_service_category_product(session) -> None:
    with pytest.raises(HTTPException) as invalid:
        visualization_routes.list_visualization_service_categories('monthly', session, {})
    assert invalid.value.status_code == 422


@pytest.mark.unit
def test_visualization_repository_complete_load_updates_optional_fields(session) -> None:
    repository = VisualizationRepository(session)
    now = datetime(2026, 3, 24, tzinfo=timezone.utc)
    record = repository.create_load_record(
        requested_by_actor='planner',
        forecast_product_name='daily_1_day',
        forecast_granularity='hourly',
        service_category_filter='Roads,Waste',
        history_window_start=now - timedelta(days=7),
        history_window_end=now,
        forecast_window_start=None,
        forecast_window_end=None,
    )

    completed = repository.complete_load(
        record.visualization_load_id,
        status='success',
        forecast_window_start=now,
        forecast_window_end=now + timedelta(hours=3),
        source_forecast_version_id='forecast-version-2',
    )

    assert completed.forecast_window_start == now
    assert completed.forecast_window_end == now + timedelta(hours=3)
    assert completed.source_forecast_version_id == 'forecast-version-2'


@pytest.mark.unit
def test_visualization_snapshot_service_covers_store_and_fallback_paths() -> None:
    class Repo:
        def __init__(self) -> None:
            self.snapshot = SimpleNamespace(
                visualization_snapshot_id='snapshot-1',
                payload_json=json.dumps(
                    {
                        'visualizationLoadId': 'old-load',
                        'forecastProduct': 'daily_1_day',
                        'forecastGranularity': 'hourly',
                        'categoryFilter': {'selectedCategory': 'Roads', 'selectedCategories': ['Roads', 'Waste']},
                        'historyWindowStart': '2026-03-17T00:00:00Z',
                        'historyWindowEnd': '2026-03-24T00:00:00Z',
                        'forecastWindowStart': '2026-03-24T00:00:00Z',
                        'forecastWindowEnd': '2026-03-25T00:00:00Z',
                        'forecastBoundary': '2026-03-24T00:00:00Z',
                        'lastUpdatedAt': '2026-03-24T01:00:00Z',
                        'sourceCleanedDatasetVersionId': 'dataset-1',
                        'sourceForecastVersionId': 'forecast-1',
                        'sourceWeeklyForecastVersionId': None,
                        'historicalSeries': [{'timestamp': '2026-03-23T00:00:00Z', 'value': 2.0}],
                        'forecastSeries': [{'timestamp': '2026-03-24T00:00:00Z', 'pointForecast': 4.0}],
                        'uncertaintyBands': None,
                        'alerts': [],
                        'pipelineStatus': [],
                        'viewStatus': 'success',
                        'degradationType': None,
                        'summary': 'Visualization is available.',
                    }
                ),
                created_at=datetime(2026, 3, 24, 2, 0),
                expires_at=datetime(2026, 3, 24, 5, 0),
            )
            self.created = None
            self.lookup = None

        def create_snapshot(self, **kwargs):
            self.created = kwargs
            return SimpleNamespace(visualization_snapshot_id='created-snapshot')

        def get_latest_eligible_snapshot(self, **kwargs):
            self.lookup = kwargs
            return self.snapshot

    repo = Repo()
    service = VisualizationSnapshotService(repo, fallback_age_hours=6)
    load_record = SimpleNamespace(visualization_load_id='load-1')
    source = SimpleNamespace(
        source_cleaned_dataset_version_id='dataset-1',
        source_forecast_run_id='run-1',
        source_weekly_forecast_run_id=None,
        forecast_window_start=datetime(2026, 3, 24, tzinfo=timezone.utc),
        forecast_window_end=datetime(2026, 3, 25, tzinfo=timezone.utc),
    )
    response = ForecastVisualizationRead(
        visualizationLoadId='load-1',
        forecastProduct='daily_1_day',
        forecastGranularity='hourly',
        categoryFilter=CategoryFilter(selectedCategory='Roads', selectedCategories=['Roads', 'Waste']),
        historyWindowStart=datetime(2026, 3, 17, tzinfo=timezone.utc),
        historyWindowEnd=datetime(2026, 3, 24, tzinfo=timezone.utc),
        forecastWindowStart=datetime(2026, 3, 24, tzinfo=timezone.utc),
        forecastWindowEnd=datetime(2026, 3, 25, tzinfo=timezone.utc),
        forecastBoundary=datetime(2026, 3, 24, tzinfo=timezone.utc),
        lastUpdatedAt=datetime(2026, 3, 24, 1, tzinfo=timezone.utc),
        sourceCleanedDatasetVersionId='dataset-1',
        sourceForecastVersionId='forecast-1',
        sourceWeeklyForecastVersionId=None,
        historicalSeries=[VisualizationPoint(timestamp=datetime(2026, 3, 23, tzinfo=timezone.utc), value=2.0)],
        forecastSeries=[VisualizationForecastPoint(timestamp=datetime(2026, 3, 24, tzinfo=timezone.utc), pointForecast=4.0)],
        uncertaintyBands=None,
        alerts=[],
        pipelineStatus=[],
        viewStatus='success',
        degradationType=None,
        summary='Visualization is available.',
    )

    created = service.store_snapshot(load_record=load_record, source=source, response=response)
    assert created.visualization_snapshot_id == 'created-snapshot'
    assert repo.created['service_category_filter'] == 'Roads,Waste'
    assert repo.created['expires_in_hours'] == 6

    fallback, snapshot = service.get_fallback_visualization(
        forecast_product='daily_1_day',
        service_categories=[' Waste ', 'Roads'],
        visualization_load_id='load-2',
        now=datetime(2026, 3, 24, 3, tzinfo=timezone.utc),
    )
    assert snapshot.visualization_snapshot_id == 'snapshot-1'
    assert repo.lookup['service_category_filter'] == 'Roads,Waste'
    assert fallback.visualization_load_id == 'load-2'
    assert fallback.view_status == 'fallback_shown'
    assert fallback.fallback is not None
    assert fallback.fallback.created_at.tzinfo == timezone.utc
    assert fallback.fallback.expires_at.tzinfo == timezone.utc


@pytest.mark.unit
def test_snapshot_service_prefers_load_record_filter_for_large_all_category_requests() -> None:
    class Repo:
        def __init__(self):
            self.created = None

        def create_snapshot(self, **kwargs):
            self.created = kwargs
            return SimpleNamespace(visualization_snapshot_id='created-snapshot')

    repo = Repo()
    service = VisualizationSnapshotService(repo, fallback_age_hours=6)
    load_record = SimpleNamespace(visualization_load_id='load-1', service_category_filter=None)
    source = SimpleNamespace(
        source_cleaned_dataset_version_id='dataset-1',
        source_forecast_run_id='run-1',
        source_weekly_forecast_run_id=None,
        forecast_window_start=datetime(2026, 3, 24, tzinfo=timezone.utc),
        forecast_window_end=datetime(2026, 3, 25, tzinfo=timezone.utc),
    )
    response = ForecastVisualizationRead(
        visualizationLoadId='load-1',
        forecastProduct='daily_1_day',
        forecastGranularity='hourly',
        categoryFilter=CategoryFilter(selectedCategory='Roads', selectedCategories=[f'Category {idx}' for idx in range(200)]),
        historyWindowStart=datetime(2026, 3, 17, tzinfo=timezone.utc),
        historyWindowEnd=datetime(2026, 3, 24, tzinfo=timezone.utc),
        forecastWindowStart=datetime(2026, 3, 24, tzinfo=timezone.utc),
        forecastWindowEnd=datetime(2026, 3, 25, tzinfo=timezone.utc),
        forecastBoundary=datetime(2026, 3, 24, tzinfo=timezone.utc),
        lastUpdatedAt=datetime(2026, 3, 24, 1, tzinfo=timezone.utc),
        sourceCleanedDatasetVersionId='dataset-1',
        sourceForecastVersionId='forecast-1',
        sourceWeeklyForecastVersionId=None,
        historicalSeries=[VisualizationPoint(timestamp=datetime(2026, 3, 23, tzinfo=timezone.utc), value=2.0)],
        forecastSeries=[VisualizationForecastPoint(timestamp=datetime(2026, 3, 24, tzinfo=timezone.utc), pointForecast=4.0)],
        uncertaintyBands=None,
        alerts=[],
        pipelineStatus=[],
        viewStatus='success',
        degradationType=None,
        summary='Visualization is available.',
    )

    service.store_snapshot(load_record=load_record, source=source, response=response)
    assert repo.created['service_category_filter'] is None


@pytest.mark.unit
def test_visualization_source_service_covers_positive_multi_select_and_category_listing_paths() -> None:
    service = ForecastVisualizationSourceService()

    daily = service.normalize_daily(
        marker=SimpleNamespace(source_cleaned_dataset_version_id='dataset-1', updated_at=datetime(2026, 3, 24)),
        version=SimpleNamespace(
            forecast_version_id='forecast-1',
            forecast_run_id='run-1',
            horizon_start=datetime(2026, 3, 24),
            horizon_end=datetime(2026, 3, 25),
        ),
        buckets=[
            SimpleNamespace(service_category='Roads', bucket_start=datetime(2026, 3, 24, 1), point_forecast=3.0, quantile_p10=1.0, quantile_p50=3.0, quantile_p90=5.0),
            SimpleNamespace(service_category='Waste', bucket_start=datetime(2026, 3, 24, 2), point_forecast=4.0, quantile_p10=2.0, quantile_p50=4.0, quantile_p90=6.0),
            SimpleNamespace(service_category='Transit', bucket_start=datetime(2026, 3, 24, 3), point_forecast=9.0, quantile_p10=7.0, quantile_p50=9.0, quantile_p90=11.0),
        ],
        service_categories=['Roads', 'Waste'],
    )
    assert daily is not None
    assert len(daily.forecast_series) == 2
    assert daily.uncertainty_bands is not None

    weekly = service.normalize_weekly(
        marker=SimpleNamespace(source_cleaned_dataset_version_id='dataset-2', updated_at=datetime(2026, 3, 24)),
        version=SimpleNamespace(
            weekly_forecast_version_id='weekly-1',
            weekly_forecast_run_id='weekly-run-1',
            week_start_local=datetime(2026, 3, 24),
            week_end_local=datetime(2026, 3, 31),
        ),
        buckets=[
            SimpleNamespace(service_category='Roads', forecast_date_local=date(2026, 3, 24), point_forecast=7.0, quantile_p10=5.0, quantile_p50=7.0, quantile_p90=9.0),
            SimpleNamespace(service_category='Waste', forecast_date_local=date(2026, 3, 25), point_forecast=8.0, quantile_p10=6.0, quantile_p50=8.0, quantile_p90=10.0),
        ],
        service_categories=['Roads', 'Waste'],
    )
    assert weekly is not None
    assert len(weekly.forecast_series) == 2
    assert weekly.uncertainty_bands is not None
    assert service.list_daily_categories([SimpleNamespace(service_category='Waste'), SimpleNamespace(service_category='Roads'), SimpleNamespace(service_category='')]) == ['Roads', 'Waste']
    assert service.list_weekly_categories([SimpleNamespace(service_category='Waste'), SimpleNamespace(service_category='Roads'), SimpleNamespace(service_category=None)]) == ['Roads', 'Waste']


@pytest.mark.unit
def test_historical_demand_service_covers_multi_select_and_timestamp_normalization() -> None:
    repo = _HistoryRepo(
        records=[
            {'requested_at': '2026-03-20T05:15:00', 'category': 'Roads'},
            {'requested_at': '2026-03-20T08:20:00Z', 'category': 'Waste'},
            {'requested_at': '2026-03-20T08:20:00Z', 'category': 'Transit'},
            {'requested_at': 'bad-value', 'category': 'Roads'},
        ],
        current_dataset=SimpleNamespace(dataset_version_id='dataset-77'),
    )
    service = HistoricalDemandService(repo, 'edmonton_311')
    series, dataset_version_id, start, end = service.build_series(
        boundary=datetime(2026, 3, 24),
        granularity='hourly',
        service_categories=['Roads', 'Waste'],
    )
    assert dataset_version_id == 'dataset-77'
    assert start.tzinfo == timezone.utc
    assert end.tzinfo == timezone.utc
    assert [point.value for point in series] == [1.0, 1.0]
    assert all(point.timestamp.tzinfo == timezone.utc for point in series)


@pytest.mark.unit
def test_forecast_visualization_service_covers_fallback_and_remaining_branch_paths() -> None:
    source = NormalizedForecastSource(
        forecast_product='daily_1_day',
        forecast_granularity='hourly',
        source_forecast_version_id='forecast-1',
        source_weekly_forecast_version_id=None,
        source_forecast_run_id='run-1',
        source_weekly_forecast_run_id=None,
        source_cleaned_dataset_version_id='dataset-1',
        forecast_window_start=datetime(2026, 3, 24, tzinfo=timezone.utc),
        forecast_window_end=datetime(2026, 3, 25, tzinfo=timezone.utc),
        forecast_boundary=datetime(2026, 3, 24, tzinfo=timezone.utc),
        last_updated_at=datetime(2026, 3, 24, 1, tzinfo=timezone.utc),
        forecast_series=[VisualizationForecastPoint(timestamp=datetime(2026, 3, 24, tzinfo=timezone.utc), pointForecast=12.0)],
        uncertainty_bands=UncertaintyBands(labels=['P10', 'P50', 'P90'], points=[UncertaintyPoint(timestamp=datetime(2026, 3, 24, tzinfo=timezone.utc), p10=10.0, p50=12.0, p90=14.0)]),
    )

    fallback_response = ForecastVisualizationRead(
        visualizationLoadId='fallback-load',
        forecastProduct='daily_1_day',
        forecastGranularity='hourly',
        categoryFilter=CategoryFilter(selectedCategory='Roads', selectedCategories=['Roads', 'Waste']),
        historyWindowStart=datetime(2026, 3, 17, tzinfo=timezone.utc),
        historyWindowEnd=datetime(2026, 3, 24, tzinfo=timezone.utc),
        forecastWindowStart=datetime(2026, 3, 24, tzinfo=timezone.utc),
        forecastWindowEnd=datetime(2026, 3, 25, tzinfo=timezone.utc),
        forecastBoundary=datetime(2026, 3, 24, tzinfo=timezone.utc),
        lastUpdatedAt=datetime(2026, 3, 24, 1, tzinfo=timezone.utc),
        sourceCleanedDatasetVersionId='dataset-1',
        sourceForecastVersionId='forecast-1',
        sourceWeeklyForecastVersionId=None,
        historicalSeries=[VisualizationPoint(timestamp=datetime(2026, 3, 23, tzinfo=timezone.utc), value=1.0)],
        forecastSeries=[VisualizationForecastPoint(timestamp=datetime(2026, 3, 24, tzinfo=timezone.utc), pointForecast=12.0)],
        uncertaintyBands=None,
        alerts=[],
        pipelineStatus=[],
        viewStatus='fallback_shown',
        degradationType=None,
        summary='Fallback shown.',
    )

    fallback_snapshot = SimpleNamespace(visualization_snapshot_id='snapshot-99')

    class SnapshotStub(_StubSnapshotService):
        def __init__(self):
            super().__init__()
            self.calls = []

        def get_fallback_visualization(self, **kwargs):
            self.calls.append(kwargs)
            return fallback_response, fallback_snapshot

    fallback_repo = _StubVisualizationRepository()
    fallback_service = ForecastVisualizationService(
        cleaned_dataset_repository=None,
        forecast_repository=_StubDailyForecastRepository(marker=None, version=None),
        weekly_forecast_repository=_StubWeeklyForecastRepository(),
        visualization_repository=fallback_repo,
        historical_demand_service=_StubHistoryService(([], None, datetime(2026, 3, 17, tzinfo=timezone.utc), datetime(2026, 3, 24, tzinfo=timezone.utc))),
        source_service=_StubSourceService(),
        snapshot_service=SnapshotStub(),
        settings=SimpleNamespace(forecast_product_name='daily_1_day_demand', weekly_forecast_product_name='weekly_7_day_demand'),
        logger=__import__('logging').getLogger('test.branch.visualization.fallback'),
    )

    fallback = fallback_service.get_current_visualization(
        forecast_product='daily_1_day',
        service_categories=[' Roads ', '', 'Waste', 'Roads'],
    )
    assert fallback.visualization_load_id == 'fallback-load'
    assert fallback_repo.completed[-1][1]['status'] == 'fallback_shown'
    assert fallback_repo.completed[-1][1]['fallback_snapshot_id'] == 'snapshot-99'
    assert fallback_repo.completed[-1][1]['source_forecast_version_id'] == 'forecast-1'
    assert fallback_repo.created[0].service_category_filter == 'Roads,Waste'

    success_service = _visualization_service(
        daily_repo=_StubDailyForecastRepository(
            marker=SimpleNamespace(forecast_version_id='forecast-1'),
            version=SimpleNamespace(storage_status='stored', forecast_version_id='forecast-1'),
        ),
        source_service=_StubSourceService(daily=source),
        history=([VisualizationPoint(timestamp=datetime(2026, 3, 23, tzinfo=timezone.utc), value=1.0)], None, datetime(2026, 3, 17, tzinfo=timezone.utc), datetime(2026, 3, 24, tzinfo=timezone.utc)),
    )
    success = success_service.get_current_visualization(forecast_product='daily_1_day', service_categories=['Roads'])
    assert success.view_status == 'success'
    assert success.pipeline_status[-1].code == 'visualization_ready'
    assert success_service.visualization_repository.completed[-1][1]['status'] == 'success'
    assert ForecastVisualizationService._build_alerts(None) == []

    empty_daily_service = _visualization_service(daily_repo=_StubDailyForecastRepository(marker=None, version=None))
    assert empty_daily_service.list_service_categories(forecast_product='daily_1_day').categories == []

    weekly_categories_service = _visualization_service(
        weekly_repo=_StubWeeklyForecastRepository(
            marker=SimpleNamespace(weekly_forecast_version_id='weekly-version-1'),
            version=SimpleNamespace(storage_status='stored', weekly_forecast_version_id='weekly-version-1'),
        ),
        source_service=_StubSourceService(weekly=source),
    )
    weekly_categories_service.weekly_forecast_repository.list_buckets = lambda _version_id: [SimpleNamespace(service_category='Waste'), SimpleNamespace(service_category='Roads')]
    weekly_categories_service.source_service.list_weekly_categories = lambda buckets: ['Roads', 'Waste']
    assert weekly_categories_service.list_service_categories(forecast_product='weekly_7_day').categories == ['Roads', 'Waste']
    assert _visualization_service(weekly_repo=_StubWeeklyForecastRepository(marker=None, version=None)).list_service_categories(forecast_product='weekly_7_day').categories == []



@pytest.mark.unit
def test_visualization_route_logs_and_reraises_on_unexpected_error(session, monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingService:
        def get_current_visualization(self, **kwargs):
            raise RuntimeError('boom')

    class LoggerStub:
        def __init__(self):
            self.calls = []

        def exception(self, message, **kwargs):
            self.calls.append((message, kwargs))

    logger = LoggerStub()
    monkeypatch.setattr(visualization_routes, 'build_visualization_service', lambda session: FailingService())
    original_get_logger = visualization_routes.logging.getLogger
    monkeypatch.setattr(visualization_routes.logging, 'getLogger', lambda name=None: logger if name == 'forecast_visualization.api' else original_get_logger(name))

    with pytest.raises(RuntimeError):
        visualization_routes.get_current_forecast_visualization(
            forecast_product='daily_1_day',
            service_category=['Roads'],
            exclude_service_category=['Waste'],
            session=session,
            _claims={},
        )

    assert logger.calls[0][0] == 'Failed to build current visualization'
    assert logger.calls[0][1]['extra']['service_categories'] == ['Roads']
    assert logger.calls[0][1]['extra']['excluded_service_categories'] == ['Waste']


@pytest.mark.unit
def test_visualization_source_service_covers_remaining_aggregate_and_uncertainty_paths() -> None:
    service = ForecastVisualizationSourceService()

    assert service.normalize_daily(
        marker=SimpleNamespace(source_cleaned_dataset_version_id='dataset-1', updated_at=datetime(2026, 3, 24, tzinfo=timezone.utc)),
        version=SimpleNamespace(forecast_version_id='forecast-1', forecast_run_id='run-1', horizon_start=datetime(2026, 3, 24, tzinfo=timezone.utc), horizon_end=datetime(2026, 3, 25, tzinfo=timezone.utc)),
        buckets=[SimpleNamespace(service_category='Roads', bucket_start=datetime(2026, 3, 24, tzinfo=timezone.utc), point_forecast=None, quantile_p10=1.0, quantile_p50=2.0, quantile_p90=3.0)],
    ) is None

    assert service.normalize_weekly(
        marker=SimpleNamespace(source_cleaned_dataset_version_id='dataset-1', updated_at=datetime(2026, 3, 24, tzinfo=timezone.utc)),
        version=SimpleNamespace(weekly_forecast_version_id='weekly-1', weekly_forecast_run_id='weekly-run-1', week_start_local=date(2026, 3, 24), week_end_local=date(2026, 3, 31)),
        buckets=[SimpleNamespace(service_category='Roads', forecast_date_local=date(2026, 3, 24), point_forecast='bad', quantile_p10=1.0, quantile_p50=2.0, quantile_p90=3.0)],
    ) is None

    daily_uncertainty = service._build_uncertainty_daily([
        SimpleNamespace(bucket_start=datetime(2026, 3, 24, tzinfo=timezone.utc), quantile_p10=1.2, quantile_p50=2.4, quantile_p90=3.6)
    ])
    assert daily_uncertainty is not None
    assert daily_uncertainty.points[0].p10 == 1
    assert daily_uncertainty.points[0].p50 == 2
    assert daily_uncertainty.points[0].p90 == 4

    weekly_uncertainty = service._build_uncertainty_weekly([
        SimpleNamespace(forecast_date_local=date(2026, 3, 24), quantile_p10=4.2, quantile_p50=5.5, quantile_p90=6.8)
    ])
    assert weekly_uncertainty is not None
    assert weekly_uncertainty.points[0].p10 == 4
    assert weekly_uncertainty.points[0].p50 == 6
    assert weekly_uncertainty.points[0].p90 == 7

    assert service._build_uncertainty_from_aggregates([
        {'timestamp': datetime(2026, 3, 24, tzinfo=timezone.utc), 'p10': None, 'p50': 2.0, 'p90': 3.0}
    ]) is None

    daily_aggregated = _aggregate_daily([
        SimpleNamespace(bucket_start=datetime(2026, 3, 24, tzinfo=timezone.utc), point_forecast='bad', quantile_p10=1.0, quantile_p50=2.0, quantile_p90=3.0),
        SimpleNamespace(bucket_start=datetime(2026, 3, 24, 1, tzinfo=timezone.utc), point_forecast=3.0, quantile_p10=None, quantile_p50=2.0, quantile_p90=3.0),
    ])
    assert len(daily_aggregated) == 1
    assert daily_aggregated[0]['p10'] is None
    assert daily_aggregated[0]['p50'] is None
    assert daily_aggregated[0]['p90'] is None

    weekly_aggregated = _aggregate_weekly([
        SimpleNamespace(forecast_date_local='bad-date', point_forecast=2.0, quantile_p10=1.0, quantile_p50=2.0, quantile_p90=3.0),
        SimpleNamespace(forecast_date_local=date(2026, 3, 24), point_forecast=5.0, quantile_p10=None, quantile_p50=2.0, quantile_p90=3.0),
    ])
    assert len(weekly_aggregated) == 1
    assert weekly_aggregated[0]['p10'] is None
    assert weekly_aggregated[0]['p50'] is None
    assert weekly_aggregated[0]['p90'] is None

    assert _coerce_float(object()) is None
    assert _coerce_timestamp('bad-timestamp') is None
    assert _as_utc(date(2026, 3, 24)).tzinfo == timezone.utc


@pytest.mark.unit
def test_snapshot_service_serializes_excluded_category_filters() -> None:
    assert visualization_snapshot_service._serialize_category_filter([' Roads '], [' Waste ', 'Transit']) == 'exclude:Transit,Waste'
