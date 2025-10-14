#!/usr/bin/env python3
"""Search and extraction demo"""
import asyncio
import sys
from datetime import datetime
from brave_client import BraveSearchClient
from content_extractor import ContentExtractor

DEMO_KEYWORD = "bitcoin whale"
EXTRACT_TOP_N = 10

async def demo_search(keyword):
    """Demo search and extraction workflow"""
    print(f"\nSearching for: '{keyword}'")
    print("-" * 50)

    # Initialize clients
    client = BraveSearchClient()
    extractor = ContentExtractor(auto_archive=True)

    # Search
    try:
        search_start = datetime.now()
        results = await client.search(keyword)
        search_time = (datetime.now() - search_start).total_seconds()
        print(f"Found {len(results)} results in {search_time:.2f}s")
    except Exception as e:
        print(f"Search failed: {e}")
        return

    # Display results
    print(f"\nTop results:")
    for i, r in enumerate(results[:5], 1):
        print(f"{i}. {r.title[:60]}")
        print(f"   {r.url[:70]}")

    # Extract content
    if results:
        print(f"\nExtracting content from top {EXTRACT_TOP_N} URLs...")
        urls = [r.url for r in results[:EXTRACT_TOP_N]]

        try:
            extract_start = datetime.now()
            contents = await extractor.extract_batch(urls)
            extract_time = (datetime.now() - extract_start).total_seconds()

            success_count = sum(1 for c in contents if c.success)
            total_chars = sum(len(c.text) for c in contents if c.success and c.text)

            print(f"Extracted {success_count}/{len(contents)} successfully in {extract_time:.2f}s")
            if total_chars > 0:
                print(f"Total: {total_chars:,} characters ({total_chars/extract_time:.0f} chars/s)")
        except Exception as e:
            print(f"Extraction failed: {e}")

    print("\nData saved to archives/ directory")

async def main():
    """Main function"""
    keyword = sys.argv[1] if len(sys.argv) > 1 else DEMO_KEYWORD
    await demo_search(keyword)

if __name__ == "__main__":
    asyncio.run(main())