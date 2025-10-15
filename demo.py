#!/usr/bin/env python3
"""Search and extraction demo"""
import asyncio
import sys
from datetime import datetime
import logging
from .brave_client import BraveSearchClient
from .content_extractor import ContentExtractor

DEMO_KEYWORD = "bitcoin whale"
EXTRACT_TOP_N = 10

async def demo_search(keyword):
    """Demo search and extraction workflow"""
    logger = logging.getLogger("demo")
    logger.info("Searching for: %r", keyword)

    # Initialize clients
    client = BraveSearchClient()
    extractor = ContentExtractor(auto_archive=True)

    # Search
    try:
        search_start = datetime.now()
        results = await client.search(keyword)
        search_time = (datetime.now() - search_start).total_seconds()
        logger.info("Found %d results in %.2fs", len(results), search_time)
    except Exception as e:
        logging.exception("Search failed: %s", e)
        return

    # Display results
    if results:
        logger.info("Top results:")
        for i, r in enumerate(results[:5], 1):
            logger.info("%d. %s", i, r.title[:60])
            logger.info("   %s", r.url[:70])

    # Extract content
    if results:
        logger.info("Extracting content from top %d URLs...", EXTRACT_TOP_N)
        urls = [r.url for r in results[:EXTRACT_TOP_N]]

        try:
            extract_start = datetime.now()
            contents = await extractor.extract_batch(urls)
            extract_time = (datetime.now() - extract_start).total_seconds()

            success_count = sum(1 for c in contents if c.success)
            total_chars = sum(len(c.text) for c in contents if c.success and c.text)

            logger.info(
                "Extracted %d/%d successfully in %.2fs",
                success_count,
                len(contents),
                extract_time,
            )
            if total_chars > 0:
                rate = total_chars / extract_time if extract_time > 0 else 0
                logger.info(
                    "Total: %s characters (%.0f chars/s)",
                    f"{total_chars:,}",
                    rate,
                )
        except Exception as e:
            logging.exception("Extraction failed: %s", e)

    logger.info("Data saved to archives/ directory")

async def main():
    """Main function"""
    keyword = sys.argv[1] if len(sys.argv) > 1 else DEMO_KEYWORD
    await demo_search(keyword)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(main())
