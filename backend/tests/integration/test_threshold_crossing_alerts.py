from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.pipelines.threshold_alert_evaluation_pipeline import ThresholdAlertEvaluationPipeline
from app.repositories.notification_event_repository import NotificationEventRepository
from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository
from app.repositories.threshold_evaluation_repository import ThresholdEvaluationRepository
from app.repositories.threshold_state_repository import ThresholdStateRepository
from app.services.forecast_scope_service import ForecastScope


class StubForecastScopeService:
    def __init__(self, scopes: list[ForecastScope]) -> None:
        self.scopes = scopes

    def list_scopes(self, *, forecast_product: str, forecast_reference_id: str) -> list[ForecastScope]:
        return self.scopes


def test_threshold_crossing_creates_notification_event(session) -> None:
    start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=1)

    config_repo = ThresholdConfigurationRepository(session)
    config = config_repo.create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=20,
        operational_manager_id="mgr-1",
        notification_channels=["email", "dashboard"],
    )
    session.commit()

    pipeline = ThresholdAlertEvaluationPipeline(
        forecast_scope_service=StubForecastScopeService(
            [
                ForecastScope(
                    service_category="Roads",
                    geography_type=None,
                    geography_value=None,
                    forecast_window_type="hourly",
                    forecast_window_start=start,
                    forecast_window_end=end,
                    forecast_value=42,
                )
            ]
        ),
        threshold_configuration_repository=config_repo,
        threshold_evaluation_repository=ThresholdEvaluationRepository(session),
        threshold_state_repository=ThresholdStateRepository(session),
        notification_event_repository=NotificationEventRepository(session),
    )

    run_id = pipeline.evaluate(
        forecast_reference_id="forecast-version-1",
        forecast_product="daily",
        trigger_source="manual_replay",
    )
    session.commit()

    events = NotificationEventRepository(session).list_events(service_category="Roads")
    runs = ThresholdEvaluationRepository(session).get_run(run_id)

    assert runs is not None
    assert runs.alert_created_count == 1
    assert len(events) == 1
    assert events[0].threshold_configuration_id == config.threshold_configuration_id
    assert float(events[0].forecast_value) == 42
    assert float(events[0].threshold_value) == 20
