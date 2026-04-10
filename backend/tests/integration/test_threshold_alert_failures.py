"""T024 – Integration tests for missing-threshold, suppressed-duplicate, and total-failure outcomes."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.clients.notification_service import NotificationAttemptResult, NotificationServiceClient
from app.pipelines.threshold_alert_evaluation_pipeline import ThresholdAlertEvaluationPipeline
from app.repositories.notification_event_repository import NotificationEventRepository
from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository
from app.repositories.threshold_evaluation_repository import ThresholdEvaluationRepository
from app.repositories.threshold_state_repository import ThresholdStateRepository
from app.services.forecast_scope_service import ForecastScope


class StubScopeService:
    def __init__(self, scopes: list[ForecastScope]) -> None:
        self.scopes = scopes

    def list_scopes(self, *, forecast_product: str, forecast_reference_id: str) -> list[ForecastScope]:
        return self.scopes


def _make_scope(
    *,
    category: str = "Roads",
    geo: str | None = None,
    value: float = 50,
) -> ForecastScope:
    start = datetime(2026, 4, 1, 8, 0, tzinfo=timezone.utc)
    return ForecastScope(
        service_category=category,
        geography_type="ward" if geo else None,
        geography_value=geo,
        forecast_window_type="hourly",
        forecast_window_start=start,
        forecast_window_end=start + timedelta(hours=1),
        forecast_value=value,
    )


def _build_pipeline(session, scopes):
    config_repo = ThresholdConfigurationRepository(session)
    return ThresholdAlertEvaluationPipeline(
        forecast_scope_service=StubScopeService(scopes),
        threshold_configuration_repository=config_repo,
        threshold_evaluation_repository=ThresholdEvaluationRepository(session),
        threshold_state_repository=ThresholdStateRepository(session),
        notification_event_repository=NotificationEventRepository(session),
    ), config_repo


# ── FR-008: missing threshold records configuration_missing ────────────────


def test_missing_threshold_records_configuration_gap(session) -> None:
    """FR-008: no threshold → record configuration_missing, no notification."""
    scope = _make_scope(value=999)
    pipeline, config_repo = _build_pipeline(session, [scope])

    # Do NOT set create_default_if_missing so that no auto-default is created.
    # Override the selection service to not auto-create defaults.
    pipeline.threshold_selection_service.repository = config_repo
    original_resolve = pipeline.threshold_selection_service.resolve

    def resolve_no_default(*, service_category, geography_value, forecast_window_type):
        result = config_repo.find_active_threshold(
            service_category=service_category,
            geography_value=geography_value,
            forecast_window_type=forecast_window_type,
            create_default_if_missing=False,
        )
        return result

    pipeline.threshold_selection_service.resolve = resolve_no_default

    run_id = pipeline.evaluate(
        forecast_reference_id="fv-1",
        forecast_product="daily",
        trigger_source="manual_replay",
    )
    session.commit()

    evals = ThresholdEvaluationRepository(session).list_scope_evaluations(run_id)
    assert len(evals) == 1
    assert evals[0].outcome == "configuration_missing"
    assert evals[0].notification_event_id is None

    events = NotificationEventRepository(session).list_events(service_category="Roads")
    assert len(events) == 0


# ── FR-013: suppressed duplicate when still above threshold ────────────────


def test_duplicate_suppressed_while_above_threshold(session) -> None:
    """FR-013: second evaluation above threshold is suppressed, no duplicate alert."""
    scope = _make_scope(value=150)
    pipeline, config_repo = _build_pipeline(session, [scope])
    config_repo.create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=100,
        operational_manager_id="mgr-1",
        notification_channels=["dashboard"],
    )
    session.commit()

    # First evaluation: should create alert
    pipeline.evaluate(
        forecast_reference_id="fv-1",
        forecast_product="daily",
        trigger_source="manual_replay",
    )
    session.commit()

    events_first = NotificationEventRepository(session).list_events(service_category="Roads")
    assert len(events_first) == 1

    # Second evaluation: same scope still above threshold → suppressed
    run_id_2 = pipeline.evaluate(
        forecast_reference_id="fv-2",
        forecast_product="daily",
        trigger_source="manual_replay",
    )
    session.commit()

    events_second = NotificationEventRepository(session).list_events(service_category="Roads")
    assert len(events_second) == 1  # no new event

    evals = ThresholdEvaluationRepository(session).list_scope_evaluations(run_id_2)
    assert any(e.outcome == "exceeded_suppressed" for e in evals)


# ── FR-013 continued: re-arm after returning below threshold ───────────────


def test_rearm_after_returning_below_threshold(session) -> None:
    """FR-013: after returning to/below threshold, a subsequent exceedance triggers a new alert."""
    scope_high = _make_scope(value=150)
    scope_low = _make_scope(value=80)

    pipeline_high, config_repo = _build_pipeline(session, [scope_high])
    config_repo.create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=100,
        operational_manager_id="mgr-1",
        notification_channels=["dashboard"],
    )
    session.commit()

    # First: above → alert
    pipeline_high.evaluate(
        forecast_reference_id="fv-1",
        forecast_product="daily",
        trigger_source="manual_replay",
    )
    session.commit()

    # Second: below → re-arm
    pipeline_low, _ = _build_pipeline(session, [scope_low])
    pipeline_low.evaluate(
        forecast_reference_id="fv-2",
        forecast_product="daily",
        trigger_source="manual_replay",
    )
    session.commit()

    # Third: above again → new alert
    pipeline_high2, _ = _build_pipeline(session, [scope_high])
    pipeline_high2.evaluate(
        forecast_reference_id="fv-3",
        forecast_product="daily",
        trigger_source="manual_replay",
    )
    session.commit()

    events = NotificationEventRepository(session).list_events(service_category="Roads")
    assert len(events) == 2  # two distinct alerts


# ── FR-010: total delivery failure → manual_review_required ────────────────


def test_total_delivery_failure_records_manual_review(session) -> None:
    """FR-010: when all channels fail, overall status is manual_review_required."""
    scope = _make_scope(value=200)
    pipeline, config_repo = _build_pipeline(session, [scope])
    config_repo.create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=100,
        operational_manager_id="mgr-1",
        notification_channels=["webhook"],  # unsupported → will fail
    )
    session.commit()

    pipeline.evaluate(
        forecast_reference_id="fv-1",
        forecast_product="daily",
        trigger_source="manual_replay",
    )
    session.commit()

    events = NotificationEventRepository(session).list_events(service_category="Roads")
    assert len(events) == 1
    assert events[0].overall_delivery_status == "manual_review_required"
    assert events[0].follow_up_reason is not None

    attempts = NotificationEventRepository(session).list_channel_attempts(events[0].notification_event_id)
    assert len(attempts) == 1
    assert attempts[0].status == "failed"
    assert attempts[0].failure_reason is not None


# ── FR-007c: partial delivery ──────────────────────────────────────────────


def test_partial_delivery_when_one_channel_fails(session) -> None:
    """FR-007c: at least one channel succeeds + at least one fails → partial_delivery."""
    scope = _make_scope(value=200)
    pipeline, config_repo = _build_pipeline(session, [scope])
    config_repo.create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=100,
        operational_manager_id="mgr-1",
        notification_channels=["dashboard", "webhook"],  # dashboard succeeds, webhook fails
    )
    session.commit()

    pipeline.evaluate(
        forecast_reference_id="fv-1",
        forecast_product="daily",
        trigger_source="manual_replay",
    )
    session.commit()

    events = NotificationEventRepository(session).list_events(service_category="Roads")
    assert len(events) == 1
    assert events[0].overall_delivery_status == "partial_delivery"

    attempts = NotificationEventRepository(session).list_channel_attempts(events[0].notification_event_id)
    assert len(attempts) == 2
    statuses = {a.channel_type: a.status for a in attempts}
    assert statuses["dashboard"] == "succeeded"
    assert statuses["webhook"] == "failed"


# ── FR-004 / FR-009: equal to threshold is NOT an exceedance ──────────────


def test_equal_to_threshold_does_not_trigger_alert(session) -> None:
    """FR-004/FR-009: forecast value == threshold → no alert."""
    scope = _make_scope(value=100)  # exactly equal
    pipeline, config_repo = _build_pipeline(session, [scope])
    config_repo.create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=100,
        operational_manager_id="mgr-1",
        notification_channels=["dashboard"],
    )
    session.commit()

    pipeline.evaluate(
        forecast_reference_id="fv-1",
        forecast_product="daily",
        trigger_source="manual_replay",
    )
    session.commit()

    events = NotificationEventRepository(session).list_events(service_category="Roads")
    assert len(events) == 0
