from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import WeeklyForecastRun


class WeeklyForecastRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_run(
        self,
        *,
        trigger_type: str,
        source_cleaned_dataset_version_id: str | None,
        week_start_local: datetime,
        week_end_local: datetime,
    ) -> WeeklyForecastRun:
        run = WeeklyForecastRun(
            trigger_type=trigger_type,
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            week_start_local=week_start_local,
            week_end_local=week_end_local,
            status="running",
        )
        self.session.add(run)
        self.session.flush()
        return run

    def get_run(self, weekly_forecast_run_id: str) -> WeeklyForecastRun | None:
        return self.session.get(WeeklyForecastRun, weekly_forecast_run_id)

    def find_in_progress_run(self, *, week_start_local: datetime, week_end_local: datetime) -> WeeklyForecastRun | None:
        statement = select(WeeklyForecastRun).where(
            WeeklyForecastRun.week_start_local == week_start_local,
            WeeklyForecastRun.week_end_local == week_end_local,
            WeeklyForecastRun.status == "running",
        )
        return self.session.scalar(statement)

    def finalize_generated(
        self,
        weekly_forecast_run_id: str,
        *,
        generated_forecast_version_id: str,
        geography_scope: str,
        summary: str,
    ) -> WeeklyForecastRun:
        run = self._require_run(weekly_forecast_run_id)
        run.status = "success"
        run.result_type = "generated_new"
        run.generated_forecast_version_id = generated_forecast_version_id
        run.geography_scope = geography_scope
        run.summary = summary
        run.completed_at = datetime.utcnow()
        self.session.flush()
        return run

    def finalize_reused(
        self,
        weekly_forecast_run_id: str,
        *,
        served_forecast_version_id: str,
        geography_scope: str,
        summary: str,
    ) -> WeeklyForecastRun:
        run = self._require_run(weekly_forecast_run_id)
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
        weekly_forecast_run_id: str,
        *,
        result_type: str,
        failure_reason: str,
        summary: str,
    ) -> WeeklyForecastRun:
        run = self._require_run(weekly_forecast_run_id)
        run.status = "failed"
        run.result_type = result_type
        run.failure_reason = failure_reason
        run.summary = summary
        run.completed_at = datetime.utcnow()
        self.session.flush()
        return run

    def _require_run(self, weekly_forecast_run_id: str) -> WeeklyForecastRun:
        run = self.get_run(weekly_forecast_run_id)
        if run is None:
            raise ValueError("Weekly forecast run not found")
        return run
