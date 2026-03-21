from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class SchemaValidationOutcome:
    passed: bool
    status: str
    required_field_check: str
    type_check: str
    format_check: str
    completeness_check: str
    issue_summary: str | None


class SchemaValidationService:
    required_fields = {"service_request_id", "requested_at", "category"}

    def validate(self, records: list[dict[str, Any]]) -> SchemaValidationOutcome:
        if not records:
            return SchemaValidationOutcome(
                passed=False,
                status="rejected",
                required_field_check="failed",
                type_check="failed",
                format_check="failed",
                completeness_check="failed",
                issue_summary="No records supplied for validation.",
            )

        for index, record in enumerate(records):
            missing = sorted(self.required_fields.difference(record.keys()))
            if missing:
                return SchemaValidationOutcome(
                    passed=False,
                    status="rejected",
                    required_field_check="failed",
                    type_check="passed",
                    format_check="passed",
                    completeness_check="failed",
                    issue_summary=f"Record {index} missing fields: {', '.join(missing)}.",
                )

            blank_fields = [field for field in sorted(self.required_fields) if record.get(field) in (None, "", [])]
            if blank_fields:
                return SchemaValidationOutcome(
                    passed=False,
                    status="rejected",
                    required_field_check="passed",
                    type_check="passed",
                    format_check="passed",
                    completeness_check="failed",
                    issue_summary=f"Record {index} has blank required fields: {', '.join(blank_fields)}.",
                )

            if not all(isinstance(record.get(field), str) for field in self.required_fields):
                return SchemaValidationOutcome(
                    passed=False,
                    status="rejected",
                    required_field_check="passed",
                    type_check="failed",
                    format_check="passed",
                    completeness_check="passed",
                    issue_summary=f"Record {index} has invalid field types.",
                )

            try:
                datetime.fromisoformat(str(record["requested_at"]).replace("Z", "+00:00"))
            except ValueError:
                return SchemaValidationOutcome(
                    passed=False,
                    status="rejected",
                    required_field_check="passed",
                    type_check="passed",
                    format_check="failed",
                    completeness_check="passed",
                    issue_summary=f"Record {index} has invalid requested_at format.",
                )

        return SchemaValidationOutcome(
            passed=True,
            status="passed",
            required_field_check="passed",
            type_check="passed",
            format_check="passed",
            completeness_check="passed",
            issue_summary=None,
        )
