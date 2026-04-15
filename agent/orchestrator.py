from __future__ import annotations
import json
import time
from datetime import datetime, timezone

from openai import OpenAI

from .models import (
    BrandConfig, BrandReport, ProductItem, TrendAttributes, TrendReport
)
from .tools import FirecrawlTools, TOOL_DEFINITIONS
from .aggregator import TrendAggregator
from .renderer import HTMLRenderer


SYSTEM_PROMPT = """You are a fashion trend intelligence agent. Your job is to crawl apparel brand websites and extract structured fashion trend data for a trend report.

You have two tools:
1. search_brand_products — search the web for product page URLs on a brand's website
2. scrape_product_page — scrape a URL to get its title, product images, and page content as markdown

Your workflow for each brand:
1. Use search_brand_products to find 10-15 product page URLs (try different queries like "dress new arrivals 2025", "top summer collection", "skirt linen" to get diverse products)
2. Scrape each promising URL with scrape_product_page
3. From the scraped markdown, analyze the product and extract trend attributes
4. Skip any 404 pages, category listing pages, or non-product pages — focus on individual product pages
5. If a search returns mostly category pages, try more specific search queries

After scraping and analyzing all products, output a JSON array where each element is:
{
  "url": "the product page URL",
  "brand": "brand name",
  "product_name": "full product name",
  "category": "dress|top|skirt|jacket|trousers|jumpsuit|co-ord",
  "price": "price with currency or null",
  "image_urls": ["image URLs from the scrape results"],
  "trends": {
    "fit": "slim|oversized|relaxed|tailored|boxy|regular",
    "silhouette": "A-line|bodycon|boxy|straight|flared|wrap|shift",
    "fabric": "primary material name",
    "prints_patterns": ["list of prints/patterns"],
    "colors": ["actual color names, not codes"],
    "length": "mini|midi|maxi|cropped|knee-length",
    "neckline": "V-neck|crew|off-shoulder|square|halter|round|strapless",
    "sleeve_style": "sleeveless|short|long|puff|balloon|cap",
    "details": ["cutout|ruching|pleats|buttons|embroidery|pockets"],
    "season": "SS25|AW25|Resort 2025"
  }
}

IMPORTANT:
- Always include image_urls from the scrape results — these are critical for the visual report
- Use real color names (e.g. "ivory", "cobalt blue"), not color codes (not "060" or "700")
- If a trend attribute can't be determined from the page content, set it to null
- Output ONLY the JSON array at the end — no extra text, no markdown fences"""


