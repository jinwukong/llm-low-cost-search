"""Content extractor using Readability with auto-archiving"""
import aiohttp
import asyncio
from typing import Optional, List, Tuple
from dataclasses import dataclass
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

@dataclass
class ExtractedContent:
    url: str
    title: Optional[str] = None
    text: Optional[str] = None
    success: bool = False
    error: Optional[str] = None

class ContentExtractor:
    """Content extractor using Readability"""

    def __init__(self, timeout: int = 15, max_text_length: int = 50000, auto_archive: bool = True):
        self.timeout = timeout
        self.max_text_length = max_text_length
        self.auto_archive = auto_archive

        try:
            from readability import Document
            self.Document = Document
        except ImportError:
            raise ImportError("Please install: pip install readability-lxml")

        try:
            from bs4 import BeautifulSoup
            self.BeautifulSoup = BeautifulSoup
        except ImportError:
            self.BeautifulSoup = None

        if self.auto_archive:
            try:
                from archive_manager import ArchiveManager
                self.archive_manager = ArchiveManager()
            except ImportError:
                logger.warning("Archive manager not available, auto-archive disabled")
                self.auto_archive = False
                self.archive_manager = None
        else:
            self.archive_manager = None
    
    async def _fetch_html(self, url: str) -> Tuple[Optional[str], str]:
        """Fetch HTML from URL"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers, allow_redirects=True) as response:
                    if response.status >= 400:
                        return None, f"HTTP {response.status}"

                    html = await response.text()
                    return html, ""

        except asyncio.TimeoutError:
            return None, "Timeout"
        except Exception as e:
            return None, str(e)[:100]

    def _extract_text(self, html: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract text from HTML using Readability"""
        try:
            doc = self.Document(html)
            title = doc.title()
            summary_html = doc.summary()

            if self.BeautifulSoup and summary_html:
                soup = self.BeautifulSoup(summary_html, 'html.parser')
                for script in soup(['script', 'style']):
                    script.decompose()
                text = soup.get_text(separator='\n', strip=True)
            else:
                import re
                text = re.sub(r'<[^>]+>', ' ', summary_html)
                text = re.sub(r'\s+', ' ', text).strip()

            return title, text

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return None, None

    async def extract(self, url: str) -> ExtractedContent:
        """Extract content from URL"""
        result = ExtractedContent(url=url)

        html, error = await self._fetch_html(url)
        if not html:
            result.error = error
            result.success = False
            return result

        title, text = self._extract_text(html)

        if text:
            result.title = title
            result.text = text[:self.max_text_length]
            result.success = True
        else:
            result.error = "Failed to extract content"
            result.success = False

        return result
    
    async def extract_batch(self, urls: List[str], max_concurrent: int = 5) -> List[ExtractedContent]:
        """Extract content from multiple URLs with auto-archiving"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def extract_with_limit(url: str) -> ExtractedContent:
            async with semaphore:
                return await self.extract(url)

        tasks = [extract_with_limit(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                final_results.append(ExtractedContent(
                    url=url,
                    success=False,
                    error=str(result)[:100]
                ))
            else:
                final_results.append(result)

        if self.auto_archive and self.archive_manager:
            try:
                self.archive_manager.archive_extracted_content(final_results)
            except Exception as e:
                logger.error(f"Failed to archive extracted content: {e}")

        success_count = sum(1 for r in final_results if r.success)
        total = len(final_results)
        if total > 0:
            logger.info(f"Extraction: {success_count}/{total} successful ({success_count*100/total:.1f}%)")

        return final_results
