import os
from agent.models import BrandConfig

FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL_NAME = os.environ.get("OPENAI_MODEL", "gpt-4o")

BRANDS = [
    BrandConfig(
        name="Zara",
        domain="zara.com",
        new_arrivals_path="/en/in/woman",
        categories=["dresses", "tops", "trousers", "skirts"],
        max_pages=20,
    ),
    BrandConfig(
        name="Bershka",
        domain="bershka.com",
        new_arrivals_path="/en/woman",
        categories=["dresses", "tops", "jeans", "skirts"],
        max_pages=20,
    ),
    BrandConfig(
        name="H&M",
        domain="hm.com",
        new_arrivals_path="/en_in/women/new-arrivals",
        categories=["dresses", "tops", "trousers", "skirts"],
        max_pages=20,
    ),
]

OUTPUT_PATH = "output/trend_report.html"
