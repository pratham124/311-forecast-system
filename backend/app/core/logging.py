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
