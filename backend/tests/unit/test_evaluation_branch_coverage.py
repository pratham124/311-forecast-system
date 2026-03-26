
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app import main as main_module
from app.core.logging import (
    configure_logging,
    redact_value,
    sanitize_mapping,
    summarize_evaluation_event,
    summarize_visualization_event,
)
from app.models import CurrentDatasetMarker, DatasetRecord, DatasetVersion
from app.repositories.cleaned_dataset_repository import (
    CleanedDatasetRepository,
    _extract_geography_key,
    _to_requested_at_string,
)
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.evaluation_repository import EvaluationRepository
from app.schemas.evaluation import EvaluationRunTrigger
from app.services import evaluation_scope_service as scope_module
from app.services.baseline_service import BaselineGenerationError, BaselineService
from app.services.evaluation_metrics import compute_metric_values
from app.services.evaluation_scope_service import ActualsNotReadyError, EvaluationScope, EvaluationScopeService, MissingForecastScopeError
from app.services.evaluation_segments import build_evaluation_segments
from app.services.evaluation_service import EvaluationService


UTC = timezone.utc


def _seed_cleaned_dataset(session, *, dataset_version_id: str, run_id: str) -> DatasetVersion:
    repository = DatasetRepository(session)
    version = repository.create_dataset_version(
        source_name='edmonton_311',
        run_id=run_id,
        candidate_id=None,
        record_count=0,
        records=[],
        validation_status='approved',
        dataset_kind='cleaned',
        approved_by_validation_run_id=f'{run_id}-validation',
    )
    if version.dataset_version_id != dataset_version_id:
        version.dataset_version_id = dataset_version_id
        session.flush()
    repository.activate_dataset('edmonton_311', version.dataset_version_id, f'{run_id}-validation')
    session.commit()
    return version


def _create_run_and_result(repo: EvaluationRepository, *, run_id: str, dataset_version_id: str, forecast_product_name: str = 'daily_1_day'):
    start = datetime(2026, 3, 20, 0, tzinfo=UTC)
    end = start + timedelta(hours=3)
    run = repo.create_run(
        trigger_type='on_demand',
        forecast_product_name=forecast_product_name,
        source_cleaned_dataset_version_id=dataset_version_id,
        source_forecast_version_id=None,
        source_weekly_forecast_version_id=None,
        evaluation_window_start=start,
        evaluation_window_end=end,
    )
    run.evaluation_run_id = run_id
    repo.session.flush()
    result = repo.create_result(
        evaluation_run_id=run.evaluation_run_id,
        forecast_product_name=forecast_product_name,
        source_cleaned_dataset_version_id=dataset_version_id,
        source_forecast_version_id=None,
        source_weekly_forecast_version_id=None,
        evaluation_window_start=start,
        evaluation_window_end=end,
        comparison_status='complete',
        baseline_methods=['seasonal_naive', 'moving_average'],
        metric_set=['mae', 'rmse', 'mape'],
        summary='stored summary',
        comparison_summary='comparison summary',
    )
    repo.session.commit()
    return run, result


@pytest.mark.unit
def test_logging_schema_and_metric_guard_branches() -> None:
    assert redact_value(None) is None
    assert redact_value('abcd') == '***'
    assert redact_value('abcdef') == 'ab***ef'
    assert redact_value({'token': 'abcdef'}) == {'token': 'ab***ef'}
    assert redact_value(['abcdef', 3]) == ['ab***ef', 3]
    assert sanitize_mapping({'Authorization': 'abcdef', 'nested': {'password': 'secret'}, 'items': [{'api_key': 'abcde'}]}) == {
        'Authorization': 'ab***ef',
        'nested': {'password': 'se***et'},
        'items': [{'api_key': 'ab***de'}],
    }
    assert configure_logging().name == 'forecast_system'
    assert summarize_visualization_event('visualized', token='abcdef')['token'] == 'ab***ef'

    partial = summarize_evaluation_event('evaluation.stored', outcome='partial_success', run_id='run-1')
    failure = summarize_evaluation_event('evaluation.failed', outcome='failure', run_id='run-2')
    success = summarize_evaluation_event('evaluation.stored', outcome='unexpected', run_id='run-3')
    assert partial['outcome'] == 'partial_success'
    assert failure['outcome'] == 'failure'
    assert success['outcome'] == 'success'

    with pytest.raises(ValidationError):
        EvaluationRunTrigger(forecastProduct='daily_1_day', triggerType='scheduled')

    with pytest.raises(ValueError):
        compute_metric_values([], 'forecast_engine', 'Forecast Engine')

    with pytest.raises(ValueError):
        build_evaluation_segments([])


