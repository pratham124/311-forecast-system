from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ThresholdDecision:
    exceeded: bool
    should_create_alert: bool
    next_state: str
    outcome: str


class ThresholdAlertService:
    def evaluate(
        self,
        *,
        forecast_value: float,
        threshold_value: float,
        current_state: str | None,
    ) -> ThresholdDecision:
        if forecast_value <= threshold_value:
            return ThresholdDecision(
                exceeded=False,
                should_create_alert=False,
                next_state="below_or_equal",
                outcome="below_or_equal",
            )

        if current_state == "above_threshold_alerted":
            return ThresholdDecision(
                exceeded=True,
                should_create_alert=False,
                next_state="above_threshold_alerted",
                outcome="exceeded_suppressed",
            )

        return ThresholdDecision(
            exceeded=True,
            should_create_alert=True,
            next_state="above_threshold_alerted",
            outcome="exceeded_alert_created",
        )