class TrendAgent:
    def __init__(
        self,
        brands: list[BrandConfig],
        firecrawl_api_key: str,
        openai_api_key: str,
        model_name: str = "gpt-4o",
        output_path: str = "output/trend_report.html",
    ):
        self.brands = brands
        self.fc_tools = FirecrawlTools(api_key=firecrawl_api_key)
        self.openai = OpenAI(api_key=openai_api_key)
        self.model_name = model_name
        self.aggregator = TrendAggregator()
        self.renderer = HTMLRenderer()
        self.output_path = output_path

    def run(self) -> TrendReport:
        print(f"\n{'='*60}")
        print("Fashion Trend Intelligence Agent")
        print(f"{'='*60}\n")

        brand_reports: list[BrandReport] = []

        for brand_config in self.brands:
            print(f"[{brand_config.name}] Starting crawl...")
            report = self._crawl_brand(brand_config)
            brand_reports.append(report)
            print(f"[{brand_config.name}] Done — {len(report.products)} products extracted\n")

        print("[Aggregator] Computing cross-brand trends...")
        cross_brand = self.aggregator.cross_brand_synthesis(brand_reports)

        trend_report = TrendReport(
            brand_reports=brand_reports,
            cross_brand_trends=cross_brand,
            generated_at=datetime.now(timezone.utc).isoformat(),
            html_output_path=self.output_path,
        )

        print("[Renderer] Generating HTML report...")
        html = self.renderer.render(trend_report)
        self.renderer.save(html, self.output_path)

        return trend_report

    def _crawl_brand(self, config: BrandConfig) -> BrandReport:
        now = datetime.now(timezone.utc).isoformat()
        products = self._agentic_loop(config)
        dominant = self.aggregator.aggregate_brand(products)

        return BrandReport(
            brand_name=config.name,
            domain=config.domain,
            products=products,
            dominant_trends=dominant,
            crawled_at=now,
        )

    def _agentic_loop(self, config: BrandConfig) -> list[ProductItem]:
        categories_str = ", ".join(config.categories) if config.categories else "all women's"
        user_message = (
            f"Analyze the {config.name} website ({config.domain}) for current fashion trends.\n"
            f"Target categories: {categories_str}\n"
            f"Extract trend data for up to {config.max_pages} products.\n"
            f"Brand name to use in output: {config.name}\n"
            f"Be resourceful with search queries — try different category-specific queries "
            f"to find individual product pages, not just category listing pages."
        )

        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]
        max_iterations = 80
        iteration = 0

        print(f"  [agent] Starting agentic loop for {config.name}...")

        while iteration < max_iterations:
            iteration += 1

            response = self.openai.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                temperature=0.2,
            )

            choice = response.choices[0]
            msg = choice.message

            # Append the assistant message
            messages.append(msg.to_dict() if hasattr(msg, "to_dict") else {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [tc.to_dict() if hasattr(tc, "to_dict") else {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                } for tc in msg.tool_calls] if msg.tool_calls else None,
            })

            # If no tool calls, the agent is done
            if not msg.tool_calls:
                print(f"  [agent] Done after {iteration} iterations")
                return self._parse_products(msg.content or "", config.name)

            # Execute each tool call
            for tc in msg.tool_calls:
                tool_name = tc.function.name
                try:
                    tool_input = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    tool_input = {}

                print(f"  [tool] {tool_name}({json.dumps(tool_input)[:100]}...)")

                try:
                    result_str = self.fc_tools.dispatch(tool_name, tool_input)
                except Exception as e:
                    result_str = json.dumps({"error": str(e)})

                time.sleep(1)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_str,
                })

        print(f"  [agent] Reached max iterations ({max_iterations})")
        for m in reversed(messages):
            if m.get("role") == "assistant" and m.get("content"):
                return self._parse_products(m["content"], config.name)
        return []

    def _parse_products(self, content: str, brand_name: str) -> list[ProductItem]:
        now = datetime.now(timezone.utc).isoformat()
        raw_text = content.strip()

        # Strip markdown code fences
        if raw_text.startswith("```"):
            lines = raw_text.splitlines()
            raw_text = "\n".join(
                l for l in lines if not l.strip().startswith("```")
            ).strip()

        if not raw_text:
            return []

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            start = raw_text.find("[")
            end = raw_text.rfind("]") + 1
            if start != -1 and end > start:
                try:
                    data = json.loads(raw_text[start:end])
                except json.JSONDecodeError:
                    print(f"  [parser] Could not parse JSON for {brand_name}")
                    return []
            else:
                print(f"  [parser] No JSON array found for {brand_name}")
                return []

        if not isinstance(data, list):
            data = [data]

        TREND_KEYS = set(TrendAttributes.model_fields.keys())

        products = []
        for item in data:
            if not isinstance(item, dict):
                continue
            try:
                nested = item.get("trends") or {}
                trend_src = {**nested, **{k: v for k, v in item.items() if k in TREND_KEYS}}

                product = ProductItem(
                    url=item.get("url", ""),
                    brand=item.get("brand", brand_name),
                    product_name=item.get("product_name", "Unknown Product"),
                    category=item.get("category"),
                    price=item.get("price"),
                    image_urls=item.get("image_urls") or [],
                    trends=TrendAttributes(**{
                        k: v for k, v in trend_src.items()
                        if k in TREND_KEYS and v is not None
                    }),
                    scraped_at=now,
                )
                products.append(product)
            except Exception as e:
                print(f"  [parser] Skipping malformed product: {e}")

        return products
