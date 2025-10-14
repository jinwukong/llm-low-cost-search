#!/usr/bin/env python3
"""Search module demo"""
import asyncio
from pathlib import Path
from datetime import datetime

import sys
sys.path.append(str(Path(__file__).parent.parent))

from search.brave_client import BraveSearchClient
from search.content_extractor import ContentExtractor

DEMO_KEYWORD = "bitcoin whale"
EXTRACT_TOP_N = 10

async def demo_search(keyword):
    """Demo search and extraction workflow"""
    print("\n" + "="*60)
    print(f"🔍 搜索演示: '{keyword}'")
    print("="*60)

    print("\n📡 初始化搜索客户端...")
    client = BraveSearchClient()
    extractor = ContentExtractor(auto_archive=True)

    start_time = datetime.now()

    print(f"\n🔍 正在搜索 '{keyword}'...")
    try:
        search_start = datetime.now()
        results = await client.search(keyword)
        search_time = (datetime.now() - search_start).total_seconds()
        print(f"   ✅ 搜索完成: {len(results)} 个结果 ({search_time:.2f}秒)")
    except Exception as e:
        print(f"   ❌ 搜索失败: {e}")
        return

    print(f"\n📋 搜索结果概览 (前{min(len(results), 10)}个):")
    print("-" * 60)
    for i, r in enumerate(results[:10], 1):
        print(f"{i:2}. {r.title[:50]}...")
        print(f"    {r.url[:55]}...")

    extract_time = 0
    success_count = 0
    total_chars = 0

    if results:
        print(f"\n⚙️ 正在提取前{EXTRACT_TOP_N}个URL的内容...")
        urls_to_extract = [r.url for r in results[:EXTRACT_TOP_N]]

        try:
            extract_start = datetime.now()
            contents = await extractor.extract_batch(urls_to_extract)
            extract_time = (datetime.now() - extract_start).total_seconds()

            success_count = sum(1 for c in contents if c.success)
            total_chars = sum(len(c.text) for c in contents if c.success)

            print(f"   ✅ 提取完成: {success_count}/{len(contents)} 成功 ({extract_time:.2f}秒)")
            print(f"   📄 总计提取: {total_chars:,} 字符")

        except Exception as e:
            print(f"   ❌ 提取失败: {e}")

    total_time = (datetime.now() - start_time).total_seconds()

    print("\n" + "="*60)
    print("📊 性能统计:")
    print("="*60)
    print(f"关键词: '{keyword}'")
    print(f"搜索结果: {len(results)} 个")
    print(f"内容提取: {success_count}/{EXTRACT_TOP_N} 成功")
    print(f"提取字符: {total_chars:,} 字符")
    print(f"搜索用时: {search_time:.2f} 秒")
    print(f"提取用时: {extract_time:.2f} 秒")
    print(f"总计用时: {total_time:.2f} 秒")
    if success_count > 0 and extract_time > 0:
        print(f"提取效率: {total_chars/extract_time:.0f} 字符/秒")

    print("\n" + "="*60)
    print("💾 归档信息:")
    print("="*60)
    print("搜索记录已保存到: search/archives/daily/")
    if success_count > 0:
        print("提取内容已保存到: search/archives/extracted/")
        print("索引已更新: search/archives/search_index.json")
        print("URL库已更新: search/archives/url_database.json")

    print(f"\n时间戳: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    """Main function"""
    print("\n" + "*"*60)
    print("*" + " "*15 + "🔍 搜索模块效率演示" + " "*15 + "*")
    print("*"*60)

    keyword = DEMO_KEYWORD

    print(f"\n当前演示关键词: '{keyword}'")
    print(f"将提取前 {EXTRACT_TOP_N} 个URL的内容")

    choice = input("\n按回车开始演示，或输入新关键词: ").strip()

    if choice:
        keyword = choice
        print(f"\n✅ 关键词已更改为: '{keyword}'")

    await demo_search(keyword)

    print("\n" + "="*60)
    print("✅ 演示完成！")
    print("\n💡 提示:")
    print("  • 修改脚本顶部的 DEMO_KEYWORD 可更换默认关键词")
    print("  • 调整 EXTRACT_TOP_N 可控制提取数量")
    print("  • 查看 search/archives/ 目录了解归档结构")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
