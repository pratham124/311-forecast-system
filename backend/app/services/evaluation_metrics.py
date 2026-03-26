from __future__ import annotations

from math import sqrt


def _round_metric(value: float) -> float:
    return round(value, 4)


def compute_metric_values(rows: list[dict[str, object]], compared_method: str, method_name: str) -> dict[str, object]:
    if not rows:
        raise ValueError("Cannot compute metrics without aligned comparison rows")

    errors = [abs(float(row[compared_method]) - float(row["actual"])) for row in rows]
    squared_errors = [(float(row[compared_method]) - float(row["actual"])) ** 2 for row in rows]
    actuals = [float(row["actual"]) for row in rows]

    metrics: list[dict[str, object]] = [
        {
            "metric_name": "mae",
            "metric_value": _round_metric(sum(errors) / len(errors)),
            "is_excluded": False,
            "exclusion_reason": None,
        },
        {
            "metric_name": "rmse",
            "metric_value": _round_metric(sqrt(sum(squared_errors) / len(squared_errors))),
            "is_excluded": False,
            "exclusion_reason": None,
        },
    ]

    if any(actual == 0 for actual in actuals):
        metrics.append(
            {
                "metric_name": "mape",
                "metric_value": None,
                "is_excluded": True,
                "exclusion_reason": "MAPE cannot be computed when actual demand includes zero values",
            }
        )
    else:
        percentage_errors = [abs((float(row[compared_method]) - float(row["actual"])) / float(row["actual"])) * 100 for row in rows]
        metrics.append(
            {
                "metric_name": "mape",
                "metric_value": _round_metric(sum(percentage_errors) / len(percentage_errors)),
                "is_excluded": False,
                "exclusion_reason": None,
            }
        )

    return {
        "compared_method": compared_method,
        "method_name": method_name,
        "metrics": metrics,
    }
