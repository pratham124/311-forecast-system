from __future__ import annotations

from dataclasses import dataclass

from app.repositories.weekly_forecast_repository import WeeklyForecastRepository


class WeeklyForecastStorageError(RuntimeError):
    pass


@dataclass
class WeeklyForecastActivationService:
    repository: WeeklyForecastRepository

    def store_and_activate(
        self,
        *,
        forecast_product_name: str,
        weekly_forecast_run_id: str,
        source_cleaned_dataset_version_id: str,
        week_start_local,
        week_end_local,
        geography_scope: str,
        baseline_method: str,
        summary: str,
        buckets: list[dict[str, object]],
    ) -> str:
        if not buckets:
            raise WeeklyForecastStorageError("No weekly forecast buckets were produced")
        version = self.repository.create_forecast_version(
            weekly_forecast_run_id=weekly_forecast_run_id,
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            week_start_local=week_start_local,
            week_end_local=week_end_local,
            geography_scope=geography_scope,
            baseline_method=baseline_method,
            summary=summary,
        )
        self.repository.store_buckets(version.weekly_forecast_version_id, buckets)
        self.repository.mark_version_stored(version.weekly_forecast_version_id)
        self.repository.activate_forecast(
            forecast_product_name=forecast_product_name,
            weekly_forecast_version_id=version.weekly_forecast_version_id,
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            week_start_local=week_start_local,
            week_end_local=week_end_local,
            updated_by_run_id=weekly_forecast_run_id,
            geography_scope=geography_scope,
        )
        return version.weekly_forecast_version_id
