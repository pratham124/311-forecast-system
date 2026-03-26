from __future__ import annotations

from collections import defaultdict

from app.services.evaluation_metrics import compute_metric_values


METHOD_LABELS = {
    "forecast_engine": "Forecast Engine",
    "seasonal_naive": "Seasonal Naive",
    "moving_average": "Moving Average",
}


def _build_segment(segment_type: str, segment_key: str, rows: list[dict[str, object]]) -> dict[str, object]:
    method_metrics = [
        compute_metric_values(rows, "forecast_engine", METHOD_LABELS["forecast_engine"]),
        compute_metric_values(rows, "seasonal_naive", METHOD_LABELS["seasonal_naive"]),
        compute_metric_values(rows, "moving_average", METHOD_LABELS["moving_average"]),
    ]
    excluded_metric_count = sum(1 for method in method_metrics for metric in method["metrics"] if metric["is_excluded"])
    notes = None
    if excluded_metric_count:
        notes = "Some metrics were excluded because one or more comparison rows had zero actual demand."
    return {
        "segment_type": segment_type,
        "segment_key": segment_key,
        "segment_status": "partial" if excluded_metric_count else "complete",
        "comparison_row_count": len(rows),
        "excluded_metric_count": excluded_metric_count,
        "notes": notes,
        "method_metrics": method_metrics,
    }


def build_evaluation_segments(rows: list[dict[str, object]], *, excluded_scopes: list[str] | None = None) -> tuple[list[dict[str, object]], str]:
    if not rows:
        raise ValueError("Cannot build evaluation segments without aligned rows")

    excluded_scopes = sorted(set(excluded_scopes or []))
    segments = [_build_segment("overall", "overall", rows)]
    if excluded_scopes:
        segments[0]["segment_status"] = "partial"
        segments[0]["notes"] = f"Excluded categories without baseline history: {', '.join(excluded_scopes)}"

    rows_by_category: dict[str, list[dict[str, object]]] = defaultdict(list)
    rows_by_period: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        rows_by_category[str(row["service_category"])].append(row)
        rows_by_period[str(row["time_period_key"])].append(row)

    for category in sorted(rows_by_category):
        segment = _build_segment("service_category", category, rows_by_category[category])
        if category in excluded_scopes:
            segment["segment_status"] = "partial"
            segment["notes"] = "This category was partially evaluated because some comparison rows had no baseline history."
        segments.append(segment)
    for category in excluded_scopes:
        if category not in rows_by_category:
            segments.append(
                {
                    "segment_type": "service_category",
                    "segment_key": category,
                    "segment_status": "partial",
                    "comparison_row_count": 0,
                    "excluded_metric_count": 0,
                    "notes": "This category was excluded because no baseline history was available in the evaluation lookback window.",
                    "method_metrics": [],
                }
            )
    for period in sorted(rows_by_period):
        segments.append(_build_segment("time_period", period, rows_by_period[period]))

    comparison_status = "partial" if excluded_scopes or any(segment["segment_status"] == "partial" for segment in segments) else "complete"
    return segments, comparison_status
