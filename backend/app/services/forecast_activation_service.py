from __future__ import annotations

from dataclasses import dataclass

from app.repositories.forecast_repository import ForecastRepository


class ForecastStorageError(RuntimeError):
    pass


@dataclass
class ForecastActivationService:
    repository: ForecastRepository

    def store_and_activate(
        self,
        *,
        forecast_product_name: str,
        forecast_run_id: str,
        source_cleaned_dataset_version_id: str,
        horizon_start,
        horizon_end,
        geography_scope: str,
        baseline_method: str,
        summary: str,
        buckets: list[dict[str, object]],
    ) -> str:
        if len({bucket["bucket_start"] for bucket in buckets}) != 24:
            raise ForecastStorageError("Forecast must cover 24 hourly buckets")

        version = self.repository.create_forecast_version(
            forecast_run_id=forecast_run_id,
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            geography_scope=geography_scope,
            baseline_method=baseline_method,
            summary=summary,
        )
        self.repository.store_buckets(version.forecast_version_id, buckets)
        self.repository.mark_version_stored(version.forecast_version_id, 24)
        self.repository.activate_forecast(
            forecast_product_name=forecast_product_name,
            forecast_version_id=version.forecast_version_id,
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            updated_by_run_id=forecast_run_id,
            geography_scope=geography_scope,
        )
        return version.forecast_version_id
