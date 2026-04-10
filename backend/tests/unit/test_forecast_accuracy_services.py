from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.forecast_accuracy_alignment_service import ForecastAccuracyAlignmentService
from app.services.forecast_accuracy_metric_service import ForecastAccuracyMetricService


class FakeEvaluationRepository:
    def __init__(self, bundles=None, values=None) -> None:
        self._bundles = bundles or []
        self._values = values or {}

    def list_result_bundles_for_product(self, _product: str, limit: int | None = None):
        return self._bundles[:limit]

    def list_metric_values(self, segment_id: str):
        return self._values.get(segment_id, [])


def test_alignment_service_aligns_matching_buckets() -> None:
    service = ForecastAccuracyAlignmentService()
    result = service.align(
        forecast_rows=[
            {
                "bucket_start": datetime(2026, 3, 1, 0, tzinfo=timezone.utc),
                "bucket_end": datetime(2026, 3, 1, 1, tzinfo=timezone.utc),
                "service_category": "Roads",
                "forecast_value": 4.0,
            }
        ],
        actual_rows=[
            {
                "bucket_start": datetime(2026, 3, 1, 0, tzinfo=timezone.utc),
                "bucket_end": datetime(2026, 3, 1, 1, tzinfo=timezone.utc),
                "service_category": "Roads",
                "actual_value": 3.0,
            }
        ],
    )
    assert result.excluded_bucket_count == 0
    assert result.aligned_buckets[0]["absolute_error_value"] == 1.0


def test_metric_service_reuses_precomputed_exact_match() -> None:
    segment = SimpleNamespace(evaluation_segment_id="seg-1", segment_type="overall", segment_key="overall")
    bundle = SimpleNamespace(
        result=SimpleNamespace(
            evaluation_result_id="eval-1",
            evaluation_window_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
            evaluation_window_end=datetime(2026, 3, 2, tzinfo=timezone.utc),
        ),
        segments=[segment],
    )
    values = {
        "seg-1": [
            SimpleNamespace(compared_method="forecast_engine", is_excluded=False, metric_value=1.0, metric_name="mae"),
            SimpleNamespace(compared_method="forecast_engine", is_excluded=False, metric_value=2.0, metric_name="rmse"),
            SimpleNamespace(compared_method="forecast_engine", is_excluded=False, metric_value=3.0, metric_name="mape"),
        ]
    }
    service = ForecastAccuracyMetricService(FakeEvaluationRepository([bundle], values))
    status, metrics, evaluation_result_id, message = service.resolve_metrics(
        aligned_buckets=[{"forecast_value": 4.0, "actual_value": 3.0}],
        time_range_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        time_range_end=datetime(2026, 3, 2, tzinfo=timezone.utc),
        service_category=None,
    )
    assert status == "retrieved_precomputed"
    assert metrics == {"mae": 1.0, "rmse": 2.0, "mape": 3.0}
    assert evaluation_result_id == "eval-1"
    assert message is None
