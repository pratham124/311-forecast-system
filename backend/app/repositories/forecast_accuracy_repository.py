from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import (
    ForecastAccuracyAlignedBucket,
    ForecastAccuracyComparisonResult,
    ForecastAccuracyMetricResolution,
    ForecastAccuracyRenderEvent,
    ForecastAccuracyRequest,
)


class ForecastAccuracyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_request(self, **kwargs) -> ForecastAccuracyRequest:
        record = ForecastAccuracyRequest(**kwargs)
        self.session.add(record)
        self.session.flush()
        return record

    def finalize_request(
        self,
        forecast_accuracy_request_id: str,
        *,
        status: str,
        source_forecast_version_id: str | None = None,
        source_evaluation_result_id: str | None = None,
        failure_reason: str | None = None,
        render_reported: bool = False,
    ) -> ForecastAccuracyRequest:
        record = self.require_request(forecast_accuracy_request_id)
        record.status = status
        record.failure_reason = failure_reason
        record.completed_at = datetime.utcnow()
        if source_forecast_version_id is not None:
            record.source_forecast_version_id = source_forecast_version_id
        if source_evaluation_result_id is not None:
            record.source_evaluation_result_id = source_evaluation_result_id
        if render_reported:
            record.render_reported_at = datetime.utcnow()
        self.session.flush()
        return record

    def upsert_metric_resolution(
        self,
        *,
        forecast_accuracy_request_id: str,
        resolution_status: str,
        metric_names: list[str],
        metric_values: dict[str, float] | None,
        source_evaluation_result_id: str | None = None,
        status_message: str | None = None,
    ) -> ForecastAccuracyMetricResolution:
        record = self.session.scalar(
            select(ForecastAccuracyMetricResolution).where(
                ForecastAccuracyMetricResolution.forecast_accuracy_request_id == forecast_accuracy_request_id
            )
        )
        payload_json = json.dumps(metric_values) if metric_values is not None else None
        metric_names_json = json.dumps(metric_names)
        if record is None:
            record = ForecastAccuracyMetricResolution(
                forecast_accuracy_request_id=forecast_accuracy_request_id,
                source_evaluation_result_id=source_evaluation_result_id,
                resolution_status=resolution_status,
                metric_names_json=metric_names_json,
                metric_values_json=payload_json,
                status_message=status_message,
            )
            self.session.add(record)
        else:
            record.source_evaluation_result_id = source_evaluation_result_id
            record.resolution_status = resolution_status
            record.metric_names_json = metric_names_json
            record.metric_values_json = payload_json
            record.status_message = status_message
            record.resolved_at = datetime.utcnow()
        self.session.flush()
        return record

    def create_result(
        self,
        *,
        forecast_accuracy_request_id: str,
        view_status: str,
        metric_resolution_status: str | None,
        status_message: str | None,
        aligned_bucket_count: int,
        excluded_bucket_count: int,
    ) -> ForecastAccuracyComparisonResult:
        result = ForecastAccuracyComparisonResult(
            forecast_accuracy_request_id=forecast_accuracy_request_id,
            view_status=view_status,
            metric_resolution_status=metric_resolution_status,
            status_message=status_message,
            aligned_bucket_count=aligned_bucket_count,
            excluded_bucket_count=excluded_bucket_count,
        )
        self.session.add(result)
        self.session.flush()
        return result

    def replace_aligned_buckets(self, forecast_accuracy_result_id: str, buckets: list[dict[str, object]]) -> None:
        self.session.execute(
            delete(ForecastAccuracyAlignedBucket).where(
                ForecastAccuracyAlignedBucket.forecast_accuracy_result_id == forecast_accuracy_result_id
            )
        )
        for bucket in buckets:
            self.session.add(
                ForecastAccuracyAlignedBucket(
                    forecast_accuracy_result_id=forecast_accuracy_result_id,
                    bucket_start=bucket["bucket_start"],
                    bucket_end=bucket["bucket_end"],
                    service_category=bucket.get("service_category"),
                    forecast_value=float(bucket["forecast_value"]),
                    actual_value=float(bucket["actual_value"]),
                    absolute_error_value=float(bucket["absolute_error_value"]),
                    percentage_error_value=bucket.get("percentage_error_value"),
                )
            )
        self.session.flush()

    def create_render_event(
        self,
        *,
        forecast_accuracy_request_id: str,
        forecast_accuracy_result_id: str,
        render_outcome: str,
        failure_reason: str | None,
        reported_by_subject: str,
    ) -> ForecastAccuracyRenderEvent:
        event = ForecastAccuracyRenderEvent(
            forecast_accuracy_request_id=forecast_accuracy_request_id,
            forecast_accuracy_result_id=forecast_accuracy_result_id,
            render_outcome=render_outcome,
            failure_reason=failure_reason,
            reported_by_subject=reported_by_subject,
        )
        self.session.add(event)
        self.session.flush()
        return event

    def get_result_by_request(self, forecast_accuracy_request_id: str) -> ForecastAccuracyComparisonResult | None:
        return self.session.scalar(
            select(ForecastAccuracyComparisonResult).where(
                ForecastAccuracyComparisonResult.forecast_accuracy_request_id == forecast_accuracy_request_id
            )
        )

    def list_aligned_buckets(self, forecast_accuracy_result_id: str) -> list[ForecastAccuracyAlignedBucket]:
        return list(
            self.session.scalars(
                select(ForecastAccuracyAlignedBucket)
                .where(ForecastAccuracyAlignedBucket.forecast_accuracy_result_id == forecast_accuracy_result_id)
                .order_by(ForecastAccuracyAlignedBucket.bucket_start.asc())
            )
        )

    def get_metric_resolution(self, forecast_accuracy_request_id: str) -> ForecastAccuracyMetricResolution | None:
        return self.session.scalar(
            select(ForecastAccuracyMetricResolution).where(
                ForecastAccuracyMetricResolution.forecast_accuracy_request_id == forecast_accuracy_request_id
            )
        )

    def require_request(self, forecast_accuracy_request_id: str) -> ForecastAccuracyRequest:
        record = self.session.get(ForecastAccuracyRequest, forecast_accuracy_request_id)
        if record is None:
            raise LookupError("Forecast accuracy request not found")
        return record
