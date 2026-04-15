# Fashion Trend Intelligence Agent — High Level Design (HLD)

## 1. System Overview

An agentic pipeline that crawls apparel brand websites (Zara, Bershka, H&M), extracts structured fashion trend data (fit, fabric, silhouette, print, pattern, etc.), and renders a visual HTML report with product images.

The agent uses **Claude** as the reasoning core and **Firecrawl** as the web access layer. It follows a **ReAct** (Reason + Act) pattern: plan → crawl → extract → aggregate → render.

---

## 2. High-Level Architecture

```mermaid
flowchart TB
    subgraph INPUT["Input Layer"]
        UI["User / Config\n(brands, categories, limits)"]
    end

    subgraph AGENT["Agent Orchestrator (Claude claude-sonnet-4-6)"]
        direction TB
        PLAN["Planner\n(decides which URLs to crawl)"]
        TOOL["Tool Router\n(dispatches to Firecrawl tools)"]
        REASON["Reasoner\n(aggregates + synthesizes trends)"]
    end

    subgraph TOOLS["Tool Layer"]
        FC_MAP["Firecrawl: map()\n(discover product URLs)"]
        FC_SCRAPE["Firecrawl: scrape()\n(extract page content + images)"]
        FC_EXTRACT["Firecrawl: extract()\n(schema-guided LLM extraction)"]
    end

    subgraph DATA["Data Layer"]
        RAW["Raw Crawl Cache\n(JSON per brand)"]
        STRUCTURED["Structured Trend Data\n(ProductItem + TrendSignal)"]
    end

    subgraph OUTPUT["Output Layer"]
        HTML["Trend Report\n(HTML + product images)"]
    end

    UI --> AGENT
    AGENT --> TOOLS
    TOOLS --> DATA
    DATA --> AGENT
    AGENT --> OUTPUT
```

---

## 3. Component Responsibilities

| Component | Responsibility |
|---|---|
| **Agent Orchestrator** | Agentic loop — plan, call tools, observe results, iterate until done |
| **Firecrawl `map()`** | Discover all product/collection URLs under a brand domain |
| **Firecrawl `scrape()`** | Pull full page markdown + image URLs from product pages |
| **Firecrawl `extract()`** | Schema-guided structured extraction of trend attributes via LLM |
| **Trend Aggregator** | Cross-brand synthesis — identify dominant trends by frequency |
| **HTML Renderer** | Jinja2 template → styled report with product images and trend badges |

---

## 4. Technology Stack

```mermaid
flowchart LR
    A["Python 3.12"] --> B["firecrawl-py\n(crawl + extract)"]
    A --> C["anthropic SDK\n(Claude as agent brain)"]
    A --> D["Jinja2\n(HTML rendering)"]
    A --> E["Pydantic\n(data models + validation)"]
    B --> F["Firecrawl Cloud API"]
    C --> G["Anthropic API"]
```

| Library | Version | Purpose |
|---|---|---|
| `firecrawl-py` | latest | Web crawling, scraping, structured extraction |
| `anthropic` | latest | Claude claude-sonnet-4-6 as agent reasoning core |
| `pydantic` | v2 | Data model validation and schema generation |
| `jinja2` | latest | HTML report templating |
| `asyncio` | stdlib | Concurrent brand crawling |

---

## 5. End-to-End Data Flow

```mermaid
sequenceDiagram
    participant User
    participant Agent as Agent Orchestrator
    participant Firecrawl
    participant Aggregator
    participant Renderer

    User->>Agent: run(brands=["zara", "bershka", "hm"])

    loop For each brand
        Agent->>Firecrawl: map_brand_urls(domain, limit=50)
        Firecrawl-->>Agent: [product_url_1, ..., url_N]

        loop Agentic tool-call loop (ReAct)
            Agent->>Agent: reason — which URL to process next
            Agent->>Firecrawl: extract_trends(url, TrendSchema)
            Firecrawl-->>Agent: TrendAttributes (structured JSON)
            Agent->>Agent: store ProductItem, decide continue/stop
        end
    end

    Agent->>Aggregator: aggregate per brand + cross-brand synthesis
    Aggregator-->>Agent: dominant trends (ranked by frequency)

    Agent->>Renderer: render(TrendReport)
    Renderer-->>Agent: trend_report.html

    Agent-->>User: path to HTML report
```

---

## 6. HTML Output Structure

```mermaid
flowchart TD
    HTML["trend_report.html"]
    HTML --> H["Header — title, date, brands covered"]
    HTML --> GLOBAL["Global Trends Section\ncross-brand top trends with frequency counts"]
    HTML --> BRANDS["Per-Brand Sections"]
    BRANDS --> B1["Zara\n├─ dominant trend chips\n└─ product grid"]
    BRANDS --> B2["Bershka\n├─ dominant trend chips\n└─ product grid"]
    BRANDS --> B3["H&M\n├─ dominant trend chips\n└─ product grid"]
    B1 & B2 & B3 --> CARD["Product Card\n├─ product image\n├─ product name + price\n└─ trend badges\n   fit · silhouette · fabric · print · pattern · color"]
```

---

## 7. Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Agent brain | Claude claude-sonnet-4-6 via tool use API | Best structured extraction + multi-step reasoning |
| Extraction strategy | `firecrawl.extract()` with Pydantic schema | Avoids brittle CSS selectors, handles JS-rendered pages |
| URL discovery | `firecrawl.map()` scoped to `/new-arrivals` or `/woman` | Targeted crawl, avoids crawling entire site |
| Trend aggregation | Counter-based frequency per attribute | Simple, interpretable, no extra ML dependency |
| HTML rendering | Jinja2 template | Clean separation of data logic and presentation |
| Concurrency | `asyncio` + batched scraping per brand | Respects rate limits while maximising speed |

---

## 8. System Constraints & Boundaries

- **Scope**: New arrivals and current season collections only — not full site crawl
- **Rate limiting**: Max 50 product pages per brand per run (configurable)
- **Images**: Referenced by URL in HTML — not downloaded locally
- **Authentication**: No login required; only publicly accessible product pages
- **Output**: Single self-contained HTML file written to `output/trend_report.html`
