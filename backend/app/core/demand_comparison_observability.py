from __future__ import annotations

from typing import Any

from app.core.logging import sanitize_mapping, summarize_status


def summarize_demand_comparison_event(event: str, **fields: Any) -> dict[str, Any]:
    return summarize_status(event, **sanitize_mapping(fields))


def summarize_demand_comparison_success(event: str, **fields: Any) -> dict[str, Any]:
    return summarize_demand_comparison_event(event, outcome="success", **fields)


def summarize_demand_comparison_warning(event: str, **fields: Any) -> dict[str, Any]:
    return summarize_demand_comparison_event(event, outcome="warning", **fields)


def summarize_demand_comparison_failure(event: str, **fields: Any) -> dict[str, Any]:
    return summarize_demand_comparison_event(event, outcome="failure", **fields)
