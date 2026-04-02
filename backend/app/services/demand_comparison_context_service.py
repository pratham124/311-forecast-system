from __future__ import annotations

from collections import defaultdict

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.schemas.demand_comparison_api import DemandComparisonContext


class DemandComparisonContextService:
    SUPPORTED_LEVELS = ("ward", "district", "neighbourhood", "geography_key")

    def __init__(self, cleaned_dataset_repository: CleanedDatasetRepository, source_name: str) -> None:
        self.cleaned_dataset_repository = cleaned_dataset_repository
        self.source_name = source_name

    def get_context(self) -> DemandComparisonContext:
        records = self.cleaned_dataset_repository.list_current_cleaned_records(self.source_name)

        categories: set[str] = set()
        geography_options: dict[str, set[str]] = defaultdict(set)
        for record in records:
            category = str(record.get("category", "")).strip()
            if category:
                categories.add(category)
            for level in self.SUPPORTED_LEVELS:
                value = self.extract_geography_value(record, level)
                if value:
                    geography_options[level].add(value)

        levels = sorted(geography_options.keys())

        return DemandComparisonContext(
            serviceCategories=sorted(categories),
            geographyLevels=levels,
            geographyOptions={level: sorted(values) for level, values in geography_options.items()},
            summary="Comparison filters are sourced from the approved cleaned dataset lineage.",
        )

    @staticmethod
    def extract_geography_value(record: dict[str, object], geography_level: str | None) -> str | None:
        if geography_level is None:
            return None
        aliases = {
            "ward": ("ward",),
            "district": ("district",),
            "neighbourhood": ("neighbourhood", "neighborhood"),
            "geography_key": ("geography_key", "ward", "district", "neighbourhood", "neighborhood"),
        }
        for key in aliases.get(geography_level, (geography_level,)):
            value = record.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

