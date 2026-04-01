from __future__ import annotations

from app.schemas.demand_comparison_models import MissingCombinationRecord


def map_terminal_outcome(
    *,
    has_historical_data: bool,
    has_forecast_data: bool,
    missing_combinations: list[MissingCombinationRecord],
) -> str:
    if has_historical_data and has_forecast_data:
        return "partial_forecast_missing" if missing_combinations else "success"
    if has_forecast_data:
        return "forecast_only"
    return "historical_only"


def build_terminal_message(
    outcome_status: str,
    *,
    missing_count: int = 0,
    uncovered_historical_interval: str | None = None,
) -> str:
    if outcome_status == "success":
        return "Historical and forecast demand were aligned successfully."
    if outcome_status == "partial_forecast_missing":
        return f"Comparison loaded with {missing_count} selected combinations missing forecast data."
    if outcome_status == "forecast_only":
        interval = f" Historical coverage is missing for {uncovered_historical_interval}." if uncovered_historical_interval else ""
        return f"Historical demand is unavailable for the selected scope.{interval}"
    if outcome_status == "historical_only":
        return "Forecast demand is unavailable for the selected scope."
    if outcome_status == "historical_retrieval_failed":
        return "Historical demand data could not be retrieved."
    if outcome_status == "forecast_retrieval_failed":
        return "Forecast demand data could not be retrieved."
    if outcome_status == "alignment_failed":
        return "Historical and forecast demand could not be aligned for the selected scope."
    return "Demand comparison could not be completed."
