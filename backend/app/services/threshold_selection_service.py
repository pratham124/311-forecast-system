from __future__ import annotations

from app.models.threshold_alert_models import ThresholdConfiguration
from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository


class ThresholdSelectionService:
    def __init__(self, repository: ThresholdConfigurationRepository) -> None:
        self.repository = repository

    def resolve(
        self,
        *,
        service_category: str,
        geography_value: str | None,
        forecast_window_type: str,
    ) -> ThresholdConfiguration | None:
        return self.repository.find_active_threshold(
            service_category=service_category,
            geography_value=geography_value,
            forecast_window_type=forecast_window_type,
            create_default_if_missing=True,
        )
