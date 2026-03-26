from __future__ import annotations

import logging
from typing import Any

SENSITIVE_KEYS = {"authorization", "token", "secret", "password", "api_key"}


def redact_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        if len(value) <= 4:
            return "***"
        return f"{value[:2]}***{value[-2:]}"
    if isinstance(value, dict):
        return sanitize_mapping(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    return value


def sanitize_mapping(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in payload.items():
        if key.lower() in SENSITIVE_KEYS:
            sanitized[key] = redact_value(str(value))
            continue
        if isinstance(value, dict):
            sanitized[key] = sanitize_mapping(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_mapping(v) if isinstance(v, dict) else v for v in value]
        else:
            sanitized[key] = value
    return sanitized


def summarize_status(message: str, **fields: Any) -> dict[str, Any]:
    summary = sanitize_mapping(fields)
    summary["message"] = message
    return summary


def configure_logging() -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    return logging.getLogger("forecast_system")


def summarize_visualization_event(event: str, **fields: Any) -> dict[str, Any]:
    return summarize_status(event, **fields)


def _summarize_evaluation_outcome(event: str, *, outcome: str, **fields: Any) -> dict[str, Any]:
    payload = dict(fields)
    payload["outcome"] = outcome
    return summarize_status(event, **payload)


def summarize_evaluation_success(event: str, **fields: Any) -> dict[str, Any]:
    return _summarize_evaluation_outcome(event, outcome="success", **fields)


def summarize_evaluation_partial_success(event: str, **fields: Any) -> dict[str, Any]:
    return _summarize_evaluation_outcome(event, outcome="partial_success", **fields)


def summarize_evaluation_failure(event: str, **fields: Any) -> dict[str, Any]:
    return _summarize_evaluation_outcome(event, outcome="failure", **fields)


def summarize_evaluation_event(event: str, **fields: Any) -> dict[str, Any]:
    outcome = str(fields.get("outcome") or "")
    if outcome == "partial_success":
        return summarize_evaluation_partial_success(event, **{k: v for k, v in fields.items() if k != "outcome"})
    if outcome == "failure":
        return summarize_evaluation_failure(event, **{k: v for k, v in fields.items() if k != "outcome"})
    return summarize_evaluation_success(event, **{k: v for k, v in fields.items() if k != "outcome"})
