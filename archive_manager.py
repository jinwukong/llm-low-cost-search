"""Simple archive manager for search and extraction data"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class ArchiveManager:
    """Manages archive of search results and extracted content"""

    def __init__(self, archive_dir: str = "./archives"):
        self.archive_dir = Path(archive_dir)
        self.daily_dir = self.archive_dir / 'daily'
        self.extracted_dir = self.archive_dir / 'extracted'

        # Create directories
        self.archive_dir.mkdir(exist_ok=True)
        self.daily_dir.mkdir(exist_ok=True)
        self.extracted_dir.mkdir(exist_ok=True)

    def archive_search_results(self, query: str, results: List[Any], search_type: str = 'web') -> Optional[Path]:
        """Archive search results to daily JSON file"""
        timestamp = datetime.now()
        date_str = timestamp.strftime('%Y-%m-%d')

        # Daily file path
        daily_file = self.daily_dir / f'{date_str}_searches.json'

        # Load existing or create new
        if daily_file.exists():
            with open(daily_file, 'r', encoding='utf-8') as f:
                daily_data = json.load(f)
        else:
            daily_data = {
                'date': date_str,
                'searches': []
            }

        # Create search record
        search_record = {
            'query': query,
            'type': search_type,
            'timestamp': timestamp.isoformat(),
            'result_count': len(results),
            'results': []
        }

        # Add results
        for result in results:
            result_data = {
                'url': result.url,
                'title': result.title,
                'snippet': getattr(result, 'snippet', result.description),
                'age': getattr(result, 'age', None)
            }
            search_record['results'].append(result_data)

        # Append and save
        daily_data['searches'].append(search_record)

        with open(daily_file, 'w', encoding='utf-8') as f:
            json.dump(daily_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Archived {len(results)} search results to {daily_file.name}")
        print(f"📁 存档完成: {daily_file}")
        print(f"   - 保存了 {len(results)} 个URL")

        return daily_file

    def archive_extracted_content(self, contents: List[Any]) -> Optional[Path]:
        """Archive extracted content"""
        if not contents:
            return None

        timestamp = datetime.now()
        date_str = timestamp.strftime('%Y-%m-%d')

        # Daily extractions file
        daily_file = self.extracted_dir / f'{date_str}_extractions.json'

        # Load existing or create new
        if daily_file.exists():
            with open(daily_file, 'r', encoding='utf-8') as f:
                daily_data = json.load(f)
        else:
            daily_data = {
                'date': date_str,
                'extractions': []
            }

        # Create extraction batch record
        batch_record = {
            'timestamp': timestamp.isoformat(),
            'total': len(contents),
            'successful': [],
            'failed': []
        }

        # Process each content
        for content in contents:
            if content.success and content.text:
                # Save individual full text
                content_filename = f"{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}_{hash(content.url) % 100000000:08x}.json"
                content_file = self.extracted_dir / content_filename

                content_data = {
                    'url': content.url,
                    'title': content.title,
                    'text': content.text,
                    'extraction_time': timestamp.isoformat()
                }

                with open(content_file, 'w', encoding='utf-8') as f:
                    json.dump(content_data, f, ensure_ascii=False, indent=2)

                batch_record['successful'].append({
                    'url': content.url,
                    'title': content.title,
                    'file': content_filename,
                    'text_length': len(content.text)
                })
            else:
                batch_record['failed'].append({
                    'url': content.url,
                    'error': getattr(content, 'error', 'Unknown error')
                })

        # Append batch record and save
        daily_data['extractions'].append(batch_record)

        with open(daily_file, 'w', encoding='utf-8') as f:
            json.dump(daily_data, f, ensure_ascii=False, indent=2)

        success_count = len(batch_record['successful'])
        failed_count = len(batch_record['failed'])

        print(f"📄 提取存档完成: {daily_file.name}")
        print(f"   - 成功: {success_count}, 失败: {failed_count}")
        if success_count > 0:
            print(f"   - 全文保存在: extracted/ 目录")

        logger.info(f"Archived extraction batch: {success_count} successful, {failed_count} failed")

        return daily_file