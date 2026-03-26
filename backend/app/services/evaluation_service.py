from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Callable

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.logging import summarize_evaluation_failure, summarize_evaluation_partial_success, summarize_evaluation_success
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.evaluation_repository import EvaluationRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.schemas.evaluation import CurrentEvaluationRead, EvaluationRunStatusRead, EvaluationSegmentRead, FairComparisonMetadataRead, MethodMetricSummaryRead, MetricValueRead
from app.services.baseline_service import BaselineGenerationError, BaselineService
from app.services.evaluation_scope_service import ActualsNotReadyError, EvaluationScopeService, MissingForecastScopeError
from app.services.evaluation_segments import build_evaluation_segments


@dataclass
class EvaluationService:
    evaluation_repository: EvaluationRepository
    cleaned_dataset_repository: CleanedDatasetRepository
    forecast_repository: ForecastRepository
    weekly_forecast_repository: WeeklyForecastRepository
    settings: object
    logger: logging.Logger | None = None

    def __post_init__(self) -> None:
        self.logger = self.logger or logging.getLogger("evaluation")
        self.scope_service = EvaluationScopeService(
            cleaned_dataset_repository=self.cleaned_dataset_repository,
            forecast_repository=self.forecast_repository,
            weekly_forecast_repository=self.weekly_forecast_repository,
            settings=self.settings,
        )
        self.baseline_service = BaselineService(self.cleaned_dataset_repository, self.settings)

    def start_run(self, forecast_product: str, trigger_type: str, now=None):
        scope = self.scope_service.resolve_scope(forecast_product, now=now)
        return self.evaluation_repository.create_run(
            trigger_type=trigger_type,
            forecast_product_name=scope.forecast_product_name,
            source_cleaned_dataset_version_id=scope.source_cleaned_dataset_version_id,
            source_forecast_version_id=scope.source_forecast_version_id,
            source_weekly_forecast_version_id=scope.source_weekly_forecast_version_id,
            evaluation_window_start=scope.evaluation_window_start,
            evaluation_window_end=scope.evaluation_window_end,
        )

    def execute_run(self, evaluation_run_id: str):
        run = self.evaluation_repository.require_run(evaluation_run_id)
        if run.status != "running":
            return run
        if run.source_cleaned_dataset_version_id is None:
            return self._fail(run.evaluation_run_id, "missing_input_data", "No approved cleaned dataset is available", "approved cleaned dataset missing")

        scope = self.scope_service.resolve_scope_from_run(run)
        try:
            engine_rows = self.scope_service.list_engine_rows(scope)
        except MissingForecastScopeError as exc:
            return self._fail(run.evaluation_run_id, "missing_forecast_output", str(exc), "current forecast output missing")

        ensure_actuals_ready = getattr(self.scope_service, "ensure_actuals_ready", None)
        if callable(ensure_actuals_ready):
            try:
                ensure_actuals_ready(scope)
            except ActualsNotReadyError as exc:
                return self._fail(run.evaluation_run_id, "actuals_not_available", str(exc), "evaluation waiting for observed demand")

        actual_rows = self.scope_service.list_actual_rows(scope)
        try:
            aligned_rows = self.scope_service.build_aligned_rows(scope, engine_rows, actual_rows)
        except MissingForecastScopeError as exc:
            return self._fail(run.evaluation_run_id, "missing_input_data", str(exc), "actuals unavailable for comparison")

        try:
            comparison_rows = self.baseline_service.generate_baselines(scope.forecast_product_name, aligned_rows)
        except Exception as exc:
            if isinstance(exc, BaselineGenerationError) or isinstance(exc, RuntimeError):
                return self._fail(run.evaluation_run_id, "baseline_failure", str(exc), "baseline generation failed")
            raise

        excluded_scopes = list(getattr(comparison_rows, "excluded_scopes", []))
        segments, comparison_status = build_evaluation_segments(comparison_rows, excluded_scopes=excluded_scopes)
        summary = f"Evaluation stored for {scope.forecast_product_name} across {len(comparison_rows)} comparison rows"
        if excluded_scopes:
            summary += f"; excluded categories without baseline history: {', '.join(excluded_scopes)}"
        comparison_summary = self._build_comparison_summary(segments)

        try:
            result = self.evaluation_repository.create_result(
                evaluation_run_id=run.evaluation_run_id,
                forecast_product_name=scope.forecast_product_name,
                source_cleaned_dataset_version_id=run.source_cleaned_dataset_version_id,
                source_forecast_version_id=run.source_forecast_version_id,
                source_weekly_forecast_version_id=run.source_weekly_forecast_version_id,
                evaluation_window_start=run.evaluation_window_start,
                evaluation_window_end=run.evaluation_window_end,
                comparison_status=comparison_status,
                baseline_methods=self._baseline_methods(),
                metric_set=["mae", "rmse", "mape"],
                summary=summary,
                comparison_summary=comparison_summary,
            )
            self.evaluation_repository.replace_segments(result.evaluation_result_id, segments)
            self.evaluation_repository.store_result_and_activate(
                evaluation_result_id=result.evaluation_result_id,
                updated_by_run_id=run.evaluation_run_id,
            )
        except Exception as exc:
            return self._fail(run.evaluation_run_id, "storage_failure", str(exc), "evaluation result storage failed")

        if comparison_status == "partial":
            self.logger.info(
                "%s",
                summarize_evaluation_partial_success(
                    "evaluation.stored",
                    run_id=run.evaluation_run_id,
                    result_id=result.evaluation_result_id,
                    comparison_status=comparison_status,
                    forecast_product=scope.forecast_product_name,
                ),
            )
        else:
            self.logger.info(
                "%s",
                summarize_evaluation_success(
                    "evaluation.stored",
                    run_id=run.evaluation_run_id,
                    result_id=result.evaluation_result_id,
                    comparison_status=comparison_status,
                    forecast_product=scope.forecast_product_name,
                ),
            )
        return self.evaluation_repository.finalize_success(
            run.evaluation_run_id,
            result_type="stored_partial" if comparison_status == "partial" else "stored_complete",
            evaluation_result_id=result.evaluation_result_id,
            summary=summary,
        )

    def get_run_status(self, evaluation_run_id: str) -> EvaluationRunStatusRead:
        run = self.evaluation_repository.get_run(evaluation_run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation run not found")
        return EvaluationRunStatusRead(
            evaluationRunId=run.evaluation_run_id,
            triggerType=run.trigger_type,
            forecastProduct=run.forecast_product_name,
            sourceCleanedDatasetVersionId=run.source_cleaned_dataset_version_id,
            sourceForecastVersionId=run.source_forecast_version_id,
            sourceWeeklyForecastVersionId=run.source_weekly_forecast_version_id,
            evaluationWindowStart=run.evaluation_window_start,
            evaluationWindowEnd=run.evaluation_window_end,
            status=run.status,
            resultType=run.result_type,
            evaluationResultId=run.evaluation_result_id,
            startedAt=run.started_at,
            completedAt=run.completed_at,
            failureReason=run.failure_reason,
            summary=run.summary,
        )

    def get_current_evaluation(self, forecast_product: str) -> CurrentEvaluationRead:
        marker = self.evaluation_repository.get_current_marker(forecast_product)
        if marker is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Current evaluation not found")
        bundle = self.evaluation_repository.get_result_bundle(marker.evaluation_result_id)
        if bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Current evaluation not found")
        scope = self.scope_service.resolve_scope_from_run(self.evaluation_repository.require_run(marker.updated_by_run_id))
        segments = self._build_segment_reads(bundle)
        return CurrentEvaluationRead(
            evaluationResultId=bundle.result.evaluation_result_id,
            forecastProduct=bundle.result.forecast_product_name,
            sourceCleanedDatasetVersionId=bundle.result.source_cleaned_dataset_version_id,
            sourceForecastVersionId=bundle.result.source_forecast_version_id,
            sourceWeeklyForecastVersionId=bundle.result.source_weekly_forecast_version_id,
            evaluationWindowStart=bundle.result.evaluation_window_start,
            evaluationWindowEnd=bundle.result.evaluation_window_end,
            comparisonStatus=bundle.result.comparison_status,
            baselineMethods=json.loads(bundle.result.baseline_methods_json),
            metricSet=json.loads(bundle.result.metric_set_json),
            fairComparison=FairComparisonMetadataRead.model_validate(self.scope_service.fair_comparison_metadata(scope, [segment.model_dump(by_alias=False) for segment in segments])),
            updatedAt=marker.updated_at,
            updatedByRunId=marker.updated_by_run_id,
            summary=bundle.result.summary,
            comparisonSummary=bundle.result.comparison_summary,
            segments=segments,
        )

    def _build_segment_reads(self, bundle) -> list[EvaluationSegmentRead]:
        reads: list[EvaluationSegmentRead] = []
        for segment in bundle.segments:
            metrics_by_method: dict[str, list[MetricValueRead]] = {}
            labels: dict[str, str] = {}
            for value in bundle.metric_values_by_segment_id.get(segment.evaluation_segment_id, []):
                metrics_by_method.setdefault(value.compared_method, []).append(
                    MetricValueRead(
                        metricName=value.metric_name,
                        metricValue=float(value.metric_value) if value.metric_value is not None else None,
                        isExcluded=value.is_excluded,
                        exclusionReason=value.exclusion_reason,
                    )
                )
                labels[value.compared_method] = value.compared_method_label
            method_metrics = [
                MethodMetricSummaryRead(methodName=labels[key], metrics=metrics_by_method[key])
                for key in sorted(metrics_by_method)
            ]
            reads.append(
                EvaluationSegmentRead(
                    segmentType=segment.segment_type,
                    segmentKey=segment.segment_key,
                    segmentStatus=segment.segment_status,
                    comparisonRowCount=segment.comparison_row_count,
                    excludedMetricCount=segment.excluded_metric_count,
                    notes=segment.notes,
                    methodMetrics=method_metrics,
                )
            )
        return reads

    def _baseline_methods(self) -> list[str]:
        raw = getattr(self.settings, "evaluation_baseline_methods", "seasonal_naive,moving_average")
        return [item.strip() for item in raw.split(",") if item.strip()]

    def _build_comparison_summary(self, segments: list[dict[str, object]]) -> str:
        overall = next(segment for segment in segments if segment["segment_type"] == "overall")
        scores: dict[str, float] = {}
        for method in overall["method_metrics"]:
            usable = [metric["metric_value"] for metric in method["metrics"] if metric["metric_value"] is not None]
            scores[str(method["compared_method"])] = sum(usable) / len(usable)
        engine = scores["forecast_engine"]
        baseline_best = min(scores["seasonal_naive"], scores["moving_average"])
        if engine < baseline_best:
            return "The forecasting engine outperformed the included baselines for the evaluated scope."
        if engine == baseline_best:
            return "The forecasting engine matched the strongest included baseline for the evaluated scope."
        return "The forecasting engine underperformed at least one included baseline for the evaluated scope."

    def _fail(self, evaluation_run_id: str, result_type: str, failure_reason: str, summary: str):
        self.logger.info(
            "%s",
            summarize_evaluation_failure(
                "evaluation.failed",
                run_id=evaluation_run_id,
                result_type=result_type,
                failure_reason=failure_reason,
            ),
        )
        return self.evaluation_repository.finalize_failed(
            evaluation_run_id,
            result_type=result_type,
            failure_reason=failure_reason,
            summary=summary,
        )


def build_evaluation_job(session_factory: Callable[[], object]):
    def run_job() -> list[str]:
        session = session_factory()
        try:
            from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
            from app.repositories.evaluation_repository import EvaluationRepository
            from app.repositories.forecast_repository import ForecastRepository
            from app.repositories.weekly_forecast_repository import WeeklyForecastRepository

            settings = get_settings()
            service = EvaluationService(
                evaluation_repository=EvaluationRepository(session),
                cleaned_dataset_repository=CleanedDatasetRepository(session),
                forecast_repository=ForecastRepository(session),
                weekly_forecast_repository=WeeklyForecastRepository(session),
                settings=settings,
                logger=logging.getLogger("scheduler.evaluation"),
            )
            run_ids: list[str] = []
            for product in [item.strip() for item in getattr(settings, "evaluation_forecast_products", "daily_1_day,weekly_7_day").split(",") if item.strip()]:
                run = service.start_run(product, trigger_type="scheduled")
                session.commit()
                service.execute_run(run.evaluation_run_id)
                session.commit()
                run_ids.append(run.evaluation_run_id)
            return run_ids
        finally:
            session.close()

    return run_job
