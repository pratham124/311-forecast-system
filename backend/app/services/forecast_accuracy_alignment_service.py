from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ForecastAccuracyAlignmentResult:
    aligned_buckets: list[dict[str, object]]
    excluded_bucket_count: int


class ForecastAccuracyAlignmentService:
    def align(
        self,
        *,
        forecast_rows: list[dict[str, object]],
        actual_rows: list[dict[str, object]],
    ) -> ForecastAccuracyAlignmentResult:
        forecast_by_key = {
            (row["bucket_start"], row["service_category"]): row
            for row in forecast_rows
        }
        actual_by_key = {
            (row["bucket_start"], row["service_category"]): row
            for row in actual_rows
        }
        keys = sorted(set(forecast_by_key).intersection(actual_by_key))
        excluded_bucket_count = len(set(forecast_by_key).symmetric_difference(actual_by_key))
        aligned: list[dict[str, object]] = []
        for key in keys:
            forecast_row = forecast_by_key[key]
            actual_row = actual_by_key[key]
            forecast_value = float(forecast_row["forecast_value"])
            actual_value = float(actual_row["actual_value"])
            absolute_error = abs(forecast_value - actual_value)
            percentage_error = None if actual_value == 0 else abs((forecast_value - actual_value) / actual_value) * 100
            aligned.append(
                {
                    "bucket_start": forecast_row["bucket_start"],
                    "bucket_end": forecast_row["bucket_end"],
                    "service_category": forecast_row["service_category"],
                    "forecast_value": forecast_value,
                    "actual_value": actual_value,
                    "absolute_error_value": absolute_error,
                    "percentage_error_value": percentage_error,
                }
            )
        if not aligned:
            raise ValueError("No overlapping forecast and actual buckets are available for safe comparison")
        return ForecastAccuracyAlignmentResult(aligned_buckets=aligned, excluded_bucket_count=excluded_bucket_count)
