from __future__ import annotations

from dataclasses import dataclass

from app.services.surge_detection_service import SurgeMetrics


@dataclass
class ConfirmationDecision:
    outcome: str
    z_score_check_passed: bool | None
    percent_floor_check_passed: bool | None


class SurgeConfirmationService:
    def evaluate(
        self,
        *,
        metrics: SurgeMetrics,
        z_score_threshold: float,
        percent_above_forecast_floor: float,
        active_surge: bool,
    ) -> ConfirmationDecision:
        z_score_check = metrics.residual_z_score >= z_score_threshold
        if metrics.forecast_p50_value <= 0:
            percent_check = metrics.actual_demand_value > 0
        else:
            percent_check = (metrics.percent_above_forecast or 0.0) >= percent_above_forecast_floor
        if z_score_check and percent_check:
            return ConfirmationDecision(
                outcome="suppressed_active_surge" if active_surge else "confirmed",
                z_score_check_passed=True,
                percent_floor_check_passed=True,
            )
        return ConfirmationDecision(
            outcome="filtered",
            z_score_check_passed=z_score_check,
            percent_floor_check_passed=percent_check,
        )
