from __future__ import annotations

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository


class DemandLineageRepository:
    def __init__(
        self,
        cleaned_dataset_repository: CleanedDatasetRepository,
        forecast_repository: ForecastRepository,
        weekly_forecast_repository: WeeklyForecastRepository,
    ) -> None:
        self.cleaned_dataset_repository = cleaned_dataset_repository
        self.forecast_repository = forecast_repository
        self.weekly_forecast_repository = weekly_forecast_repository

    def get_current_approved_dataset(self, source_name: str):
        return self.cleaned_dataset_repository.get_current_approved_dataset(source_name)

    def get_current_daily_forecast_marker(self, forecast_product_name: str):
        return self.forecast_repository.get_current_marker(forecast_product_name)

    def get_current_weekly_forecast_marker(self, forecast_product_name: str):
        return self.weekly_forecast_repository.get_current_marker(forecast_product_name)
