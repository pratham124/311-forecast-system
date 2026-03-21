from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.duplicate_analysis_service import DuplicateGroupCandidate


@dataclass
class DuplicateResolutionRecord:
    group_key: str
    source_record_count: int
    resolution_status: str
    cleaned_record: dict[str, Any]
    resolution_summary: str


class DuplicateResolutionService:
    def resolve(
        self,
        records: list[dict[str, Any]],
        duplicate_groups: list[DuplicateGroupCandidate],
    ) -> tuple[list[dict[str, Any]], list[DuplicateResolutionRecord]]:
        grouped_keys = {group.group_key for group in duplicate_groups}
        cleaned_records = [record.copy() for record in records if str(record.get("service_request_id", "")) not in grouped_keys]
        resolutions: list[DuplicateResolutionRecord] = []

        for group in duplicate_groups:
            cleaned = self._merge_records(group.records)
            resolutions.append(
                DuplicateResolutionRecord(
                    group_key=group.group_key,
                    source_record_count=len(group.records),
                    resolution_status="consolidated",
                    cleaned_record=cleaned,
                    resolution_summary=f"Consolidated {len(group.records)} records into one cleaned record.",
                )
            )
            cleaned_records.append(cleaned)

        return cleaned_records, resolutions

    def _merge_records(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        all_keys = sorted({key for record in records for key in record.keys()})
        for key in all_keys:
            values = [record.get(key) for record in records if record.get(key) not in (None, "", [])]
            merged[key] = values[0] if values else records[0].get(key)
        return merged
