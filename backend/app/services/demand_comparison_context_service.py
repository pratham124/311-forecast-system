from __future__ import annotations

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.schemas.demand_comparison_api import DemandComparisonContext


class DemandComparisonContextService:
    def __init__(self, cleaned_dataset_repository: CleanedDatasetRepository, source_name: str) -> None:
        self.cleaned_dataset_repository = cleaned_dataset_repository
        self.source_name = source_name

    def get_context(self) -> DemandComparisonContext:
        return DemandComparisonContext(
            serviceCategories=self.cleaned_dataset_repository.list_current_categories(self.source_name),
            geographyLevels=[],
            geographyOptions={},
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
