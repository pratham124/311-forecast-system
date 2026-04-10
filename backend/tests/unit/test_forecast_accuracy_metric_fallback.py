from __future__ import annotations

from app.services.forecast_accuracy_metric_service import ForecastAccuracyMetricService


class EmptyEvaluationRepository:
    def list_result_bundles_for_product(self, _product: str, limit: int | None = None):
        return []


def test_metric_service_computes_on_demand_when_no_precomputed_match() -> None:
    service = ForecastAccuracyMetricService(EmptyEvaluationRepository())
    status, metrics, evaluation_result_id, message = service.resolve_metrics(
        aligned_buckets=[
            {"forecast_value": 4.0, "actual_value": 2.0},
            {"forecast_value": 3.0, "actual_value": 3.0},
        ],
        time_range_start=None,
        time_range_end=None,
        service_category=None,
    )
    assert status == "computed_on_demand"
    assert metrics is not None
    assert evaluation_result_id is None
    assert message is None


def test_metric_service_reports_unavailable_when_actual_contains_zero() -> None:
    service = ForecastAccuracyMetricService(EmptyEvaluationRepository())
    status, metrics, evaluation_result_id, message = service.resolve_metrics(
        aligned_buckets=[{"forecast_value": 4.0, "actual_value": 0.0}],
        time_range_start=None,
        time_range_end=None,
        service_category=None,
    )
    assert status == "unavailable"
    assert metrics is None
    assert evaluation_result_id is None
    assert "MAPE cannot be computed" in str(message)
