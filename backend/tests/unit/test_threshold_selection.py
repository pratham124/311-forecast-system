from __future__ import annotations

from dataclasses import dataclass

from app.services.threshold_selection_service import ThresholdSelectionService


@dataclass
class FakeRule:
    name: str


def test_threshold_selection_prefers_geography_specific_rule() -> None:
    service = ThresholdSelectionService()

    result = service.select(
        geography_value="Ward 1",
        geography_rule=FakeRule("geo"),
        category_rule=FakeRule("category"),
    )

    assert result.rule is not None
    assert result.rule.name == "geo"


def test_threshold_selection_falls_back_to_category_rule() -> None:
    service = ThresholdSelectionService()

    result = service.select(
        geography_value="Ward 2",
        geography_rule=None,
        category_rule=FakeRule("category"),
    )

    assert result.rule is not None
    assert result.rule.name == "category"
