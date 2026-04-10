from __future__ import annotations

from dataclasses import dataclass

from app.repositories.threshold_configuration_repository import ThresholdRule


@dataclass
class ThresholdSelectionResult:
    rule: ThresholdRule | None


class ThresholdSelectionService:
    def select(self, *, geography_value: str | None, geography_rule: ThresholdRule | None, category_rule: ThresholdRule | None) -> ThresholdSelectionResult:
        if geography_value and geography_rule is not None:
            return ThresholdSelectionResult(rule=geography_rule)
        return ThresholdSelectionResult(rule=category_rule)
