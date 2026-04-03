from __future__ import annotations

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.schemas.demand_comparison_api import (
    DateConstraints,
    DemandComparisonAvailability,
)


class DemandComparisonAvailabilityService:
    def __init__(
        self,
        cleaned_dataset_repository: CleanedDatasetRepository,
        forecast_repository: ForecastRepository,
        weekly_forecast_repository: WeeklyForecastRepository,
        source_name: str,
        daily_forecast_product_name: str,
        weekly_forecast_product_name: str,
    ) -> None:
        self.cleaned_dataset_repository = cleaned_dataset_repository
        self.forecast_repository = forecast_repository
        self.weekly_forecast_repository = weekly_forecast_repository
        self.source_name = source_name
        self.daily_forecast_product_name = daily_forecast_product_name
        self.weekly_forecast_product_name = weekly_forecast_product_name

    def get_availability(self) -> DemandComparisonAvailability:
        return DemandComparisonAvailability(
            serviceCategories=self.cleaned_dataset_repository.list_current_categories(self.source_name),
            byCategoryGeography={},
            dateConstraints=DateConstraints(),
            presets=[],
            forecastProduct=None,
            summary="Initial comparison filters are sourced from the approved cleaned dataset lineage.",
        )
