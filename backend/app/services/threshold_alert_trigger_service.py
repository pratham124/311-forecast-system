from __future__ import annotations

from sqlalchemy.orm import Session

from app.clients.notification_service import NotificationDeliveryClient
from app.pipelines.threshold_alert_evaluation_pipeline import ThresholdAlertEvaluationPipeline
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.notification_event_repository import NotificationEventRepository
from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository
from app.repositories.threshold_evaluation_repository import ThresholdEvaluationRepository
from app.repositories.threshold_state_repository import ThresholdStateRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.services.forecast_scope_service import ForecastScopeService
from app.services.notification_delivery_service import NotificationDeliveryService
from app.services.threshold_alert_service import ThresholdAlertService


def run_threshold_alert_evaluation(
    session: Session,
    *,
    forecast_reference_id: str,
    forecast_product: str,
    trigger_source: str,
) -> object:
    pipeline = ThresholdAlertEvaluationPipeline(
        scope_service=ForecastScopeService(
            forecast_repository=ForecastRepository(session),
            weekly_forecast_repository=WeeklyForecastRepository(session),
        ),
        configuration_repository=ThresholdConfigurationRepository(session),
        evaluation_repository=ThresholdEvaluationRepository(session),
        threshold_state_repository=ThresholdStateRepository(session),
        notification_repository=NotificationEventRepository(session),
        alert_service=ThresholdAlertService(),
        notification_delivery_service=NotificationDeliveryService(NotificationDeliveryClient()),
    )
    return pipeline.run(
        forecast_reference_id=forecast_reference_id,
        forecast_product=forecast_product,
        trigger_source=trigger_source,
    )