@pytest.mark.unit
def test_baseline_service_remaining_branches() -> None:
    settings = SimpleNamespace(source_name='edmonton_311')
    service = BaselineService(
        SimpleNamespace(
            list_current_cleaned_records=lambda _source_name, **_kwargs: [
                {'category': 'Roads'},
                {'category': 'Roads', 'requested_at': '2026-03-10T00:00:00Z'},
            ]
        ),
        settings,
    )

    with pytest.raises(BaselineGenerationError, match='No aligned rows'):
        service.generate_baselines('daily_1_day', [])

    with pytest.raises(BaselineGenerationError, match='No historical baseline series'):
        service.generate_baselines(
            'daily_1_day',
            [
                {
                    'bucket_start': datetime(2026, 3, 20, 0, tzinfo=UTC),
                    'bucket_end': datetime(2026, 3, 20, 1, tzinfo=UTC),
                    'service_category': 'Waste',
                    'geography_key': None,
                    'forecast_engine': 2.0,
                    'actual': 1.0,
                }
            ],
        )

    ok_service = BaselineService(
        SimpleNamespace(
            list_current_cleaned_records=lambda _source_name, **_kwargs: [
                {'category': 'Roads', 'requested_at': '2026-03-10T00:00:00Z'},
                {'category': 'Roads', 'requested_at': '2026-03-11T00:00:00Z'},
            ]
        ),
        settings,
    )
    enriched = ok_service.generate_baselines(
        'weekly_7_day',
        [
            {
                'bucket_start': datetime(2026, 3, 20, 0, tzinfo=UTC),
                'bucket_end': datetime(2026, 3, 21, 0, tzinfo=UTC),
                'service_category': 'Roads',
                'geography_key': None,
                'forecast_engine': 3.0,
                'actual': 2.0,
            }
        ],
    )
    assert enriched[0]['seasonal_naive'] == 1.0
    assert enriched[0]['moving_average'] == 1.0

    category_only_service = BaselineService(
        SimpleNamespace(
            list_current_cleaned_records=lambda _source_name, **_kwargs: [
                {'category': 'Bees/Wasps', 'requested_at': '2026-03-10T00:15:00Z', 'ward': 'CROMDALE'},
                {'category': 'Bees/Wasps', 'requested_at': '2026-03-10T00:25:00Z', 'ward': 'DOWNTOWN'},
            ]
        ),
        settings,
    )
    category_only_enriched = category_only_service.generate_baselines(
        'daily_1_day',
        [
            {
                'bucket_start': datetime(2026, 3, 20, 0, tzinfo=UTC),
                'bucket_end': datetime(2026, 3, 20, 1, tzinfo=UTC),
                'service_category': 'Bees/Wasps',
                'geography_key': None,
                'forecast_engine': 0.5,
                'actual': 2.0,
            }
        ],
    )
    assert category_only_enriched[0]['seasonal_naive'] == 2.0
    assert category_only_enriched[0]['moving_average'] == 2.0


@pytest.mark.unit
def test_cleaned_dataset_repository_remaining_branches(session) -> None:
    repository = CleanedDatasetRepository(session)
    assert _to_requested_at_string(datetime(2026, 3, 20, 0)) == '2026-03-20T00:00:00Z'
    assert _extract_geography_key({'district': ' District 1 '}) == 'District 1'
    assert _extract_geography_key({'district': '  '}) is None
    assert repository.get_current_approved_dataset('missing-source') is None
    assert repository.list_current_cleaned_records('missing-source') == []

    session.add(CurrentDatasetMarker(source_name='edmonton_311', dataset_version_id='missing-dataset', updated_by_run_id='run-0', record_count=0))
    session.commit()
    assert repository.get_current_approved_dataset('edmonton_311') is None

    pending_dataset = DatasetVersion(
        dataset_version_id='pending-dataset',
        source_name='edmonton_311',
        ingestion_run_id='run-pending',
        candidate_dataset_id=None,
        source_dataset_version_id=None,
        record_count=0,
        validation_status='pending',
        storage_status='stored',
        dataset_kind='source',
        duplicate_group_count=0,
        approved_by_validation_run_id=None,
        is_current=False,
    )
    session.add(pending_dataset)
    session.get(CurrentDatasetMarker, 'edmonton_311').dataset_version_id = 'pending-dataset'
    session.commit()
    assert repository.get_current_approved_dataset('edmonton_311') is None

    _seed_cleaned_dataset(session, dataset_version_id='dataset-latest', run_id='seed-latest')
    session.add(
        DatasetRecord(
            dataset_version_id='dataset-latest',
            source_record_id='bad-json',
            requested_at='2026-03-20T02:00:00Z',
            category='Roads',
            record_payload='{bad-json}',
        )
    )
    session.add(
        DatasetRecord(
            dataset_version_id='dataset-latest',
            source_record_id='record-2',
            requested_at='2026-03-20T03:00:00Z',
            category='Roads',
            record_payload='{"service_request_id": "record-2", "requested_at": "2026-03-20T03:00:00Z", "category": "Roads"}',
        )
    )
    session.add(
        DatasetRecord(
            dataset_version_id='dataset-latest',
            source_record_id='record-3',
            requested_at='2026-03-20T03:00:00Z',
            category='Roads',
            record_payload='{"service_request_id": "record-3", "category": "Roads"}',
        )
    )
    session.add(
        DatasetRecord(
            dataset_version_id='dataset-latest',
            source_record_id='record-4',
            requested_at='2026-03-20T03:00:00Z',
            category='Roads',
            record_payload='{"service_request_id": "record-4", "requested_at": "2026-03-20T03:00:00Z", "category": "Roads"}',
        )
    )
    session.commit()

    records = repository.list_dataset_records('dataset-latest')
    assert records[0]['service_request_id'] == 'bad-json'
    assert repository.get_latest_current_requested_at('edmonton_311') == datetime(2026, 3, 20, 3, tzinfo=UTC)

    repository.upsert_current_cleaned_records(
        source_name='edmonton_311',
        ingestion_run_id='seed-latest',
        source_dataset_version_id='dataset-latest',
        approved_dataset_version_id='dataset-latest',
        approved_by_validation_run_id='seed-latest-validation',
        cleaned_records=[
            {
                'service_request_id': '',
                'requested_at': '2026-03-21T03:00:00Z',
                'category': 'Skip',
            },
            {
                'service_request_id': 'current-1',
                'requested_at': '2026-03-21T04:00:00Z',
                'category': 'Roads',
                'neighbourhood': 'Central',
            },
            {
                'service_request_id': 'current-2',
                'requested_at': '2026-03-21T05:00:00Z',
                'category': 'Waste',
            },
        ],
    )
    assert repository.count_current_cleaned_records('edmonton_311') == 2

    repository.upsert_current_cleaned_records(
        source_name='edmonton_311',
        ingestion_run_id='seed-latest-2',
        source_dataset_version_id='dataset-latest',
        approved_dataset_version_id='dataset-latest',
        approved_by_validation_run_id='seed-latest-validation-2',
        cleaned_records=[
            {
                'service_request_id': 'current-1',
                'requested_at': '2026-03-21T06:00:00Z',
                'category': 'Updated Roads',
                'geography_key': 'Updated Central',
            }
        ],
    )
    assert repository.count_current_cleaned_records('edmonton_311') == 2
    listed = repository.list_current_cleaned_records(
        'edmonton_311',
        start_time=datetime(2026, 3, 21, 0),
        end_time=datetime(2026, 3, 22, 0),
    )
    updated = next(item for item in listed if item['service_request_id'] == 'current-1')
    assert updated['category'] == 'Updated Roads'
    assert repository.get_latest_current_requested_at('edmonton_311') == datetime(2026, 3, 21, 6, tzinfo=UTC)

    row = repository.session.query(scope_module.CleanedDatasetRepository.__mro__[0]).first() if False else None
    current_row = repository.session.query(type(repository.session.query)).__class__ if False else None
    stored_row = repository.session.query  # noop to keep lint quiet in this environment
    del row, current_row, stored_row

    current_record = repository.session.get(scope_module.CleanedDatasetRepository.__mro__[0], None) if False else None
    del current_record

    from app.models import CleanedCurrentRecord
    saved_row = repository.session.get(CleanedCurrentRecord, 'current-1')
    assert saved_row is not None
    saved_row.record_payload = '{bad-json}'
    saved_row.geography_key = 'Central'
    second_row = repository.session.get(CleanedCurrentRecord, 'current-2')
    assert second_row is not None
    second_row.record_payload = '{bad-json}'
    second_row.geography_key = None
    session.commit()
    fallback_listed = repository.list_current_cleaned_records('edmonton_311')
    central = next(item for item in fallback_listed if item['service_request_id'] == 'current-1')
    no_geo = next(item for item in fallback_listed if item['service_request_id'] == 'current-2')
    assert central['geography_key'] == 'Central'
    assert 'geography_key' not in no_geo


