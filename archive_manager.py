#!/usr/bin/env python3
"""Archive manager for search results and extracted content"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib

class ArchiveManager:
    """Manages archives for search results and extracted content"""

    def __init__(self, archive_dir: str = None):
        if archive_dir is None:
            try:
                from config_loader import get_config
                config = get_config()
                brave_config = config.get_brave_config()
                archive_dir = brave_config.get('archive_path', './archives')
            except:
                archive_dir = './archives'

        if not Path(archive_dir).is_absolute():
            archive_dir = Path(__file__).parent / archive_dir

        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(exist_ok=True)

        self.daily_dir = self.archive_dir / 'daily'
        self.daily_dir.mkdir(exist_ok=True)

        self.extracted_dir = self.archive_dir / 'extracted'
        self.extracted_dir.mkdir(exist_ok=True)

        self.index_file = self.archive_dir / 'search_index.json'
        self.url_database = self.archive_dir / 'url_database.json'
        self.extraction_index = self.archive_dir / 'extraction_index.json'

        self.index = self._load_index()
        self.url_db = self._load_url_database()
        self.extract_index = self._load_extraction_index()
    
    def _load_index(self) -> Dict:
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'total_searches': 0,
            'total_urls': 0,
            'searches': []
        }

    def _load_url_database(self) -> Dict:
        if self.url_database.exists():
            with open(self.url_database, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _load_extraction_index(self) -> Dict:
        if self.extraction_index.exists():
            with open(self.extraction_index, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'total_extracted': 0,
            'total_success': 0,
            'total_failed': 0,
            'extractions': []
        }

    def _save_index(self):
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)

    def _save_url_database(self):
        with open(self.url_database, 'w', encoding='utf-8') as f:
            json.dump(self.url_db, f, ensure_ascii=False, indent=2)

    def _save_extraction_index(self):
        with open(self.extraction_index, 'w', encoding='utf-8') as f:
            json.dump(self.extract_index, f, ensure_ascii=False, indent=2)
    
    def archive_search_results(self, query: str, results: List[Any],
                              search_type: str = 'general') -> str:
        """Archive search results with URL deduplication"""
        timestamp = datetime.now()
        date_str = timestamp.strftime('%Y-%m-%d')

        search_record = {
            'query': query,
            'type': search_type,
            'timestamp': timestamp.isoformat(),
            'result_count': len(results),
            'results': []
        }

        for result in results:
            url_hash = hashlib.md5(result.url.encode()).hexdigest()

            search_record['results'].append({
                'url': result.url,
                'title': result.title,
                'snippet': result.snippet,
                'age': getattr(result, 'age', None)
            })

            if url_hash not in self.url_db:
                self.url_db[url_hash] = {
                    'url': result.url,
                    'first_seen': timestamp.isoformat(),
                    'last_seen': timestamp.isoformat(),
                    'titles': [result.title],
                    'queries': [query],
                    'seen_count': 1
                }
            else:
                self.url_db[url_hash]['last_seen'] = timestamp.isoformat()
                if result.title not in self.url_db[url_hash]['titles']:
                    self.url_db[url_hash]['titles'].append(result.title)
                if query not in self.url_db[url_hash]['queries']:
                    self.url_db[url_hash]['queries'].append(query)
                self.url_db[url_hash]['seen_count'] += 1

        daily_file = self.daily_dir / f'{date_str}_searches.json'

        if daily_file.exists():
            with open(daily_file, 'r', encoding='utf-8') as f:
                daily_data = json.load(f)
        else:
            daily_data = {'date': date_str, 'searches': []}

        daily_data['searches'].append(search_record)

        with open(daily_file, 'w', encoding='utf-8') as f:
            json.dump(daily_data, f, ensure_ascii=False, indent=2)

        self.index['total_searches'] += 1
        self.index['total_urls'] += len(results)
        self.index['searches'].append({
            'query': query,
            'timestamp': timestamp.isoformat(),
            'result_count': len(results),
            'file': str(daily_file.name)
        })

        self._save_index()
        self._save_url_database()

        print(f'📁 存档完成: {daily_file}')
        print(f'   - 保存了 {len(results)} 个URL')

        return str(daily_file)
    
    def archive_extracted_content(self, contents: List[Any]) -> str:
        """Archive extracted full-text content"""
        timestamp = datetime.now()
        date_str = timestamp.strftime('%Y-%m-%d')
        time_str = timestamp.strftime('%H-%M-%S')

        success_count = sum(1 for c in contents if c.success)
        failed_count = len(contents) - success_count

        extraction_record = {
            'timestamp': timestamp.isoformat(),
            'total': len(contents),
            'success': success_count,
            'failed': failed_count,
            'contents': []
        }

        for content in contents:
            record = {
                'url': content.url,
                'success': content.success,
                'title': content.title if content.success else None,
                'text_length': len(content.text) if content.text else 0,
                'error': content.error if not content.success else None,
                'extraction_time': timestamp.isoformat()
            }

            if content.success and content.text:
                url_hash = hashlib.md5(content.url.encode()).hexdigest()[:8]
                content_file = self.extracted_dir / f'{date_str}_{time_str}_{url_hash}.json'

                full_content = {
                    'url': content.url,
                    'title': content.title,
                    'text': content.text,
                    'text_length': len(content.text),
                    'extraction_time': timestamp.isoformat(),
                    'metadata': {
                        'success': True,
                        'method': 'readability'
                    }
                }

                with open(content_file, 'w', encoding='utf-8') as f:
                    json.dump(full_content, f, ensure_ascii=False, indent=2)

                record['content_file'] = content_file.name

            extraction_record['contents'].append(record)

        daily_extract_file = self.extracted_dir / f'{date_str}_extractions.json'

        if daily_extract_file.exists():
            with open(daily_extract_file, 'r', encoding='utf-8') as f:
                daily_extracts = json.load(f)
        else:
            daily_extracts = {'date': date_str, 'extractions': []}

        daily_extracts['extractions'].append(extraction_record)

        with open(daily_extract_file, 'w', encoding='utf-8') as f:
            json.dump(daily_extracts, f, ensure_ascii=False, indent=2)

        self.extract_index['total_extracted'] += len(contents)
        self.extract_index['total_success'] += success_count
        self.extract_index['total_failed'] += failed_count
        self.extract_index['extractions'].append({
            'timestamp': timestamp.isoformat(),
            'total': len(contents),
            'success': success_count,
            'failed': failed_count,
            'file': daily_extract_file.name
        })

        self._save_extraction_index()

        print(f'📄 提取存档完成: {daily_extract_file.name}')
        print(f'   - 成功: {success_count}, 失败: {failed_count}')
        if success_count > 0:
            print(f'   - 全文保存在: extracted/ 目录')

        return str(daily_extract_file)

    def get_stats(self) -> Dict:
        """Get archive statistics"""
        return {
            'search': {
                'total_searches': self.index.get('total_searches', 0),
                'total_urls': self.index.get('total_urls', 0),
                'unique_urls': len(self.url_db)
            },
            'extraction': {
                'total_extracted': self.extract_index.get('total_extracted', 0),
                'total_success': self.extract_index.get('total_success', 0),
                'total_failed': self.extract_index.get('total_failed', 0),
                'success_rate': (
                    self.extract_index.get('total_success', 0) /
                    self.extract_index.get('total_extracted', 1) * 100
                    if self.extract_index.get('total_extracted', 0) > 0 else 0
                )
            }
        }
