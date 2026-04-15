from __future__ import annotations
import json
import re
from firecrawl import Firecrawl


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_brand_products",
            "description": (
                "Search the web for product page URLs on a fashion brand's website. "
                "Returns a list of URLs found via Google. Use this first to discover pages to scrape."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "The brand domain e.g. zara.com, bershka.com, hm.com"
                    },
                    "query": {
                        "type": "string",
                        "description": "Additional search terms to find specific products e.g. 'dress new arrivals', 'linen top summer 2025'"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max URLs to return (default 10)"
                    }
                },
                "required": ["domain"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_product_page",
            "description": (
                "Scrape a fashion product page. Returns the page title, product image URLs "
                "(og:image + images from page), and the page content as markdown. "
                "Use this on URLs discovered by search_brand_products. "
                "Analyze the returned markdown to extract trend attributes like fit, fabric, silhouette, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL to scrape"
                    }
                },
                "required": ["url"]
            }
        }
    }
]


class FirecrawlTools:
    def __init__(self, api_key: str):
        self.fc = Firecrawl(api_key=api_key)

    def search_brand_products(self, domain: str, query: str = "", limit: int = 10) -> list[str]:
        bare = domain.replace("www.", "").replace("www2.", "")
        search_query = f"site:{bare} women {query or 'new arrivals 2025 dress OR top OR skirt OR jacket'}"
        try:
            result = self.fc.search(search_query, limit=limit, ignore_invalid_urls=True)
            urls = []
            for item in (result.web or []):
                if hasattr(item, "url") and item.url:
                    urls.append(item.url)
            return urls
        except Exception as e:
            print(f"    [search error] {e}")
            return []

    def scrape_product_page(self, url: str) -> dict:
        try:
            result = self.fc.scrape(url, formats=["markdown"])
            meta = result.metadata

            images = []
            if meta and meta.og_image:
                images.append(meta.og_image)

            md = result.markdown or ""
            md_images = re.findall(r'!\[.*?\]\((https?://[^\s\)]+)\)', md)
            for img_url in md_images:
                if img_url not in images:
                    images.append(img_url)

            title = ""
            if meta:
                title = meta.title or meta.og_title or ""

            return {
                "title": title,
                "image_urls": images[:5],
                "markdown": md[:4000],
            }
        except Exception as e:
            print(f"    [scrape error] {e}")
            return {"title": "", "image_urls": [], "markdown": ""}

    def dispatch(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "search_brand_products":
            urls = self.search_brand_products(
                domain=tool_input["domain"],
                query=tool_input.get("query", ""),
                limit=tool_input.get("limit", 10),
            )
            return json.dumps({"urls": urls, "count": len(urls)})

        elif tool_name == "scrape_product_page":
            data = self.scrape_product_page(url=tool_input["url"])
            return json.dumps(data)

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
