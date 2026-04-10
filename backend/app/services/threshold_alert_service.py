from __future__ import annotations


class ThresholdAlertService:
    def is_exceeded(self, *, forecast_value: float, threshold_value: float) -> bool:
        return forecast_value >= threshold_value

    def should_alert(self, *, current_state: str | None, forecast_value: float, threshold_value: float) -> bool:
        return self.is_exceeded(forecast_value=forecast_value, threshold_value=threshold_value) and current_state != "above_threshold_alerted"

    def next_state(self, *, forecast_value: float, threshold_value: float) -> str:
        return "above_threshold_alerted" if self.is_exceeded(forecast_value=forecast_value, threshold_value=threshold_value) else "below_or_equal"
