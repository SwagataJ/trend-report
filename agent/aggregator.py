from collections import Counter
from .models import ProductItem, BrandReport


class TrendAggregator:
    TREND_FIELDS = [
        "fit", "silhouette", "fabric", "length", "neckline", "sleeve_style"
    ]
    LIST_FIELDS = ["prints_patterns", "colors", "details"]

    def aggregate_brand(self, products: list[ProductItem]) -> dict:
        dominant: dict = {}

        for field in self.TREND_FIELDS:
            counter: Counter = Counter()
            for p in products:
                val = getattr(p.trends, field, None)
                if val:
                    counter[val.lower().strip()] += 1
            if counter:
                dominant[field] = dict(counter.most_common(5))

        for field in self.LIST_FIELDS:
            counter = Counter()
            for p in products:
                vals = getattr(p.trends, field, [])
                for v in vals:
                    if v:
                        counter[v.lower().strip()] += 1
            if counter:
                dominant[field] = dict(counter.most_common(5))

        return dominant

    def cross_brand_synthesis(self, reports: list[BrandReport]) -> dict:
        merged: dict[str, Counter] = {}

        for report in reports:
            for field, counts in report.dominant_trends.items():
                if field not in merged:
                    merged[field] = Counter()
                for val, count in counts.items():
                    merged[field][val] += count

        return {
            field: dict(counter.most_common(10))
            for field, counter in merged.items()
        }
