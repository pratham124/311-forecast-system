from __future__ import annotations

from math import sqrt

from app.repositories.evaluation_repository import EvaluationRepository


class ForecastAccuracyMetricService:
    def __init__(self, evaluation_repository: EvaluationRepository) -> None:
        self.evaluation_repository = evaluation_repository

    def resolve_metrics(
        self,
        *,
        aligned_buckets: list[dict[str, object]],
        time_range_start,
        time_range_end,
        service_category: str | None,
    ) -> tuple[str, dict[str, float] | None, str | None, str | None]:
        precomputed = self._find_precomputed_metrics(
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            service_category=service_category,
        )
        if precomputed is not None:
            return "retrieved_precomputed", precomputed["metrics"], precomputed["evaluation_result_id"], None
        try:
            metrics = self._compute_on_demand(aligned_buckets)
        except ValueError as exc:
            return "unavailable", None, None, str(exc)
        return "computed_on_demand", metrics, None, None

    def _find_precomputed_metrics(
        self,
        *,
        time_range_start,
        time_range_end,
        service_category: str | None,
    ) -> dict[str, object] | None:
        bundles = self.evaluation_repository.list_result_bundles_for_product("daily_1_day", limit=20)
        for bundle in bundles:
            result = bundle.result
            if result.evaluation_window_start != time_range_start or result.evaluation_window_end != time_range_end:
                continue
            if service_category:
                segment = next(
                    (item for item in bundle.segments if item.segment_type == "service_category" and item.segment_key == service_category),
                    None,
                )
            else:
                segment = next((item for item in bundle.segments if item.segment_type == "overall"), None)
            if segment is None:
                continue
            values = self.evaluation_repository.list_metric_values(segment.evaluation_segment_id)
            metrics = {}
            for value in values:
                if value.compared_method != "forecast_engine" or value.is_excluded or value.metric_value is None:
                    continue
                metrics[value.metric_name] = float(value.metric_value)
            if {"mae", "rmse", "mape"}.issubset(metrics):
                return {"metrics": metrics, "evaluation_result_id": result.evaluation_result_id}
        return None

    def _compute_on_demand(self, aligned_buckets: list[dict[str, object]]) -> dict[str, float]:
        if not aligned_buckets:
            raise ValueError("No aligned buckets are available for metric computation")
        if any(float(bucket["actual_value"]) == 0 for bucket in aligned_buckets):
            raise ValueError("Metrics are unavailable because MAPE cannot be computed when actual demand includes zero values")
        if len(aligned_buckets) < 2:
            raise ValueError("Metrics are unavailable because at least two aligned buckets are required for on-demand computation")
        errors = [abs(float(bucket["forecast_value"]) - float(bucket["actual_value"])) for bucket in aligned_buckets]
        squared_errors = [(float(bucket["forecast_value"]) - float(bucket["actual_value"])) ** 2 for bucket in aligned_buckets]
        percentage_errors = [
            abs((float(bucket["forecast_value"]) - float(bucket["actual_value"])) / float(bucket["actual_value"])) * 100
            for bucket in aligned_buckets
        ]
        return {
            "mae": round(sum(errors) / len(errors), 4),
            "rmse": round(sqrt(sum(squared_errors) / len(squared_errors)), 4),
            "mape": round(sum(percentage_errors) / len(percentage_errors), 4),
        }