@pytest.mark.unit
def test_evaluation_scope_service_remaining_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    daily_marker = SimpleNamespace(
        forecast_version_id='forecast-1',
        horizon_start=datetime(2026, 3, 20, 0),
        horizon_end=datetime(2026, 3, 20, 3),
    )
    weekly_marker = SimpleNamespace(
        weekly_forecast_version_id='weekly-1',
        week_start_local=datetime(2026, 3, 23, 0, tzinfo=UTC),
        week_end_local=datetime(2026, 3, 26, 0, tzinfo=UTC),
    )
    cleaned_repo = SimpleNamespace(
        get_current_approved_dataset=lambda _source: SimpleNamespace(dataset_version_id='dataset-1'),
        list_current_cleaned_records=lambda _source, **_kwargs: [
            {'category': 'Roads'},
            {'requested_at': '2026-03-23T08:00:00Z', 'category': 'Roads', 'ward': 'Ward 2'},
        ],
    )
    forecast_repo = SimpleNamespace(
        find_latest_stored_version=lambda: None,
        get_current_marker=lambda _product: daily_marker,
        get_forecast_version=lambda _version_id: SimpleNamespace(geography_scope='category_only'),
        list_buckets=lambda _version_id: [
            SimpleNamespace(
                bucket_start=datetime(2026, 3, 20, 0),
                bucket_end=datetime(2026, 3, 20, 1),
                service_category='Roads',
                geography_key=None,
                point_forecast=2.0,
            ),
            SimpleNamespace(
                bucket_start=datetime(2026, 3, 20, 1, tzinfo=UTC),
                bucket_end=datetime(2026, 3, 20, 2, tzinfo=UTC),
                service_category='Roads',
                geography_key=None,
                point_forecast=3.0,
            ),
        ],
    )
    weekly_repo = SimpleNamespace(
        find_latest_stored_version=lambda: None,
        get_current_marker=lambda _product: weekly_marker,
        list_buckets=lambda _version_id: [
            SimpleNamespace(forecast_date_local=datetime(2026, 3, 23, tzinfo=UTC).date(), service_category='Roads', geography_key=None, point_forecast=5.0)
        ],
    )
    settings = SimpleNamespace(source_name='edmonton_311', forecast_product_name='daily_1_day_demand', weekly_forecast_product_name='weekly_7_day_demand', weekly_forecast_timezone='America/Edmonton')
    service = EvaluationScopeService(cleaned_repo, forecast_repo, weekly_repo, settings)

    daily_scope = service.resolve_scope('daily_1_day')
    engine_rows = service.list_engine_rows(daily_scope)
    assert daily_scope.source_forecast_version_id == 'forecast-1'
    assert engine_rows[0]['bucket_start'].tzinfo == UTC
    assert engine_rows[1]['bucket_start'].tzinfo == UTC

    weekly_scope = service.resolve_scope('weekly_7_day')
    assert weekly_scope.source_weekly_forecast_version_id == 'weekly-1'
    actual_rows = service.list_actual_rows(weekly_scope)
    assert actual_rows[(datetime(2026, 3, 23, 0, tzinfo=UTC), 'Roads', 'Ward 2')] == 1.0

    run_scope = service.resolve_scope_from_run(
        SimpleNamespace(
            forecast_product_name='daily_1_day',
            source_cleaned_dataset_version_id='dataset-1',
            source_forecast_version_id='forecast-2',
            source_weekly_forecast_version_id=None,
            evaluation_window_start=datetime(2026, 3, 24, 0, tzinfo=UTC),
            evaluation_window_end=datetime(2026, 3, 24, 3, tzinfo=UTC),
        )
    )
    assert run_scope.source_forecast_version_id == 'forecast-2'

    aligned = service.build_aligned_rows(
        weekly_scope,
        [{'bucket_start': datetime(2026, 3, 23, 0, tzinfo=UTC), 'service_category': 'Roads', 'geography_key': 'Ward 2', 'forecast_engine': 1.0}],
        actual_rows,
    )
    assert aligned[0]['actual'] == 1.0

    daily_aligned = service.build_aligned_rows(
        daily_scope,
        [{'bucket_start': datetime(2026, 3, 20, 0, tzinfo=UTC), 'service_category': 'Bees/Wasps', 'geography_key': None, 'forecast_engine': 0.5}],
        {
            (datetime(2026, 3, 20, 0, tzinfo=UTC), 'Bees/Wasps', 'CROMDALE'): 1.0,
            (datetime(2026, 3, 20, 0, tzinfo=UTC), 'Bees/Wasps', 'DOWNTOWN'): 2.0,
        },
    )
    assert daily_aligned[0]['actual'] == 3.0

    with pytest.raises(MissingForecastScopeError):
        service.list_engine_rows(
            EvaluationScope(
                forecast_product_name='weekly_7_day',
                source_cleaned_dataset_version_id='dataset-1',
                source_forecast_version_id=None,
                source_weekly_forecast_version_id=None,
                evaluation_window_start=datetime(2026, 3, 23, 0, tzinfo=UTC),
                evaluation_window_end=datetime(2026, 3, 26, 0, tzinfo=UTC),
            )
        )

    with pytest.raises(MissingForecastScopeError):
        service.build_aligned_rows(daily_scope, [], {})

    no_actuals_service = EvaluationScopeService(SimpleNamespace(get_current_approved_dataset=lambda _source: None), forecast_repo, weekly_repo, settings)
    with pytest.raises(ActualsNotReadyError):
        no_actuals_service.ensure_actuals_ready(daily_scope)

    weekly_fallback_service = EvaluationScopeService(
        SimpleNamespace(get_current_approved_dataset=lambda _source: None),
        SimpleNamespace(find_latest_stored_version=lambda: None, get_current_marker=lambda _product: None),
        SimpleNamespace(find_latest_stored_version=lambda: None, get_current_marker=lambda _product: None),
        settings,
    )

    class StubWeekWindowService:
        def __init__(self, _timezone):
            pass

        def get_week_window(self, _now):
            return SimpleNamespace(
                week_start_local=datetime(2026, 3, 30, 0, tzinfo=UTC),
                week_end_local=datetime(2026, 4, 6, 0, tzinfo=UTC),
            )

    monkeypatch.setattr(scope_module, 'WeekWindowService', StubWeekWindowService)
    weekly_fallback_scope = weekly_fallback_service.resolve_scope('weekly_7_day', now=datetime(2026, 3, 29, tzinfo=UTC))
    assert weekly_fallback_scope.evaluation_window_start == datetime(2026, 3, 30, 0, tzinfo=UTC)


