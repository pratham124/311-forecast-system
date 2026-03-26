from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import CurrentEvaluationMarker, EvaluationResult, EvaluationRun, EvaluationSegment, MetricComparisonValue


@dataclass
class EvaluationResultBundle:
    result: EvaluationResult
    segments: list[EvaluationSegment]
    metric_values_by_segment_id: dict[str, list[MetricComparisonValue]]


class EvaluationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_run(
        self,
        *,
        trigger_type: str,
        forecast_product_name: str,
        source_cleaned_dataset_version_id: str | None,
        source_forecast_version_id: str | None,
        source_weekly_forecast_version_id: str | None,
        evaluation_window_start: datetime,
        evaluation_window_end: datetime,
    ) -> EvaluationRun:
        run = EvaluationRun(
            trigger_type=trigger_type,
            forecast_product_name=forecast_product_name,
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            source_forecast_version_id=source_forecast_version_id,
            source_weekly_forecast_version_id=source_weekly_forecast_version_id,
            evaluation_window_start=evaluation_window_start,
            evaluation_window_end=evaluation_window_end,
            status="running",
        )
        self.session.add(run)
        self.session.flush()
        return run

    def get_run(self, evaluation_run_id: str) -> EvaluationRun | None:
        return self.session.get(EvaluationRun, evaluation_run_id)

    def create_result(
        self,
        *,
        evaluation_run_id: str,
        forecast_product_name: str,
        source_cleaned_dataset_version_id: str,
        source_forecast_version_id: str | None,
        source_weekly_forecast_version_id: str | None,
        evaluation_window_start: datetime,
        evaluation_window_end: datetime,
        comparison_status: str,
        baseline_methods: list[str],
        metric_set: list[str],
        summary: str,
        comparison_summary: str,
    ) -> EvaluationResult:
        result = EvaluationResult(
            evaluation_run_id=evaluation_run_id,
            forecast_product_name=forecast_product_name,
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            source_forecast_version_id=source_forecast_version_id,
            source_weekly_forecast_version_id=source_weekly_forecast_version_id,
            evaluation_window_start=evaluation_window_start,
            evaluation_window_end=evaluation_window_end,
            comparison_status=comparison_status,
            baseline_methods_json=json.dumps(baseline_methods),
            metric_set_json=json.dumps(metric_set),
            storage_status="pending",
            summary=summary,
            comparison_summary=comparison_summary,
        )
        self.session.add(result)
        self.session.flush()
        return result

    def replace_segments(self, evaluation_result_id: str, segments: list[dict[str, object]]) -> None:
        existing_segments = self.session.scalars(
            select(EvaluationSegment).where(EvaluationSegment.evaluation_result_id == evaluation_result_id)
        ).all()
        for segment in existing_segments:
            self.session.execute(
                delete(MetricComparisonValue).where(MetricComparisonValue.evaluation_segment_id == segment.evaluation_segment_id)
            )
        self.session.execute(delete(EvaluationSegment).where(EvaluationSegment.evaluation_result_id == evaluation_result_id))
        self.session.flush()

        for segment_payload in segments:
            segment = EvaluationSegment(
                evaluation_result_id=evaluation_result_id,
                segment_type=str(segment_payload["segment_type"]),
                segment_key=str(segment_payload["segment_key"]),
                segment_status=str(segment_payload["segment_status"]),
                comparison_row_count=int(segment_payload["comparison_row_count"]),
                excluded_metric_count=int(segment_payload["excluded_metric_count"]),
                notes=segment_payload.get("notes"),
            )
            self.session.add(segment)
            self.session.flush()
            for method_payload in segment_payload["method_metrics"]:
                for metric_payload in method_payload["metrics"]:
                    self.session.add(
                        MetricComparisonValue(
                            evaluation_segment_id=segment.evaluation_segment_id,
                            compared_method=str(method_payload["compared_method"]),
                            compared_method_label=str(method_payload["method_name"]),
                            metric_name=str(metric_payload["metric_name"]),
                            metric_value=metric_payload.get("metric_value"),
                            is_excluded=bool(metric_payload["is_excluded"]),
                            exclusion_reason=metric_payload.get("exclusion_reason"),
                        )
                    )
        self.session.flush()

    def mark_result_stored(self, evaluation_result_id: str) -> EvaluationResult:
        result = self.require_result(evaluation_result_id)
        result.storage_status = "stored"
        result.stored_at = datetime.utcnow()
        self.session.flush()
        return result

    def activate_result(self, *, evaluation_result_id: str, updated_by_run_id: str) -> CurrentEvaluationMarker:
        result = self.require_result(evaluation_result_id)
        prior_results = self.session.scalars(
            select(EvaluationResult).where(
                EvaluationResult.forecast_product_name == result.forecast_product_name,
                EvaluationResult.is_current.is_(True),
            )
        ).all()
        for item in prior_results:
            item.is_current = False
        result.is_current = True
        result.activated_at = datetime.utcnow()

        marker = self.session.get(CurrentEvaluationMarker, result.forecast_product_name)
        if marker is None:
            marker = CurrentEvaluationMarker(
                forecast_product_name=result.forecast_product_name,
                evaluation_result_id=result.evaluation_result_id,
                source_cleaned_dataset_version_id=result.source_cleaned_dataset_version_id,
                source_forecast_version_id=result.source_forecast_version_id,
                source_weekly_forecast_version_id=result.source_weekly_forecast_version_id,
                evaluation_window_start=result.evaluation_window_start,
                evaluation_window_end=result.evaluation_window_end,
                comparison_status=result.comparison_status,
                updated_by_run_id=updated_by_run_id,
            )
            self.session.add(marker)
        else:
            marker.evaluation_result_id = result.evaluation_result_id
            marker.source_cleaned_dataset_version_id = result.source_cleaned_dataset_version_id
            marker.source_forecast_version_id = result.source_forecast_version_id
            marker.source_weekly_forecast_version_id = result.source_weekly_forecast_version_id
            marker.evaluation_window_start = result.evaluation_window_start
            marker.evaluation_window_end = result.evaluation_window_end
            marker.comparison_status = result.comparison_status
            marker.updated_at = datetime.utcnow()
            marker.updated_by_run_id = updated_by_run_id
        self.session.flush()
        return marker

    def store_result_and_activate(self, *, evaluation_result_id: str, updated_by_run_id: str) -> CurrentEvaluationMarker:
        result = self.require_result(evaluation_result_id)
        product_name = result.forecast_product_name
        prior_marker = self.get_current_marker(product_name)
        prior_marker_state = None
        if prior_marker is not None:
            prior_marker_state = {
                "evaluation_result_id": prior_marker.evaluation_result_id,
                "source_cleaned_dataset_version_id": prior_marker.source_cleaned_dataset_version_id,
                "source_forecast_version_id": prior_marker.source_forecast_version_id,
                "source_weekly_forecast_version_id": prior_marker.source_weekly_forecast_version_id,
                "evaluation_window_start": prior_marker.evaluation_window_start,
                "evaluation_window_end": prior_marker.evaluation_window_end,
                "comparison_status": prior_marker.comparison_status,
                "updated_at": prior_marker.updated_at,
                "updated_by_run_id": prior_marker.updated_by_run_id,
            }
        prior_current_ids = {
            item.evaluation_result_id
            for item in self.session.scalars(
                select(EvaluationResult).where(
                    EvaluationResult.forecast_product_name == product_name,
                    EvaluationResult.is_current.is_(True),
                )
            )
        }
        try:
            self.mark_result_stored(evaluation_result_id)
            return self.activate_result(evaluation_result_id=evaluation_result_id, updated_by_run_id=updated_by_run_id)
        except Exception:
            failed_result = self.require_result(evaluation_result_id)
            failed_result.storage_status = "pending"
            failed_result.stored_at = None
            failed_result.is_current = False
            failed_result.activated_at = None
            current_marker = self.get_current_marker(product_name)
            if prior_marker_state is None:
                if current_marker is not None and current_marker.evaluation_result_id == evaluation_result_id:
                    self.session.delete(current_marker)
            else:
                marker = current_marker or CurrentEvaluationMarker(forecast_product_name=product_name, **prior_marker_state)
                if current_marker is None:
                    self.session.add(marker)
                else:
                    marker.evaluation_result_id = prior_marker_state["evaluation_result_id"]
                    marker.source_cleaned_dataset_version_id = prior_marker_state["source_cleaned_dataset_version_id"]
                    marker.source_forecast_version_id = prior_marker_state["source_forecast_version_id"]
                    marker.source_weekly_forecast_version_id = prior_marker_state["source_weekly_forecast_version_id"]
                    marker.evaluation_window_start = prior_marker_state["evaluation_window_start"]
                    marker.evaluation_window_end = prior_marker_state["evaluation_window_end"]
                    marker.comparison_status = prior_marker_state["comparison_status"]
                    marker.updated_at = prior_marker_state["updated_at"]
                    marker.updated_by_run_id = prior_marker_state["updated_by_run_id"]
            for item in self.session.scalars(select(EvaluationResult).where(EvaluationResult.forecast_product_name == product_name)):
                item.is_current = item.evaluation_result_id in prior_current_ids
                if item.evaluation_result_id == evaluation_result_id and not item.is_current:
                    item.activated_at = None
            self.session.flush()
            raise

    def finalize_success(self, evaluation_run_id: str, *, result_type: str, evaluation_result_id: str, summary: str) -> EvaluationRun:
        run = self.require_run(evaluation_run_id)
        run.status = "success"
        run.result_type = result_type
        run.evaluation_result_id = evaluation_result_id
        run.summary = summary
        run.completed_at = datetime.utcnow()
        self.session.flush()
        return run

    def finalize_failed(self, evaluation_run_id: str, *, result_type: str, failure_reason: str, summary: str) -> EvaluationRun:
        run = self.require_run(evaluation_run_id)
        run.status = "failed"
        run.result_type = result_type
        run.failure_reason = failure_reason
        run.summary = summary
        run.completed_at = datetime.utcnow()
        self.session.flush()
        return run

    def get_current_marker(self, forecast_product_name: str) -> CurrentEvaluationMarker | None:
        return self.session.get(CurrentEvaluationMarker, forecast_product_name)

    def get_result(self, evaluation_result_id: str) -> EvaluationResult | None:
        return self.session.get(EvaluationResult, evaluation_result_id)

    def list_results_for_product(self, forecast_product_name: str, *, limit: int | None = None) -> list[EvaluationResult]:
        statement = (
            select(EvaluationResult)
            .where(EvaluationResult.forecast_product_name == forecast_product_name)
            .order_by(EvaluationResult.stored_at.desc().nullslast(), EvaluationResult.evaluation_result_id.desc())
        )
        if limit is not None:
            statement = statement.limit(limit)
        return list(self.session.scalars(statement))

    def get_current_result(self, forecast_product_name: str) -> EvaluationResult | None:
        marker = self.get_current_marker(forecast_product_name)
        if marker is None:
            return None
        return self.get_result(marker.evaluation_result_id)

    def list_segments(self, evaluation_result_id: str) -> list[EvaluationSegment]:
        statement = (
            select(EvaluationSegment)
            .where(EvaluationSegment.evaluation_result_id == evaluation_result_id)
            .order_by(EvaluationSegment.segment_type.asc(), EvaluationSegment.segment_key.asc())
        )
        return list(self.session.scalars(statement))

    def list_metric_values(self, evaluation_segment_id: str) -> list[MetricComparisonValue]:
        statement = (
            select(MetricComparisonValue)
            .where(MetricComparisonValue.evaluation_segment_id == evaluation_segment_id)
            .order_by(MetricComparisonValue.compared_method.asc(), MetricComparisonValue.metric_name.asc())
        )
        return list(self.session.scalars(statement))

    def get_result_bundle(self, evaluation_result_id: str) -> EvaluationResultBundle | None:
        result = self.get_result(evaluation_result_id)
        if result is None:
            return None
        segments = self.list_segments(evaluation_result_id)
        metric_values_by_segment_id = {
            segment.evaluation_segment_id: self.list_metric_values(segment.evaluation_segment_id)
            for segment in segments
        }
        return EvaluationResultBundle(
            result=result,
            segments=segments,
            metric_values_by_segment_id=metric_values_by_segment_id,
        )

    def list_result_bundles_for_product(
        self,
        forecast_product_name: str,
        *,
        limit: int | None = None,
    ) -> list[EvaluationResultBundle]:
        return [
            bundle
            for result in self.list_results_for_product(forecast_product_name, limit=limit)
            if (bundle := self.get_result_bundle(result.evaluation_result_id)) is not None
        ]

    def require_run(self, evaluation_run_id: str) -> EvaluationRun:
        run = self.get_run(evaluation_run_id)
        if run is None:
            raise ValueError("Evaluation run not found")
        return run

    def require_result(self, evaluation_result_id: str) -> EvaluationResult:
        result = self.get_result(evaluation_result_id)
        if result is None:
            raise ValueError("Evaluation result not found")
        return result
