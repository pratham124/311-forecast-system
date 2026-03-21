from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DuplicateGroupCandidate:
    group_key: str
    records: list[dict[str, Any]]


@dataclass
class DuplicateAnalysisOutcome:
    status: str
    total_record_count: int
    duplicate_record_count: int
    duplicate_percentage: float
    threshold_percentage: float
    duplicate_group_count: int
    groups: list[DuplicateGroupCandidate]
    issue_summary: str | None


class DuplicateAnalysisService:
    def analyze(
        self,
        records: list[dict[str, Any]],
        threshold_percentage: float,
    ) -> DuplicateAnalysisOutcome:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for record in records:
            group_key = str(record.get("service_request_id", ""))
            grouped.setdefault(group_key, []).append(record)

        duplicate_groups = [
            DuplicateGroupCandidate(group_key=group_key, records=group_records)
            for group_key, group_records in grouped.items()
            if len(group_records) > 1
        ]
        duplicate_record_count = sum(len(group.records) - 1 for group in duplicate_groups)
        total_record_count = len(records)
        duplicate_percentage = 0.0
        if total_record_count > 0:
            duplicate_percentage = round((duplicate_record_count / total_record_count) * 100, 2)

        status = "passed"
        issue_summary = None
        if duplicate_percentage > threshold_percentage:
            status = "review_needed"
            issue_summary = (
                f"Duplicate percentage {duplicate_percentage:.2f}% exceeded threshold "
                f"{threshold_percentage:.2f}%."
            )

        return DuplicateAnalysisOutcome(
            status=status,
            total_record_count=total_record_count,
            duplicate_record_count=duplicate_record_count,
            duplicate_percentage=duplicate_percentage,
            threshold_percentage=threshold_percentage,
            duplicate_group_count=len(duplicate_groups),
            groups=duplicate_groups,
            issue_summary=issue_summary,
        )
