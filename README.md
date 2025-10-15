# Brave Search Extractor

Small, async-friendly toolkit to query the Brave Search API and extract readable article text using Mozilla Readability — with optional auto‑archiving of results to JSON files.

This README reflects the current implementation in the repository and is safe to publish publicly (no secrets included). Replace the API key locally before running.

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

Note: There is no `multi_search.py` in this repo. The README is accurate to the code.

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

Logging tip for your own scripts:

```python
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
```

## Security

- Never commit real API keys. `search_config.yaml` is Git‑ignored in this repo.
- Review any generated data under `archives/` before sharing.

## License

MIT — see `LICENSE`.

## Roadmap (nice to have)

- Honor `default_params` from config automatically
- Global search/extraction indexes and URL de‑duplication
- Additional search endpoints and richer result fields
