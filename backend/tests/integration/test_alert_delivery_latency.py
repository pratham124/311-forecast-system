"""T026 – Performance validation for the 5-minute successful delivery target (SC-002)."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

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


def test_single_alert_completes_within_five_minutes(session) -> None:
    """SC-002: alert evaluation and delivery finishes well within 5 minutes."""
    start = datetime(2026, 4, 1, 8, 0, tzinfo=timezone.utc)

    config_repo = ThresholdConfigurationRepository(session)
    config_repo.create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=10,
        operational_manager_id="mgr-1",
        notification_channels=["dashboard"],
    )
    session.commit()

    pipeline = ThresholdAlertEvaluationPipeline(
        forecast_scope_service=StubScopeService(
            [
                ForecastScope(
                    service_category="Roads",
                    geography_type=None,
                    geography_value=None,
                    forecast_window_type="hourly",
                    forecast_window_start=start,
                    forecast_window_end=start + timedelta(hours=1),
                    forecast_value=50,
                )
            ]
        ),
        threshold_configuration_repository=config_repo,
        threshold_evaluation_repository=ThresholdEvaluationRepository(session),
        threshold_state_repository=ThresholdStateRepository(session),
        notification_event_repository=NotificationEventRepository(session),
    )

    t0 = time.monotonic()
    pipeline.evaluate(
        forecast_reference_id="fv-perf-1",
        forecast_product="daily",
        trigger_source="manual_replay",
    )
    session.commit()
    elapsed = time.monotonic() - t0

    assert elapsed < 300, f"Alert pipeline took {elapsed:.2f}s, exceeding 5-minute target"

    events = NotificationEventRepository(session).list_events(service_category="Roads")
    assert len(events) == 1
    assert events[0].overall_delivery_status == "delivered"


def test_multi_scope_evaluation_within_five_minutes(session) -> None:
    """SC-002: evaluating 50 scopes still completes well within 5 minutes."""
    start = datetime(2026, 4, 1, 8, 0, tzinfo=timezone.utc)

    config_repo = ThresholdConfigurationRepository(session)
    config_repo.create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=10,
        operational_manager_id="mgr-1",
        notification_channels=["dashboard", "email"],
    )
    session.commit()

    scopes = [
        ForecastScope(
            service_category="Roads",
            geography_type="ward",
            geography_value=f"Ward {i}",
            forecast_window_type="hourly",
            forecast_window_start=start + timedelta(hours=i),
            forecast_window_end=start + timedelta(hours=i + 1),
            forecast_value=50 + i,
        )
        for i in range(50)
    ]

    pipeline = ThresholdAlertEvaluationPipeline(
        forecast_scope_service=StubScopeService(scopes),
        threshold_configuration_repository=config_repo,
        threshold_evaluation_repository=ThresholdEvaluationRepository(session),
        threshold_state_repository=ThresholdStateRepository(session),
        notification_event_repository=NotificationEventRepository(session),
    )

    t0 = time.monotonic()
    pipeline.evaluate(
        forecast_reference_id="fv-perf-bulk",
        forecast_product="daily",
        trigger_source="manual_replay",
    )
    session.commit()
    elapsed = time.monotonic() - t0

    assert elapsed < 300, f"Bulk evaluation took {elapsed:.2f}s, exceeding 5-minute target"

    events = NotificationEventRepository(session).list_events()
    assert len(events) == 50
