# Brave Search Extractor

Small, async-friendly toolkit to query the Brave Search API and extract readable article text using Mozilla Readability — with optional auto‑archiving of results to JSON files.

## Executive Summary

Brave Search Extractor helps you: (1) query Brave Search efficiently, (2) fetch 10–20 links per request, and (3) extract readable article text locally. This design keeps your unit cost very low (often 1/8–1/5 of hosted alternatives for typical workflows) while supporting high concurrency.

## Features

- Async Brave Search client (`aiohttp`)
- Simple rate limiting (requests/second)
- Readability‑based content extraction (`readability-lxml` + `lxml`)
- Batch extraction with bounded concurrency
- Optional auto‑archiving to `archives/` (daily search logs and extracted content files)

## Project Layout

```
search/
├── brave_client.py         # Brave Search API client
├── content_extractor.py    # Readability-based content extractor
├── archive_manager.py      # JSON archive writer
├── config_loader.py        # Configuration loader
├── demo.py                 # End-to-end demo script
├── search_config.yaml      # Local config (ignored by Git)
└── archives/               # Auto-generated archives directory
```

Note: The project ships a small demo and a minimal public API. No secrets are committed; use the example config to create your local `search_config.yaml`.

## Requirements

- Python 3.9+ (tested on 3.9.6 and newer)
- Install dependencies:

```
pip install -r requirements.txt
```

## Configuration

Copy the example config and set your Brave API key (do not commit the real key):

```
cp search_config.example.yaml search_config.yaml
# Edit search_config.yaml and set brave_search.api_key
```

Used configuration keys (from `search_config.yaml`):

- `brave_search.api_key` (required)
- `brave_search.base_url` (optional, default: `https://api.search.brave.com/res/v1`)
- `brave_search.rate_limit.requests_per_second` (optional, default: `1.0`)
- `brave_search.enable_archive` (default: `true`)
- `brave_search.archive_path` (default: `./archives`)

## Quick Start

Example usage (Python):

```python
import asyncio
from search.brave_client import BraveSearchClient
from search.content_extractor import ContentExtractor

async def main():
    client = BraveSearchClient()
    results = await client.search("Bitcoin news", count=10)

    extractor = ContentExtractor()
    content = await extractor.extract(results[0].url)
    print(content.title)
    print(content.text[:400])

asyncio.run(main())
```

Run the demo (single way):

- From the repo root: `python run_demo.py "bitcoin whale"`

### API Overview

Public types exposed by the package:

- `search.brave_client.BraveSearchClient` — async client for Brave Search.
  - Method `search(query: str, **params) -> List[SearchResult]`.
  - Common params: `count` (default 10), `offset` (0–9). Rate‑limited via a simple client‑side limiter.

- `search.brave_client.SearchResult` — structure of a search result.
  - Fields: `url`, `title`, `description`, `snippet`, `age?`, `extra_snippets?`, `source_type?` (e.g., `web`/`news`).

- `search.content_extractor.ContentExtractor` — async extractor using Readability.
  - Method `extract(url: str) -> ExtractedContent` — returns one result.
  - Method `extract_batch(urls: List[str], max_concurrent: int = 5) -> List[ExtractedContent]` — bounded concurrency; may auto‑archive.

- `search.content_extractor.ExtractedContent` — structure of extracted content.
  - Fields: `url`, `title?`, `text?`, `success` (bool), `error?`.

## Cost & Throughput Advantages

The project is optimized for a common workflow: “fetch 10–20 links per search, then extract the article text ourselves.” Under this pattern, Brave Search + self‑hosted extraction achieves excellent unit economics and high throughput.

### TL;DR

For “1 search returning 10–20 links + extract 10 pages,” Brave typically costs about 1/8–1/5 of Tavily (PAYG), while offering higher peak RPS and larger monthly ceilings, which makes it well‑suited for high concurrency and scale.

### Key Metrics at a Glance (as of 2025‑10; see vendor docs for details)

| Dimension | Brave Free | Brave Base | Brave Pro | Tavily (Free / PAYG) |
| --- | --- | --- | --- | --- |
| Unit price | $0 / 1,000 requests | $3 / 1,000 requests | $5 / 1,000 requests | Free: 1,000 credits / month; $0.008 / credit (PAYG) |
| Peak rate | 1 rps | 20 rps | 50 rps | Dev: 100 rpm (≈ 1.67 rps); Prod: 1,000 rpm (≈ 16.7 rps) |
| Monthly cap | 2,000 / month | 20M / month | Unlimited | Varies by plan; Free 1,000 credits / month |
| Results per request (`count`) | Up to 20 | Up to 20 | Up to 20 | `max_results` typically up to 20 (billed by `search_depth`) |
| Pagination offset | Up to 9 | Up to 9 | Up to 9 | — |
| Billing granularity | Per request | Per request | Per request | Per credit: `search basic = 1`, `advanced = 2`; `extract/crawl` = 1 or 2 credits per 5 successful URLs |

