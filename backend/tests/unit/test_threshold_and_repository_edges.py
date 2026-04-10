from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.models import ThresholdConfiguration
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.notification_event_repository import NotificationEventRepository
from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository
from app.repositories.threshold_evaluation_repository import ThresholdEvaluationRepository
from app.repositories.threshold_state_repository import ThresholdStateRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository


def _seed_threshold_scope(session):
    configuration = ThresholdConfigurationRepository(session).create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=8,
        notification_channels=["email"],
        operational_manager_id="manager-1",
    )
    run = ThresholdEvaluationRepository(session).create_run(
        forecast_version_reference="forecast-1",
        forecast_product="daily",
        trigger_source="manual_replay",
    )
    session.commit()
    return configuration, run


@pytest.mark.unit
def test_forecast_repository_current_service_categories_returns_empty_for_missing_or_non_stored(session) -> None:
    repository = ForecastRepository(session)

    assert repository.list_current_service_categories("daily-product") == []

    version = repository.create_forecast_version(
        forecast_run_id="run-1",
        source_cleaned_dataset_version_id="dataset-1",
        horizon_start=datetime(2026, 3, 20, tzinfo=timezone.utc),
        horizon_end=datetime(2026, 3, 21, tzinfo=timezone.utc),
        geography_scope="citywide",
        baseline_method="lgbm",
        summary="pending",
    )
    repository.activate_forecast(
        forecast_product_name="daily-product",
        forecast_version_id=version.forecast_version_id,
        source_cleaned_dataset_version_id="dataset-1",
        horizon_start=version.horizon_start,
        horizon_end=version.horizon_end,
        updated_by_run_id="run-1",
        geography_scope="citywide",
    )
    session.commit()

    assert repository.list_current_service_categories("daily-product") == []


@pytest.mark.unit
def test_weekly_forecast_repository_current_service_categories_returns_empty_for_missing_or_non_stored(session) -> None:
    repository = WeeklyForecastRepository(session)

    assert repository.list_current_service_categories("weekly-product") == []

    version = repository.create_forecast_version(
        weekly_forecast_run_id="weekly-run-1",
        source_cleaned_dataset_version_id="dataset-1",
        week_start_local=datetime(2026, 3, 23, tzinfo=timezone.utc),
        week_end_local=datetime(2026, 3, 29, 23, 59, 59, tzinfo=timezone.utc),
        geography_scope="citywide",
        baseline_method="lgbm",
        summary="pending",
    )
    repository.activate_forecast(
        forecast_product_name="weekly-product",
        weekly_forecast_version_id=version.weekly_forecast_version_id,
        source_cleaned_dataset_version_id="dataset-1",
        week_start_local=version.week_start_local,
        week_end_local=version.week_end_local,
        updated_by_run_id="weekly-run-1",
        geography_scope="citywide",
    )
    session.commit()

    assert repository.list_current_service_categories("weekly-product") == []

    repository.store_buckets(
        version.weekly_forecast_version_id,
        [
            {
                "forecast_date_local": datetime(2026, 3, 23, tzinfo=timezone.utc).date(),
                "service_category": "Roads",
                "geography_key": None,
                "point_forecast": 10,
                "quantile_p10": 8,
                "quantile_p50": 10,
                "quantile_p90": 12,
                "baseline_value": 9,
            }
        ],
    )
    repository.mark_version_stored(version.weekly_forecast_version_id)
    session.commit()

    assert repository.list_service_categories(version.weekly_forecast_version_id) == ["Roads"]
    assert repository.list_current_service_categories("weekly-product") == ["Roads"]


@pytest.mark.unit
def test_notification_event_repository_filters_and_missing_bundle(session) -> None:
    configuration, run = _seed_threshold_scope(session)
    repository = NotificationEventRepository(session)
    now = datetime(2026, 3, 20, tzinfo=timezone.utc)

    event = repository.create_event(
        threshold_evaluation_run_id=run.threshold_evaluation_run_id,
        threshold_configuration_id=configuration.threshold_configuration_id,
        service_category="Roads",
        geography_type="ward",
        geography_value="Ward 1",
        forecast_window_start=now,
        forecast_window_end=now + timedelta(hours=1),
        forecast_window_type="hourly",
        forecast_value=12,
        threshold_value=8,
        overall_delivery_status="manual_review_required",
        follow_up_reason="Needs review",
    )
    repository.add_attempt(
        notification_event_id=event.notification_event_id,
        channel_type="email",
        attempt_number=1,
        attempted_at=now,
        status="failed",
        failure_reason="gateway timeout",
    )
    session.commit()

    filtered = repository.list_events(
        service_category="Roads",
        geography_value="Ward 1",
        overall_delivery_status="manual_review_required",
        forecast_window_type="hourly",
    )
    assert [item.notification_event_id for item in filtered] == [event.notification_event_id]
    assert repository.get_event_bundle("missing") is None


