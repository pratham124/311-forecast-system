from __future__ import annotations


class ForecastBucketService:
    def build_buckets(self, generated_forecast: dict[str, object]) -> tuple[list[dict[str, object]], str]:
        geography_scope = str(generated_forecast["geography_scope"])
        buckets = list(generated_forecast["buckets"])
        if geography_scope == "category_only":
            for bucket in buckets:
                bucket["geography_key"] = None
        return buckets, geography_scope
