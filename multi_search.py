#!/usr/bin/env python3
"""Multi-type search client for web and news"""
import asyncio
import sys
from typing import List, Dict, Any
sys.path.append('.')

from brave_client import BraveSearchClient

class MultiSearchClient:
    """Client for searching multiple content types"""

    def __init__(self):
        self.web_client = BraveSearchClient()
    
    async def search_web_and_news(self, query: str,
                                  web_count: int = 10,
                                  news_count: int = 10) -> Dict[str, Any]:
        """Search both web and news simultaneously"""
        print(f'🔍 多类型搜索: "{query}"')
        print(f'   目标: {web_count}个网页 + {news_count}个新闻\n')

        tasks = [
            self.web_client.search(
                query,
                count=web_count,
                **{"result_filter": "web"}
            ),

            self.web_client.search(
                query + " news",
                count=news_count,
                freshness="pd",
                **{"result_filter": "news"}
            )
        ]
        
        try:
            web_results, news_results = await asyncio.gather(*tasks, return_exceptions=True)

            if isinstance(web_results, Exception):
                print(f'⚠️ 网页搜索失败: {web_results}')
                web_results = []

            if isinstance(news_results, Exception):
                print(f'⚠️ 新闻搜索失败: {news_results}')
                news_results = []

            web_urls = {r.url for r in web_results if hasattr(r, 'url')}
            news_results_unique = [
                r for r in news_results
                if hasattr(r, 'url') and r.url not in web_urls
            ]

            result = {
                'query': query,
                'web_results': web_results,
                'news_results': news_results_unique,
                'total_count': len(web_results) + len(news_results_unique),
                'web_count': len(web_results),
                'news_count': len(news_results_unique)
            }

            print(f'✅ 获取结果:')
            print(f'   - 网页: {len(web_results)}个')
            print(f'   - 新闻: {len(news_results_unique)}个（去重后）')
            print(f'   - 总计: {result["total_count"]}个')

            return result

        except Exception as e:
            print(f'❌ 搜索失败: {e}')
            return {
                'query': query,
                'web_results': [],
                'news_results': [],
                'error': str(e)
            }
    
    async def search_with_multiple_endpoints(self, query: str) -> Dict[str, Any]:
        """Alternative approach using multiple endpoints (requires API upgrade)"""
        print('📝 多endpoint方案需要:')
        print('1. 修改配置文件，添加多个endpoint配置')
        print('2. 修改brave_client.py支持动态endpoint')
        print('3. 或者为每个endpoint创建独立的客户端实例')

        return {}

async def demo():
    """Demo multi-type search"""
    client = MultiSearchClient()

    results = await client.search_web_and_news(
        query="Bitcoin cryptocurrency",
        web_count=5,
        news_count=5
    )

    print(f'\n📊 搜索结果示例:')

    if results['web_results']:
        print(f'\n🌐 网页结果 (前3个):')
        for i, r in enumerate(results['web_results'][:3], 1):
            print(f'{i}. {r.title[:50]}...')

    if results['news_results']:
        print(f'\n📰 新闻结果 (前3个):')
        for i, r in enumerate(results['news_results'][:3], 1):
            print(f'{i}. {r.title[:50]}...')

if __name__ == '__main__':
    asyncio.run(demo())