@pytest.mark.unit
def test_threshold_configuration_repository_edges(session) -> None:
    repository = ThresholdConfigurationRepository(session)
    now = datetime(2026, 3, 20, tzinfo=timezone.utc)

    active = repository.create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=8,
        notification_channels=["email"],
        operational_manager_id="manager-1",
        effective_from=now - timedelta(hours=2),
    )
    skipped_geography = repository.create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=9,
        notification_channels=["dashboard"],
        operational_manager_id="manager-1",
        effective_from=now - timedelta(hours=1),
    )
    skipped_geography.geography_value = "Ward 1"
    inactive = repository.create_configuration(
        service_category="Waste",
        forecast_window_type="daily",
        threshold_value=11,
        notification_channels=["dashboard"],
        operational_manager_id="manager-1",
        status="inactive",
        effective_from=now - timedelta(days=1),
        effective_to=now - timedelta(hours=1),
    )
    session.commit()

    assert repository.list_active_configurations()
    assert repository.get_configuration("missing") is None
    assert repository.get_configuration(active.threshold_configuration_id) is not None

    updated_inactive = repository.update_configuration(
        inactive.threshold_configuration_id,
        service_category="Waste",
        forecast_window_type="daily",
        threshold_value=22,
        notification_channels=["email", "dashboard"],
    )
    assert updated_inactive is not None
    assert updated_inactive.status == "inactive"
    assert repository.update_configuration(
        "missing",
        service_category="Waste",
        forecast_window_type="daily",
        threshold_value=1,
        notification_channels=["dashboard"],
    ) is None

    original_effective_to = updated_inactive.effective_to
    deactivated = repository.deactivate_configuration(inactive.threshold_configuration_id)
    assert deactivated is not None
    assert deactivated.effective_to == original_effective_to
    assert repository.deactivate_configuration("missing") is None

    selected = repository.find_active_threshold(
        service_category="Roads",
        forecast_window_type="hourly",
        at_time=now,
    )
    assert selected is not None
    assert selected.configuration.threshold_configuration_id == active.threshold_configuration_id


@pytest.mark.unit
def test_threshold_evaluation_repository_batch_state_and_finalize_edges(session) -> None:
    configuration, run = _seed_threshold_scope(session)
    repository = ThresholdEvaluationRepository(session)
    start = datetime(2026, 3, 20, tzinfo=timezone.utc)
    end = start + timedelta(hours=1)

    repository.record_scope_evaluations_batch([])
    repository.record_scope_evaluations_batch(
        [
            {
                "threshold_evaluation_run_id": run.threshold_evaluation_run_id,
                "threshold_configuration_id": configuration.threshold_configuration_id,
                "service_category": "Roads",
                "geography_type": None,
                "geography_value": None,
                "forecast_window_type": "hourly",
                "forecast_window_start": start,
                "forecast_window_end": end,
                "forecast_bucket_value": 12,
                "threshold_value": 8,
                "outcome": "alert_created",
                "notification_event_id": None,
            }
        ]
    )

    assert repository.get_state(
        service_category="Roads",
        geography_type=None,
        geography_value=None,
        forecast_window_type="hourly",
        forecast_window_start=start,
        forecast_window_end=end,
    ) is None

    created_state = repository.upsert_state(
        threshold_configuration_id=configuration.threshold_configuration_id,
        service_category="Roads",
        geography_type=None,
        geography_value=None,
        forecast_window_type="hourly",
        forecast_window_start=start,
        forecast_window_end=end,
        current_state="above_threshold_alerted",
        last_forecast_bucket_value=12,
        last_threshold_value=8,
        last_evaluated_at=end,
        last_notification_event_id=None,
    )
    updated_state = repository.upsert_state(
        threshold_configuration_id=configuration.threshold_configuration_id,
        service_category="Roads",
        geography_type=None,
        geography_value=None,
        forecast_window_type="hourly",
        forecast_window_start=start,
        forecast_window_end=end,
        current_state="below_or_equal",
        last_forecast_bucket_value=6,
        last_threshold_value=8,
        last_evaluated_at=end + timedelta(minutes=5),
        last_notification_event_id="event-1",
    )

    assert created_state.threshold_state_id == updated_state.threshold_state_id
    assert updated_state.current_state == "below_or_equal"

    finalized = repository.finalize_run(
        run.threshold_evaluation_run_id,
        status="completed",
        evaluated_scope_count=1,
        alert_created_count=1,
        failure_summary="none",
    )
    assert finalized.status == "completed"

    with pytest.raises(ValueError, match="Threshold evaluation run not found"):
        repository.finalize_run(
            "missing",
            status="failed",
            evaluated_scope_count=0,
            alert_created_count=0,
        )


@pytest.mark.unit
def test_threshold_state_repository_list_all_states(session) -> None:
    repository = ThresholdStateRepository(session)
    start = datetime(2026, 3, 20, tzinfo=timezone.utc)
    end = start + timedelta(hours=1)

    repository.reconcile_state(
        threshold_configuration_id="config-a",
        service_category="Roads",
        geography_type=None,
        geography_value=None,
        forecast_window_type="hourly",
        forecast_window_start=start,
        forecast_window_end=end,
        current_state="above_threshold_alerted",
        last_forecast_bucket_value=9,
        last_threshold_value=8,
        last_evaluated_at=start,
        last_notification_event_id=None,
    )

    states = repository.list_all_states()
    assert len(states) == 1
