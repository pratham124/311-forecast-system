from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.clients.notification_service import NotificationDeliveryClient
from app.core.config import get_settings
from app.core.logging import summarize_surge_alert_event, summarize_surge_alert_failure, summarize_surge_alert_success
from app.pipelines.surge_alert_evaluation_pipeline import SurgeAlertEvaluationPipeline
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.run_repository import RunRepository
from app.repositories.surge_configuration_repository import SurgeConfigurationRepository
from app.repositories.surge_evaluation_repository import SurgeEvaluationRepository
from app.repositories.surge_notification_event_repository import SurgeNotificationEventRepository
from app.repositories.surge_state_repository import SurgeStateRepository
from app.services.notification_delivery_service import NotificationDeliveryService
from app.services.surge_confirmation_service import SurgeConfirmationService
from app.services.surge_detection_service import SurgeDetectionService
from app.services.surge_notification_delivery_service import SurgeNotificationDeliveryService
from app.services.surge_scope_service import SurgeScopeService
from app.services.surge_state_service import SurgeStateService


def run_surge_alert_evaluation(
    session: Session,
    *,
    ingestion_run_id: str,
    trigger_source: str,
):
    logger = logging.getLogger("surge_alerts.trigger")
    logger.info(
        "%s",
        summarize_surge_alert_event(
            "surge_alerts.trigger.started",
            ingestion_run_id=ingestion_run_id,
            trigger_source=trigger_source,
        ),
    )
    settings = get_settings()
    pipeline = SurgeAlertEvaluationPipeline(
        scope_service=SurgeScopeService(
            run_repository=RunRepository(session),
            dataset_repository=DatasetRepository(session),
            forecast_repository=ForecastRepository(session),
        ),
        configuration_repository=SurgeConfigurationRepository(session),
        evaluation_repository=SurgeEvaluationRepository(session),
        state_repository=SurgeStateRepository(session),
        event_repository=SurgeNotificationEventRepository(session),
        detection_service=SurgeDetectionService(CleanedDatasetRepository(session), settings.source_name),
        confirmation_service=SurgeConfirmationService(),
        state_service=SurgeStateService(),
        delivery_service=SurgeNotificationDeliveryService(NotificationDeliveryService(NotificationDeliveryClient())),
    )
    run = pipeline.run(ingestion_run_id=ingestion_run_id, trigger_source=trigger_source)
    logger.info(
        "%s",
        summarize_surge_alert_success(
            "surge_alerts.trigger.completed",
            ingestion_run_id=ingestion_run_id,
            surge_evaluation_run_id=run.surge_evaluation_run_id,
            trigger_source=trigger_source,
            status=run.status,
        ),
    )
    return run


def run_surge_alert_evaluation_for_forecast(
    session: Session,
    *,
    forecast_version_id: str,
    trigger_source: str = "ingestion_completion",
):
    logger = logging.getLogger("surge_alerts.trigger")
    forecast_repository = ForecastRepository(session)
    dataset_repository = DatasetRepository(session)
    forecast_version = forecast_repository.get_forecast_version(forecast_version_id)
    if forecast_version is None:
        logger.warning(
            "%s",
            summarize_surge_alert_failure(
                "surge_alerts.trigger.forecast_resolution_failed",
                forecast_version_id=forecast_version_id,
                trigger_source=trigger_source,
                failure_reason="Forecast version not found",
            ),
        )
        raise ValueError("Forecast version not found")
    if forecast_version.source_cleaned_dataset_version_id is None:
        logger.warning(
            "%s",
            summarize_surge_alert_failure(
                "surge_alerts.trigger.forecast_resolution_failed",
                forecast_version_id=forecast_version_id,
                trigger_source=trigger_source,
                failure_reason="Forecast version is not linked to an approved cleaned dataset",
            ),
        )
        raise ValueError("Forecast version is not linked to an approved cleaned dataset")
    dataset_version = dataset_repository.get_dataset_version(forecast_version.source_cleaned_dataset_version_id)
    if dataset_version is None:
        logger.warning(
            "%s",
            summarize_surge_alert_failure(
                "surge_alerts.trigger.forecast_resolution_failed",
                forecast_version_id=forecast_version_id,
                source_cleaned_dataset_version_id=forecast_version.source_cleaned_dataset_version_id,
                trigger_source=trigger_source,
                failure_reason="Approved cleaned dataset version could not be resolved",
            ),
        )
        raise ValueError("Approved cleaned dataset version could not be resolved")
    logger.info(
        "%s",
        summarize_surge_alert_event(
            "surge_alerts.trigger.forecast_resolved",
            forecast_version_id=forecast_version_id,
            source_cleaned_dataset_version_id=forecast_version.source_cleaned_dataset_version_id,
            resolved_ingestion_run_id=dataset_version.ingestion_run_id,
            trigger_source=trigger_source,
        ),
    )
    return run_surge_alert_evaluation(
        session,
        ingestion_run_id=dataset_version.ingestion_run_id,
        trigger_source=trigger_source,
    )
