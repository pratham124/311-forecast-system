from __future__ import annotations

import logging
from typing import Any

from app.core.logging import sanitize_mapping


class IngestionLoggingService:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    def log(self, event: str, **fields: Any) -> dict[str, Any]:
        payload = sanitize_mapping(fields)
        self.logger.info("%s %s", event, payload)
        return payload
