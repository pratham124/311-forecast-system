from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from typing import Any

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.schemas.historical_demand import HistoricalDemandContextRead


KNOWN_GEOGRAPHY_LEVELS = ("neighbourhood", "ward", "district", "geography_key")
MIN_RELIABLE_GEOGRAPHY_RATIO = 0.9


@dataclass
class HistoricalContextService:
    cleaned_dataset_repository: CleanedDatasetRepository
    source_name: str

    def get_context(self) -> HistoricalDemandContextRead:
        dataset = self.cleaned_dataset_repository.get_current_approved_dataset(self.source_name)
        categories = self.cleaned_dataset_repository.list_current_categories(self.source_name)
        dataset_label = dataset.dataset_version_id if dataset is not None else "none"
        return HistoricalDemandContextRead(
            serviceCategories=categories,
            supportedGeographyLevels=[],
            summary=f"Using approved cleaned dataset {dataset_label} for historical demand exploration.",
        )

    def require_approved_dataset_id(self) -> str:
        dataset = self.cleaned_dataset_repository.get_current_approved_dataset(self.source_name)
        if dataset is None:
            raise LookupError("No approved cleaned dataset is available")
        return dataset.dataset_version_id

    def get_supported_geography_levels(self) -> list[str]:
        records = self.cleaned_dataset_repository.list_current_cleaned_records(self.source_name)
        return self.supported_geography_levels(records)

    def supported_geography_levels(self, records: list[dict[str, Any]]) -> list[str]:
        if not records:
            return []
        reliable_levels: list[str] = []
        for level in KNOWN_GEOGRAPHY_LEVELS:
            populated = 0
            distinct_values: Counter[str] = Counter()
            for record in records:
                value = self.extract_geography_value(record, level)
                if value:
                    populated += 1
                    distinct_values[value] += 1
            if populated == 0:
                continue
            if populated / len(records) >= MIN_RELIABLE_GEOGRAPHY_RATIO and len(distinct_values) >= 2:
                reliable_levels.append(level)
        return reliable_levels

    def normalize_record(self, record: dict[str, Any]) -> dict[str, Any]:
        if "record_payload" in record and isinstance(record["record_payload"], str):
            try:
                payload = json.loads(record["record_payload"])
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, dict):
                merged = dict(payload)
                merged.setdefault("geography_key", record.get("geography_key"))
                return merged
        return record

    def extract_geography_value(self, record: dict[str, Any], geography_level: str) -> str | None:
        normalized = self.normalize_record(record)
        raw = normalized.get(geography_level)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
        return None
