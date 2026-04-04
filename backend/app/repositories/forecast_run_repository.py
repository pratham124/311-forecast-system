from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.clients.weather_client import get_weather_enrichment_source
from app.models import ForecastRun


class ForecastRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_run(
        self,
        *,
        trigger_type: str,
        source_cleaned_dataset_version_id: str | None,
        requested_horizon_start: datetime,
        requested_horizon_end: datetime,
    ) -> ForecastRun:
        run = ForecastRun(
            trigger_type=trigger_type,
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            requested_horizon_start=requested_horizon_start,
            requested_horizon_end=requested_horizon_end,
            status="running",
        )
        self.session.add(run)
        self.session.flush()
        return run

    def get_run(self, forecast_run_id: str) -> ForecastRun | None:
        return self.session.get(ForecastRun, forecast_run_id)

    def finalize_generated(
        self,
        forecast_run_id: str,
        *,
        forecast_version_id: str,
        geography_scope: str,
        summary: str,
    ) -> ForecastRun:
        run = self._require_run(forecast_run_id)
        run.status = "success"
        run.result_type = "generated_new"
        run.forecast_version_id = forecast_version_id
        run.geography_scope = geography_scope
        run.summary = summary
        run.weather_enrichment_source = get_weather_enrichment_source()
        run.holiday_enrichment_source = "nager_date_canada"
        run.completed_at = datetime.utcnow()
        self.session.flush()
        return run

    def finalize_reused(
        self,
        forecast_run_id: str,
        *,
        served_forecast_version_id: str,
        geography_scope: str,
        summary: str,
    ) -> ForecastRun:
        run = self._require_run(forecast_run_id)
        run.status = "success"
        run.result_type = "served_current"
        run.served_forecast_version_id = served_forecast_version_id
        run.geography_scope = geography_scope
        run.summary = summary
        run.completed_at = datetime.utcnow()
        self.session.flush()
        return run

    def finalize_failed(
        self,
        forecast_run_id: str,
        *,
        result_type: str,
        failure_reason: str,
        summary: str,
    ) -> ForecastRun:
        run = self._require_run(forecast_run_id)
        run.status = "failed"
        run.result_type = result_type
        run.failure_reason = failure_reason
        run.summary = summary
        run.completed_at = datetime.utcnow()
        self.session.flush()
        return run

    def _require_run(self, forecast_run_id: str) -> ForecastRun:
        run = self.get_run(forecast_run_id)
        if run is None:
            raise ValueError("Forecast run not found")
        return run