Sources: Brave pricing and API docs; Tavily pricing, rate limits, and endpoint docs.

### Concrete Workflow Cost Example

Scenario: 1 search returns 10 links; we extract 10 pages ourselves.

- Brave path (we only pay for search; extraction is self‑hosted):
  - Base: 1 request = $0.003 ($3 / 1,000)
  - Pro: 1 request = $0.005 ($5 / 1,000)
  - Note: one request can return 10–20 links and still counts as a single request.

- Tavily path (use Tavily for search + hosted extraction):
  - basic: `search = 1 credit`; `extract basic (10 URLs) = 2 credits` (1 credit per 5 successful URLs) → total `3 credits × $0.008 = $0.024`
  - advanced: `search advanced = 2 credits`; `extract advanced (10 URLs) = 4 credits` → total `6 credits × $0.008 = $0.048`

Cost ratio (lower is better):

- Brave Base vs Tavily basic: `$0.003 / $0.024 ≈ 12.5%` (≈ 1/8). Pro vs basic: `≈ 1/4.8`.
- Brave Base vs Tavily advanced: `$0.003 / $0.048 ≈ 6.25%` (≈ 1/16). Pro vs advanced: `≈ 1/9.6`.

These calculations follow the vendors’ published billing models and do not include network jitter or retries. Always validate against the latest pricing.

### Throughput & Scalability (single API key)

- Brave: Free `1 rps` / `2,000 per month`; Base `20 rps` / `20M per month`; Pro `50 rps` / `unlimited per month`.
- Tavily: Dev `100 rpm` and Prod `1,000 rpm`. Good for medium‑to‑high concurrency, but peak is below Brave Pro in raw RPS.

### Executive Takeaways

1) Unit economics: For the same “1 search + extract 10 pages,” Brave is typically ≈ 1/8–1/5 the cost of Tavily PAYG; the gap widens for Tavily “advanced”.
2) Headroom: Brave offers 20–50 rps and very large monthly caps (20M/month on Base, unlimited on Pro), enabling batch and scale‑out workloads.
3) Strategy: Decouple “search” and “extraction”—use Brave for low‑cost bulk link retrieval (10–20 per request), keep extraction in‑house for cost control and throughput. Use Tavily advanced as a complementary retrieval option when needed.

Note: Pricing, limits, and features can change. Check the official vendor documentation for the latest information.

## Error Model

- `BraveSearchClient.search(...)` raises on HTTP errors (e.g., invalid key, rate limiting). Wrap calls with `try/except` as needed.
- `ContentExtractor.extract(...)` returns an `ExtractedContent` with `success=False` and a short `error` string on failure; it does not raise.
- `ContentExtractor.extract_batch(...)` aggregates results and converts per‑task exceptions into `ExtractedContent(success=False, error=...)` entries so the overall batch completes.

## Limitations

- Extraction relies on static HTML; sites that require heavy client‑side rendering or aggressive anti‑bot protections may fail or return partial text.
- Default headers use a generic desktop User‑Agent and `Accept-Language: en-US`; tune these if you target non‑English pages.
- Readability works best on article‑like pages; quality varies by site layout and markup.

## Archiving

If `enable_archive` is `true`, the code writes:

- Daily search logs: `archives/daily/YYYY-MM-DD_searches.json`
- Extraction batch index: `archives/extracted/YYYY-MM-DD_extractions.json`
- Individual extracted articles: `archives/extracted/YYYY-MM-DD_HH-MM-SS_<hash>.json`

Directories are created automatically. Files in `archives/` are ignored by Git.

## Troubleshooting

- Missing config: `Configuration file not found: search_config.yaml` → Copy the example and set your key.
- API key error: `Brave API key not configured!` → Edit `search_config.yaml` and replace the placeholder.
- ModuleNotFoundError: `No module named 'search'` → Run `python run_demo.py ...` from the repository root.
- HTTP errors (403/429/etc.): Sites may block scraping; Brave API enforces rate limits (≈1 req/s).
- Timeouts on extraction: Adjust `ContentExtractor(timeout=...)` or try again later.
- Archive disabled: If `enable_archive=false` or you instantiate `ContentExtractor(auto_archive=False)`, the demo runs but skips writing to `archives/`.

Logging tip for your own scripts:

```python
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
```

## Security

- Never commit real API keys. `search_config.yaml` is Git‑ignored; use `search_config.example.yaml` as a template.
- Review any generated data under `archives/` before sharing.

## Compliance

Use this project in accordance with websites’ Terms of Service and applicable laws. Respect robots.txt and rate limits.

## License

MIT — see `LICENSE`.

## Roadmap (nice to have)

- Honor `default_params` from config automatically
- Global search/extraction indexes and URL de‑duplication
- Additional search endpoints and richer result fields
