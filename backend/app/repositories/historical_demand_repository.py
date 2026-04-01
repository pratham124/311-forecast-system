from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import (
    HistoricalAnalysisOutcomeRecord,
    HistoricalDemandAnalysisRequest,
    HistoricalDemandAnalysisResult,
    HistoricalDemandSummaryPoint,
)


class HistoricalDemandRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_request(
        self,
        *,
        requested_by_actor: str,
        source_cleaned_dataset_version_id: str | None,
        service_category_filter: str | None,
        time_range_start: datetime,
        time_range_end: datetime,
        geography_filter_type: str | None,
        geography_filter_value: str | None,
        warning_status: str,
    ) -> HistoricalDemandAnalysisRequest:
        record = HistoricalDemandAnalysisRequest(
            requested_by_actor=requested_by_actor,
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            service_category_filter=service_category_filter,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            geography_filter_type=geography_filter_type,
            geography_filter_value=geography_filter_value,
            warning_status=warning_status,
            status="running",
        )
        self.session.add(record)
        self.session.flush()
        return record

    def create_result(
        self,
        *,
        analysis_request_id: str,
        source_cleaned_dataset_version_id: str,
        aggregation_granularity: str,
        result_mode: str,
        service_category_filter: str | None,
        time_range_start: datetime,
        time_range_end: datetime,
        geography_filter_type: str | None,
        geography_filter_value: str | None,
        record_count: int,
    ) -> HistoricalDemandAnalysisResult:
        result = HistoricalDemandAnalysisResult(
            analysis_request_id=analysis_request_id,
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            aggregation_granularity=aggregation_granularity,
            result_mode=result_mode,
            service_category_filter=service_category_filter,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            geography_filter_type=geography_filter_type,
            geography_filter_value=geography_filter_value,
            record_count=record_count,
        )
        self.session.add(result)
        self.session.flush()
        return result

    def replace_summary_points(self, analysis_result_id: str, points: list[dict[str, object]]) -> None:
        self.session.execute(
            delete(HistoricalDemandSummaryPoint).where(HistoricalDemandSummaryPoint.analysis_result_id == analysis_result_id)
        )
        for point in points:
            self.session.add(
                HistoricalDemandSummaryPoint(
                    analysis_result_id=analysis_result_id,
                    bucket_start=point["bucket_start"],
                    bucket_end=point["bucket_end"],
                    service_category=str(point["service_category"]),
                    geography_key=point.get("geography_key"),
                    demand_count=int(point["demand_count"]),
                )
            )
        self.session.flush()

    def finalize_request(
        self,
        analysis_request_id: str,
        *,
        status: str,
        failure_reason: str | None = None,
        warning_status: str | None = None,
    ) -> HistoricalDemandAnalysisRequest:
        record = self.require_request(analysis_request_id)
        record.status = status
        record.failure_reason = failure_reason
        record.completed_at = datetime.utcnow()
        if warning_status is not None:
            record.warning_status = warning_status
        self.session.flush()
        return record

    def upsert_outcome(
        self,
        *,
        analysis_request_id: str,
        outcome_type: str,
        warning_acknowledged: bool,
        message: str,
    ) -> HistoricalAnalysisOutcomeRecord:
        record = self.session.scalar(
            select(HistoricalAnalysisOutcomeRecord).where(
                HistoricalAnalysisOutcomeRecord.analysis_request_id == analysis_request_id
            )
        )
        if record is None:
            record = HistoricalAnalysisOutcomeRecord(
                analysis_request_id=analysis_request_id,
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

    def get_result_bundle(self, analysis_request_id: str) -> tuple[HistoricalDemandAnalysisResult, list[HistoricalDemandSummaryPoint]] | None:
        result = self.session.scalar(
            select(HistoricalDemandAnalysisResult).where(HistoricalDemandAnalysisResult.analysis_request_id == analysis_request_id)
        )
        if result is None:
            return None
        points = list(
            self.session.scalars(
                select(HistoricalDemandSummaryPoint)
                .where(HistoricalDemandSummaryPoint.analysis_result_id == result.analysis_result_id)
                .order_by(
                    HistoricalDemandSummaryPoint.bucket_start.asc(),
                    HistoricalDemandSummaryPoint.service_category.asc(),
                    HistoricalDemandSummaryPoint.geography_key.asc(),
                )
            )
        )
        return result, points

    def require_request(self, analysis_request_id: str) -> HistoricalDemandAnalysisRequest:
        record = self.session.get(HistoricalDemandAnalysisRequest, analysis_request_id)
        if record is None:
            raise LookupError("Historical demand analysis request not found")
        return record
