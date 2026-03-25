from __future__ import annotations


class WeeklyForecastBucketService:
    def build_buckets(self, generated: dict[str, object]) -> tuple[list[dict[str, object]], str]:
        return list(generated["buckets"]), str(generated["geography_scope"])
