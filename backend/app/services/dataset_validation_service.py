from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.schema_validation_service import SchemaValidationService


@dataclass
class ValidationResult:
    passed: bool
    reason: str | None = None


class DatasetValidationService:
    def __init__(self) -> None:
        self.schema_validation_service = SchemaValidationService()

    def validate(self, records: list[dict[str, Any]]) -> ValidationResult:
        result = self.schema_validation_service.validate(records)
        return ValidationResult(passed=result.passed, reason=result.issue_summary)
