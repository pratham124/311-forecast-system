from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import (
    ComparisonMissingCombination,
    DemandComparisonOutcomeRecord,
    DemandComparisonRequest,
    DemandComparisonResult,
    DemandComparisonSeriesPoint,
)


class DemandComparisonRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_request(
        self,
        *,
        requested_by_actor: str,
        requested_by_subject: str,
        source_cleaned_dataset_version_id: str | None,
        source_forecast_version_id: str | None,
        source_weekly_forecast_version_id: str | None,
        forecast_product_name: str | None,
        forecast_granularity: str | None,
        geography_level: str | None,
        service_category_count: int,
        geography_value_count: int,
        time_range_start: datetime,
        time_range_end: datetime,
        warning_status: str,
        status: str = "running",
    ) -> DemandComparisonRequest:
        record = DemandComparisonRequest(
            requested_by_actor=requested_by_actor,
            requested_by_subject=requested_by_subject,
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            source_forecast_version_id=source_forecast_version_id,
            source_weekly_forecast_version_id=source_weekly_forecast_version_id,
            forecast_product_name=forecast_product_name,
            forecast_granularity=forecast_granularity,
            geography_level=geography_level,
            service_category_count=service_category_count,
            geography_value_count=geography_value_count,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            warning_status=warning_status,
            status=status,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def create_result(
        self,
        *,
        comparison_request_id: str,
        source_cleaned_dataset_version_id: str | None,
        source_forecast_version_id: str | None,
        source_weekly_forecast_version_id: str | None,
        forecast_product_name: str | None,
        forecast_granularity: str | None,
        result_mode: str,
        comparison_granularity: str,
        status: str,
    ) -> DemandComparisonResult:
        result = DemandComparisonResult(
            comparison_request_id=comparison_request_id,
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            source_forecast_version_id=source_forecast_version_id,
            source_weekly_forecast_version_id=source_weekly_forecast_version_id,
            forecast_product_name=forecast_product_name,
            forecast_granularity=forecast_granularity,
            result_mode=result_mode,
            comparison_granularity=comparison_granularity,
            status=status,
        )
        self.session.add(result)
        self.session.flush()
        return result

    def replace_series_points(self, comparison_result_id: str, points: list[dict[str, object]]) -> None:
        self.session.execute(
            delete(DemandComparisonSeriesPoint).where(DemandComparisonSeriesPoint.comparison_result_id == comparison_result_id)
        )
        for point in points:
            self.session.add(
                DemandComparisonSeriesPoint(
                    comparison_result_id=comparison_result_id,
                    series_type=str(point["series_type"]),
                    bucket_start=point["bucket_start"],
                    bucket_end=point["bucket_end"],
                    service_category=str(point["service_category"]),
                    geography_key=point.get("geography_key"),
                    value=float(point["value"]),
                )
            )
        self.session.flush()

    def replace_missing_combinations(self, comparison_result_id: str, rows: list[dict[str, object]]) -> None:
        self.session.execute(
            delete(ComparisonMissingCombination).where(ComparisonMissingCombination.comparison_result_id == comparison_result_id)
        )
        for row in rows:
            self.session.add(
                ComparisonMissingCombination(
                    comparison_result_id=comparison_result_id,
                    service_category=str(row["service_category"]),
                    geography_key=row.get("geography_key"),
                    missing_source=str(row["missing_source"]),
                    message=str(row["message"]),
                )
            )
        self.session.flush()

    def finalize_request(
        self,
        comparison_request_id: str,
        *,
        status: str,
        warning_status: str | None = None,
        failure_reason: str | None = None,
        render_reported: bool = False,
    ) -> DemandComparisonRequest:
        record = self.require_request(comparison_request_id)
        record.status = status
        record.failure_reason = failure_reason
        record.completed_at = datetime.utcnow()
        if warning_status is not None:
            record.warning_status = warning_status
        if render_reported:
            record.render_reported_at = datetime.utcnow()
        self.session.flush()
        return record

    def upsert_outcome(
        self,
        *,
        comparison_request_id: str,
        outcome_type: str,
        warning_acknowledged: bool,
        message: str,
    ) -> DemandComparisonOutcomeRecord:
        record = self.session.scalar(
            select(DemandComparisonOutcomeRecord).where(
                DemandComparisonOutcomeRecord.comparison_request_id == comparison_request_id
            )
        )
        if record is None:
            record = DemandComparisonOutcomeRecord(
                comparison_request_id=comparison_request_id,
                outcome_type=outcome_type,
                warning_acknowledged=warning_acknowledged,
                message=message,
            )
            self.session.add(record)
        else:
            record.outcome_type = outcome_type
            record.warning_acknowledged = warning_acknowledged
            record.message = message
            record.recorded_at = datetime.utcnow()
        self.session.flush()
        return record

    def require_request(self, comparison_request_id: str) -> DemandComparisonRequest:
        record = self.session.get(DemandComparisonRequest, comparison_request_id)
        if record is None:
            raise LookupError("Demand comparison request not found")
        return record