@pytest.mark.unit
def test_evaluation_repository_remaining_branches(session, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_cleaned_dataset(session, dataset_version_id='dataset-eval', run_id='seed-eval')
    repo = EvaluationRepository(session)
    old_run, old_result = _create_run_and_result(repo, run_id='run-old', dataset_version_id='dataset-eval')
    new_run, new_result = _create_run_and_result(repo, run_id='run-new', dataset_version_id='dataset-eval')

    segment_payload = [
        {
            'segment_type': 'overall',
            'segment_key': 'overall',
            'segment_status': 'complete',
            'comparison_row_count': 1,
            'excluded_metric_count': 0,
            'notes': None,
            'method_metrics': [
                {
                    'compared_method': 'forecast_engine',
                    'method_name': 'Forecast Engine',
                    'metrics': [
                        {'metric_name': 'mae', 'metric_value': 1.0, 'is_excluded': False, 'exclusion_reason': None}
                    ],
                }
            ],
        }
    ]
    repo.replace_segments(old_result.evaluation_result_id, segment_payload)
    repo.replace_segments(old_result.evaluation_result_id, segment_payload)
    repo.activate_result(evaluation_result_id=old_result.evaluation_result_id, updated_by_run_id=old_run.evaluation_run_id)
    session.commit()

    activated = repo.activate_result(evaluation_result_id=new_result.evaluation_result_id, updated_by_run_id=new_run.evaluation_run_id)
    assert activated.evaluation_result_id == new_result.evaluation_result_id
    assert repo.get_current_result('daily_1_day').evaluation_result_id == new_result.evaluation_result_id
    assert repo.get_current_result('weekly_7_day') is None
    assert len(repo.list_results_for_product('daily_1_day')) == 2
    assert len(repo.list_results_for_product('daily_1_day', limit=1)) == 1
    assert repo.get_result_bundle('missing') is None
    bundles = repo.list_result_bundles_for_product('daily_1_day')
    assert bundles[0].result.evaluation_result_id in {old_result.evaluation_result_id, new_result.evaluation_result_id}

    with pytest.raises(ValueError, match='Evaluation run not found'):
        repo.require_run('missing-run')
    with pytest.raises(ValueError, match='Evaluation result not found'):
        repo.require_result('missing-result')

    repo_without_prior = EvaluationRepository(session)
    fresh_run, fresh_result = _create_run_and_result(repo_without_prior, run_id='run-fresh', dataset_version_id='dataset-eval', forecast_product_name='weekly_7_day')
    real_activate = repo_without_prior.activate_result

    def activate_then_fail(**kwargs):
        real_activate(**kwargs)
        raise RuntimeError('boom')

    monkeypatch.setattr(repo_without_prior, 'activate_result', activate_then_fail)
    with pytest.raises(RuntimeError, match='boom'):
        repo_without_prior.store_result_and_activate(evaluation_result_id=fresh_result.evaluation_result_id, updated_by_run_id=fresh_run.evaluation_run_id)
    assert repo_without_prior.get_current_marker('weekly_7_day') is None

    repo_no_marker = EvaluationRepository(session)
    no_marker_run, no_marker_result = _create_run_and_result(repo_no_marker, run_id='run-nomarker', dataset_version_id='dataset-eval', forecast_product_name='weekly_7_day')

    def fail_before_marker(**_kwargs):
        raise RuntimeError('no-marker-boom')

    monkeypatch.setattr(repo_no_marker, 'activate_result', fail_before_marker)
    with pytest.raises(RuntimeError, match='no-marker-boom'):
        repo_no_marker.store_result_and_activate(evaluation_result_id=no_marker_result.evaluation_result_id, updated_by_run_id=no_marker_run.evaluation_run_id)
    assert repo_no_marker.get_current_marker('weekly_7_day') is None

    repo_restore = EvaluationRepository(session)
    prior_run, prior_result = _create_run_and_result(repo_restore, run_id='run-prior', dataset_version_id='dataset-eval', forecast_product_name='weekly_7_day')
    repo_restore.activate_result(evaluation_result_id=prior_result.evaluation_result_id, updated_by_run_id=prior_run.evaluation_run_id)
    later_run, later_result = _create_run_and_result(repo_restore, run_id='run-later', dataset_version_id='dataset-eval', forecast_product_name='weekly_7_day')

    def delete_marker_then_fail(**_kwargs):
        marker = repo_restore.get_current_marker('weekly_7_day')
        if marker is not None:
            repo_restore.session.delete(marker)
            repo_restore.session.flush()
        raise RuntimeError('restore-boom')

    monkeypatch.setattr(repo_restore, 'activate_result', delete_marker_then_fail)
    with pytest.raises(RuntimeError, match='restore-boom'):
        repo_restore.store_result_and_activate(evaluation_result_id=later_result.evaluation_result_id, updated_by_run_id=later_run.evaluation_run_id)
    restored = repo_restore.get_current_marker('weekly_7_day')
    assert restored is not None
    assert restored.evaluation_result_id == prior_result.evaluation_result_id


@pytest.mark.unit
def test_evaluation_service_remaining_branches() -> None:
    running_scope = SimpleNamespace(forecast_product_name='daily_1_day')
    run = SimpleNamespace(
        evaluation_run_id='run-1',
        status='success',
        source_cleaned_dataset_version_id='dataset-1',
    )
    service = EvaluationService(
        evaluation_repository=SimpleNamespace(require_run=lambda _run_id: run),
        cleaned_dataset_repository=SimpleNamespace(),
        forecast_repository=SimpleNamespace(),
        weekly_forecast_repository=SimpleNamespace(),
        settings=SimpleNamespace(evaluation_baseline_methods='seasonal_naive,moving_average'),
    )
    assert service.execute_run('run-1') is run

    failing_run = SimpleNamespace(
        evaluation_run_id='run-2',
        status='running',
        source_cleaned_dataset_version_id='dataset-1',
        source_forecast_version_id='forecast-1',
        source_weekly_forecast_version_id=None,
        evaluation_window_start=datetime(2026, 3, 20, 0, tzinfo=UTC),
        evaluation_window_end=datetime(2026, 3, 20, 3, tzinfo=UTC),
        forecast_product_name='daily_1_day',
    )
    repo = SimpleNamespace(
        require_run=lambda _run_id: failing_run,
        finalize_failed=lambda _run_id, **kwargs: SimpleNamespace(result_type=kwargs['result_type']),
    )
    service = EvaluationService(repo, SimpleNamespace(), SimpleNamespace(), SimpleNamespace(), SimpleNamespace(evaluation_baseline_methods='seasonal_naive,moving_average'))
    service.scope_service = SimpleNamespace(
        resolve_scope_from_run=lambda _run: running_scope,
        list_engine_rows=lambda _scope: [{'bucket_start': datetime(2026, 3, 20, 0, tzinfo=UTC), 'bucket_end': datetime(2026, 3, 20, 1, tzinfo=UTC), 'service_category': 'Roads', 'time_period_key': 't', 'forecast_engine': 1.0}],
        list_actual_rows=lambda _scope: {'x': 1.0},
        build_aligned_rows=lambda _scope, _engine, _actual: [{'bucket_start': datetime(2026, 3, 20, 0, tzinfo=UTC), 'bucket_end': datetime(2026, 3, 20, 1, tzinfo=UTC), 'service_category': 'Roads', 'time_period_key': 't', 'forecast_engine': 1.0, 'actual': 1.0}],
    )
    service.baseline_service = SimpleNamespace(generate_baselines=lambda *_args, **_kwargs: (_ for _ in ()).throw(Exception('unexpected')))
    with pytest.raises(Exception, match='unexpected'):
        service.execute_run('run-2')

    missing_repo = SimpleNamespace(get_run=lambda _run_id: None)
    status_service = EvaluationService(missing_repo, SimpleNamespace(), SimpleNamespace(), SimpleNamespace(), SimpleNamespace(evaluation_baseline_methods='x'))
    with pytest.raises(HTTPException) as missing_status:
        status_service.get_run_status('missing')
    assert missing_status.value.status_code == 404

    current_repo = SimpleNamespace(
        get_current_marker=lambda _product: SimpleNamespace(evaluation_result_id='result-1', updated_by_run_id='run-1', updated_at=datetime(2026, 3, 20, tzinfo=UTC)),
        get_result_bundle=lambda _result_id: None,
    )
    current_service = EvaluationService(current_repo, SimpleNamespace(), SimpleNamespace(), SimpleNamespace(), SimpleNamespace(evaluation_baseline_methods='x'))
    with pytest.raises(HTTPException) as missing_current:
        current_service.get_current_evaluation('daily_1_day')
    assert missing_current.value.status_code == 404

    assert service._build_comparison_summary([
        {'segment_type': 'overall', 'method_metrics': [
            {'compared_method': 'forecast_engine', 'metrics': [{'metric_value': 1.0}]},
            {'compared_method': 'seasonal_naive', 'metrics': [{'metric_value': 2.0}]},
            {'compared_method': 'moving_average', 'metrics': [{'metric_value': 3.0}]},
        ]}
    ]) == 'The forecasting engine outperformed the included baselines for the evaluated scope.'
    assert service._build_comparison_summary([
        {'segment_type': 'overall', 'method_metrics': [
            {'compared_method': 'forecast_engine', 'metrics': [{'metric_value': 2.0}]},
            {'compared_method': 'seasonal_naive', 'metrics': [{'metric_value': 2.0}]},
            {'compared_method': 'moving_average', 'metrics': [{'metric_value': 3.0}]},
        ]}
    ]) == 'The forecasting engine matched the strongest included baseline for the evaluated scope.'


@pytest.mark.unit
def test_main_lifespan_registers_evaluation_scheduler(monkeypatch: pytest.MonkeyPatch) -> None:
    registered: list[tuple[str, object, str]] = []
    state = {'started': False, 'shutdown': False}

    class StubSchedulerService:
        def register_cron_job(self, name, job, cron):
            registered.append((name, job, cron))

        def start(self):
            state['started'] = True

        def shutdown(self):
            state['shutdown'] = True

    monkeypatch.setattr(main_module, 'SchedulerService', StubSchedulerService)
    monkeypatch.setattr(
        main_module,
        'get_settings',
        lambda: SimpleNamespace(
            scheduler_enabled=False,
            forecast_model_scheduler_enabled=False,
            forecast_scheduler_enabled=False,
            weekly_forecast_scheduler_enabled=False,
            weekly_forecast_model_scheduler_enabled=False,
            weekly_forecast_daily_regeneration_enabled=False,
            evaluation_scheduler_enabled=True,
            evaluation_scheduler_cron='15 3 * * *',
        ),
    )
    monkeypatch.setattr(main_module, 'build_evaluation_job', lambda session_factory: 'evaluation-job')

    app = SimpleNamespace(state=SimpleNamespace(session_factory=lambda: object()))

    async def run_lifespan():
        async with main_module.lifespan(app):
            assert state['started'] is True

    asyncio.run(run_lifespan())

    assert registered == [('forecast_evaluation', 'evaluation-job', '15 3 * * *')]
    assert state['shutdown'] is True


@pytest.mark.unit
def test_main_helper_and_bootstrap_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    assert main_module._expand_local_frontend_origins('http://localhost:5173') == ['http://127.0.0.1:5173', 'http://localhost:5173']
    assert main_module._expand_local_frontend_origins('http://127.0.0.1:4173') == ['http://127.0.0.1:4173', 'http://localhost:4173']
    assert main_module._expand_local_frontend_origins('https://example.com') == ['https://example.com']
    assert main_module._parse_allowlist('Planner@Example.com:CityPlanner|OperationalManager,bad-entry,missingroles:, :none') == [
        ('planner@example.com', ['CityPlanner', 'OperationalManager'])
    ]

    called = {'session_factory': False, 'closed': False, 'entries': None}

    class StubSession:
        def close(self):
            called['closed'] = True

    monkeypatch.setattr(main_module, 'get_settings', lambda: SimpleNamespace(auth_signup_allowlist=''))
    monkeypatch.setattr(main_module, 'get_session_factory', lambda: (_ for _ in ()).throw(AssertionError('should not create session')))
    main_module.bootstrap_auth_allowlist()

    monkeypatch.setattr(main_module, 'get_settings', lambda: SimpleNamespace(auth_signup_allowlist='Planner@Example.com:CityPlanner|OperationalManager'))
    monkeypatch.setattr(main_module, 'get_session_factory', lambda: (called.__setitem__('session_factory', True) or (lambda: StubSession())))
    monkeypatch.setattr(main_module, 'AuthRepository', lambda session: session)

    class StubBootstrapService:
        def __init__(self, _repository):
            pass

        def sync_allowlist(self, entries):
            called['entries'] = entries

    monkeypatch.setattr(main_module, 'AuthBootstrapService', StubBootstrapService)
    main_module.bootstrap_auth_allowlist()
    assert called['session_factory'] is True
    assert called['closed'] is True
    assert called['entries'] == [('planner@example.com', ['CityPlanner', 'OperationalManager'])]


@pytest.mark.unit
def test_main_lifespan_registers_all_scheduler_jobs_and_skips_start_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    registered: list[tuple[str, object, str]] = []
    state = {'started': False, 'shutdown': False}

    class StubSchedulerService:
        def register_cron_job(self, name, job, cron):
            registered.append((name, job, cron))

        def start(self):
            state['started'] = True

        def shutdown(self):
            state['shutdown'] = True

    monkeypatch.setattr(main_module, 'SchedulerService', StubSchedulerService)
    monkeypatch.setattr(main_module, 'build_ingestion_job', lambda session_factory: 'ingestion-job')
    monkeypatch.setattr(main_module, 'build_forecast_training_job', lambda session_factory: 'forecast-training-job')
    monkeypatch.setattr(main_module, 'build_forecast_job', lambda session_factory: 'forecast-job')
    monkeypatch.setattr(main_module, 'build_weekly_forecast_training_job', lambda session_factory: 'weekly-training-job')
    monkeypatch.setattr(main_module, 'build_weekly_forecast_job', lambda session_factory: 'weekly-job')
    monkeypatch.setattr(main_module, 'build_weekly_regeneration_job', lambda session_factory: 'weekly-regeneration-job')
    monkeypatch.setattr(main_module, 'build_evaluation_job', lambda session_factory: 'evaluation-job')
    monkeypatch.setattr(
        main_module,
        'get_settings',
        lambda: SimpleNamespace(
            scheduler_enabled=True,
            scheduler_cron='1 0 * * *',
            forecast_model_scheduler_enabled=True,
            forecast_model_scheduler_cron='2 0 * * *',
            forecast_scheduler_enabled=True,
            forecast_scheduler_cron='3 0 * * *',
            weekly_forecast_model_scheduler_enabled=True,
            weekly_forecast_model_scheduler_cron='4 0 * * *',
            weekly_forecast_scheduler_enabled=True,
            weekly_forecast_scheduler_cron='5 0 * * *',
            weekly_forecast_daily_regeneration_enabled=True,
            weekly_forecast_daily_regeneration_cron='6 0 * * *',
            evaluation_scheduler_enabled=True,
            evaluation_scheduler_cron='7 0 * * *',
        ),
    )

    app = SimpleNamespace(state=SimpleNamespace(session_factory=lambda: object()))

    async def run_lifespan():
        async with main_module.lifespan(app):
            assert state['started'] is True

    asyncio.run(run_lifespan())
    assert registered == [
        ('edmonton_311_ingestion', 'ingestion-job', '1 0 * * *'),
        ('daily_demand_forecast_model_training', 'forecast-training-job', '2 0 * * *'),
        ('daily_demand_forecast', 'forecast-job', '3 0 * * *'),
        ('weekly_demand_forecast_model_training', 'weekly-training-job', '4 0 * * *'),
        ('weekly_demand_forecast', 'weekly-job', '5 0 * * *'),
        ('weekly_demand_forecast_daily_regeneration', 'weekly-regeneration-job', '6 0 * * *'),
        ('forecast_evaluation', 'evaluation-job', '7 0 * * *'),
    ]
    assert state['shutdown'] is True

    registered.clear()
    state['started'] = False
    state['shutdown'] = False
    monkeypatch.setattr(
        main_module,
        'get_settings',
        lambda: SimpleNamespace(
            scheduler_enabled=False,
            forecast_model_scheduler_enabled=False,
            forecast_scheduler_enabled=False,
            weekly_forecast_model_scheduler_enabled=False,
            weekly_forecast_scheduler_enabled=False,
            weekly_forecast_daily_regeneration_enabled=False,
            evaluation_scheduler_enabled=False,
        ),
    )

    async def run_disabled_lifespan():
        async with main_module.lifespan(app):
            assert state['started'] is False

    asyncio.run(run_disabled_lifespan())
    assert registered == []
    assert state['shutdown'] is True


@pytest.mark.unit
def test_baseline_service_plural_and_default_missing_history_errors() -> None:
    settings = SimpleNamespace(source_name='edmonton_311')

    plural_service = BaselineService(
        SimpleNamespace(
            list_current_cleaned_records=lambda _source_name, **_kwargs: [
                {'category': 'Roads', 'requested_at': '2026-03-10T00:00:00Z'},
            ]
        ),
        settings,
    )
    with pytest.raises(BaselineGenerationError, match='No historical baseline series available for scopes Waste, Graffiti'):
        plural_service.generate_baselines(
            'daily_1_day',
            [
                {
                    'bucket_start': datetime(2026, 3, 20, 0, tzinfo=UTC),
                    'bucket_end': datetime(2026, 3, 20, 1, tzinfo=UTC),
                    'service_category': 'Waste',
                    'geography_key': None,
                    'forecast_engine': 1.0,
                    'actual': 1.0,
                },
                {
                    'bucket_start': datetime(2026, 3, 20, 1, tzinfo=UTC),
                    'bucket_end': datetime(2026, 3, 20, 2, tzinfo=UTC),
                    'service_category': 'Graffiti',
                    'geography_key': None,
                    'forecast_engine': 1.0,
                    'actual': 1.0,
                },
            ],
        )

    empty_history_service = BaselineService(
        SimpleNamespace(list_current_cleaned_records=lambda _source_name, **_kwargs: []),
        settings,
    )
    with pytest.raises(BaselineGenerationError, match='No historical actuals are available for baseline generation'):
        empty_history_service.generate_baselines(
            'daily_1_day',
            [
                {
                    'bucket_start': datetime(2026, 3, 20, 0, tzinfo=UTC),
                    'bucket_end': datetime(2026, 3, 20, 1, tzinfo=UTC),
                    'service_category': 'Waste',
                    'geography_key': None,
                    'forecast_engine': 1.0,
                    'actual': 1.0,
                }
            ],
        )


@pytest.mark.unit
def test_baseline_service_raises_default_error_when_history_cannot_be_aggregated() -> None:
    settings = SimpleNamespace(source_name='edmonton_311')
    service = BaselineService(
        SimpleNamespace(
            list_current_cleaned_records=lambda _source_name, **_kwargs: [
                {'category': 'Waste'},
            ]
        ),
        settings,
    )

    with pytest.raises(BaselineGenerationError, match='No historical baseline series available for the evaluated scope'):
        service.generate_baselines(
            'daily_1_day',
            [
                {
                    'bucket_start': datetime(2026, 3, 20, 0, tzinfo=UTC),
                    'bucket_end': datetime(2026, 3, 20, 1, tzinfo=UTC),
                    'service_category': 'Waste',
                    'geography_key': None,
                    'forecast_engine': 1.0,
                    'actual': 1.0,
                }
            ],
        )


@pytest.mark.unit
def test_evaluation_scope_service_category_only_guard_branches() -> None:
    service = EvaluationScopeService(
        cleaned_dataset_repository=SimpleNamespace(),
        forecast_repository=SimpleNamespace(),
        weekly_forecast_repository=SimpleNamespace(),
        settings=SimpleNamespace(),
    )

    assert service._uses_category_only_geography(
        EvaluationScope(
            forecast_product_name='daily_1_day',
            source_cleaned_dataset_version_id='dataset-1',
            source_forecast_version_id=None,
            source_weekly_forecast_version_id=None,
            evaluation_window_start=datetime(2026, 3, 20, 0, tzinfo=UTC),
            evaluation_window_end=datetime(2026, 3, 20, 1, tzinfo=UTC),
        )
    ) is False

    service.forecast_repository = SimpleNamespace(get_forecast_version='not-callable')
    assert service._uses_category_only_geography(
        EvaluationScope(
            forecast_product_name='daily_1_day',
            source_cleaned_dataset_version_id='dataset-1',
            source_forecast_version_id='forecast-1',
            source_weekly_forecast_version_id=None,
            evaluation_window_start=datetime(2026, 3, 20, 0, tzinfo=UTC),
            evaluation_window_end=datetime(2026, 3, 20, 1, tzinfo=UTC),
        )
    ) is False

    assert service._uses_category_only_geography(
        EvaluationScope(
            forecast_product_name='weekly_7_day',
            source_cleaned_dataset_version_id='dataset-1',
            source_forecast_version_id=None,
            source_weekly_forecast_version_id=None,
            evaluation_window_start=datetime(2026, 3, 20, 0, tzinfo=UTC),
            evaluation_window_end=datetime(2026, 3, 27, 0, tzinfo=UTC),
        )
    ) is False


@pytest.mark.unit
def test_evaluation_segments_marks_excluded_categories_with_and_without_rows() -> None:
    rows = [
        {
            'service_category': 'Roads',
            'time_period_key': '2026-03-20T00:00:00Z',
            'forecast_engine': 2.0,
            'seasonal_naive': 1.0,
            'moving_average': 1.5,
            'actual': 2.0,
        }
    ]

    segments, status = build_evaluation_segments(rows, excluded_scopes=['Roads', 'Waste'])

    assert status == 'partial'
    roads = next(segment for segment in segments if segment['segment_type'] == 'service_category' and segment['segment_key'] == 'Roads')
    waste = next(segment for segment in segments if segment['segment_type'] == 'service_category' and segment['segment_key'] == 'Waste')
    assert roads['segment_status'] == 'partial'
    assert roads['notes'] == 'This category was partially evaluated because some comparison rows had no baseline history.'
    assert waste['segment_status'] == 'partial'
    assert waste['comparison_row_count'] == 0
