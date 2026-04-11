from __future__ import annotations

from datetime import datetime

from app.models import AlertDetailLoadRecord


class AlertDetailRepository:
    def __init__(self, session) -> None:
        self.session = session

    def create_load(self, **kwargs) -> AlertDetailLoadRecord:
        record = AlertDetailLoadRecord(**kwargs)
        self.session.add(record)
        self.session.flush()
        return record

    def require_load(self, alert_detail_load_id: str) -> AlertDetailLoadRecord:
        record = self.session.get(AlertDetailLoadRecord, alert_detail_load_id)
        if record is None:
            raise LookupError("Alert detail load not found")
        return record

    def finalize_load(
        self,
        alert_detail_load_id: str,
        *,
        view_status: str,
        distribution_status: str,
        drivers_status: str,
        anomalies_status: str,
        preparation_status: str,
        failure_reason: str | None = None,
        source_forecast_version_id: str | None = None,
        source_weekly_forecast_version_id: str | None = None,
        source_threshold_evaluation_run_id: str | None = None,
        source_surge_evaluation_run_id: str | None = None,
        source_surge_candidate_id: str | None = None,
        correlation_id: str | None = None,
    ) -> AlertDetailLoadRecord:
        record = self.require_load(alert_detail_load_id)
        record.view_status = view_status
        record.distribution_status = distribution_status
        record.drivers_status = drivers_status
        record.anomalies_status = anomalies_status
        record.preparation_status = preparation_status
        record.failure_reason = failure_reason
        record.completed_at = datetime.utcnow()
        if source_forecast_version_id is not None:
            record.source_forecast_version_id = source_forecast_version_id
        if source_weekly_forecast_version_id is not None:
            record.source_weekly_forecast_version_id = source_weekly_forecast_version_id
        if source_threshold_evaluation_run_id is not None:
            record.source_threshold_evaluation_run_id = source_threshold_evaluation_run_id
        if source_surge_evaluation_run_id is not None:
            record.source_surge_evaluation_run_id = source_surge_evaluation_run_id
        if source_surge_candidate_id is not None:
            record.source_surge_candidate_id = source_surge_candidate_id
        if correlation_id is not None:
            record.correlation_id = correlation_id
        self.session.flush()
        return record

    def record_render_event(
        self,
        alert_detail_load_id: str,
        *,
        render_status: str,
        failure_reason: str | None = None,
    ) -> AlertDetailLoadRecord:
        record = self.require_load(alert_detail_load_id)
        if record.render_status == "render_failed":
            return record
        record.render_status = render_status
        record.render_failure_reason = failure_reason
        record.render_reported_at = datetime.utcnow()
        if render_status == "render_failed":
            record.view_status = "error"
            record.failure_reason = failure_reason or record.failure_reason
        self.session.flush()
        return record
