"""Brave Search API Client"""
import aiohttp
import asyncio
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging
from .config_loader import get_config
from .archive_manager import ArchiveManager

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Search result"""
    url: str
    title: str
    description: str
    snippet: str
    age: Optional[str] = None
    extra_snippets: Optional[List[str]] = None
    source_type: Optional[str] = None

class RateLimiter:
    """Rate limiter to control API request frequency"""
    def __init__(self, requests_per_second: float = 1.0):
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0

    async def wait_if_needed(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time()

class BraveSearchClient:
    """Brave Search API Client"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = get_config(config_path)
        brave_config = self.config.get_brave_config()

        self.api_key = self.config.get_brave_api_key()
        self.base_url = brave_config.get('base_url', 'https://api.search.brave.com/res/v1')

        rate_limit_config = brave_config.get('rate_limit', {})
        requests_per_second = rate_limit_config.get('requests_per_second', 1.0)
        self.rate_limiter = RateLimiter(requests_per_second)

        self.enable_archive = brave_config.get('enable_archive', True)
        archive_path = brave_config.get('archive_path', './archives')
        self.archive_manager = ArchiveManager(archive_path) if self.enable_archive else None

    async def search(self, query: str, **params) -> List[SearchResult]:
        """Search using Brave API (web/search endpoint)."""
        endpoint_path = 'web/search'

        await self.rate_limiter.wait_if_needed()

        search_params = {
            'q': query,
            'count': params.get('count', 10) if params else 10
        }
        if params:
            search_params.update(params)

        headers = {
            'X-Subscription-Token': self.api_key,
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip'
        }

        url = f'{self.base_url}/{endpoint_path}'

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=search_params, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()

        results: List[SearchResult] = []

        web_results = data.get('web', {}).get('results', [])
        for item in web_results:
            results.append(SearchResult(
                url=item.get('url', ''),
                title=item.get('title', ''),
                description=item.get('description', ''),
                snippet=item.get('snippet', item.get('description', '')),
                age=item.get('age'),
                extra_snippets=item.get('extra_snippets'),
                source_type='web'
            ))

        news_results = data.get('news', {}).get('results', [])
        for item in news_results:
            results.append(SearchResult(
                url=item.get('url', ''),
                title=item.get('title', ''),
                description=item.get('description', ''),
                snippet=item.get('snippet', item.get('description', '')),
                age=item.get('age'),
                source_type='news'
            ))

        if self.enable_archive and self.archive_manager and results:
            try:
                self.archive_manager.archive_search_results(query, results, 'web')
            except Exception as e:
                logger.error(f'Archive failed: {e}')

        return results
