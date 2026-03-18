from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationResult:
    passed: bool
    reason: str | None = None


class DatasetValidationService:
    required_fields = {"service_request_id", "requested_at", "category"}

    def validate(self, records: list[dict[str, Any]]) -> ValidationResult:
        if not records:
            return ValidationResult(False, "No records supplied for validation")
        for index, record in enumerate(records):
            missing = self.required_fields.difference(record.keys())
            if missing:
                return ValidationResult(False, f"Record {index} missing fields: {', '.join(sorted(missing))}")
            blank_fields = [
                field
                for field in self.required_fields
                if record.get(field) in (None, "", [])
            ]
            if blank_fields:
                return ValidationResult(False, f"Record {index} has blank required fields: {', '.join(sorted(blank_fields))}")
        return ValidationResult(True, None)
