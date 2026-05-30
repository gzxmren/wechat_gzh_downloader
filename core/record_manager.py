import os
import csv
import datetime
import io
import aiofiles
import asyncio
from pathlib import Path
from typing import List, Set, Dict, Optional
from .logger import logger
from .config import settings

class RecordManager:
    """
    资产清单管理器 (CSV 数据持久化层)
    负责 wechat_records.csv 的增量追加、全量重建以及旧数据迁移。
    """
    
    HEADERS = [
        'url', 'status', 'title', 'author', 'published_date', 
        'folder_name', 'timestamp', 'failure_reason', 'source'
    ]
    
    def __init__(self, csv_path: Optional[str] = None):
        # 默认保存到 output 目录下
        if csv_path is None:
            output_dir = str(settings.OUTPUT_DIR)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            self.csv_path = os.path.join(output_dir, "wechat_records.csv")
        else:
            self.csv_path = csv_path
            
        self.history_file = "history.log"
        self.processed_urls: Set[str] = set()
        
        # 1. 确保 CSV 文件存在并有表头
        self._init_csv()
        
        # 2. 自动执行迁移逻辑
        self._migrate_legacy_history()
        
        # 3. 加载已成功的 URL 集合用于去重
        self.load_existing_urls()
        
        # 4. 初始化协程写入锁，防止多协程并发写入冲突
        self._lock = asyncio.Lock()

    def _init_csv(self):
        """初始化 CSV 文件"""
        if not os.path.exists(self.csv_path):
            try:
                with open(self.csv_path, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(self.HEADERS)
                logger.info(f"已创建资产清单文件: {self.csv_path}")
            except Exception as e:
                logger.error(f"创建 CSV 失败: {e}")

    def load_existing_urls(self) -> Set[str]:
        """从 CSV 加载所有状态为 success 的 URL"""
        self.processed_urls = set()
        if not os.path.exists(self.csv_path):
            return self.processed_urls
            
        try:
            with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('status') == 'success' and row.get('url'):
                        self.processed_urls.add(row['url'])
        except Exception as e:
            logger.error(f"加载 CSV 记录失败: {e}")
            
        return self.processed_urls

    async def add_record(self, url: str, status: str = 'success', title: str = '', 
                   author: str = '', published_date: str = '', folder_name: str = '', 
                   failure_reason: str = '', source: str = 'downloader'):
        """
        异步向 CSV 追加一条记录 (非阻塞)。
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 只有成功的 URL 才加入内存去重集合
        if status == 'success':
            self.processed_urls.add(url)
            
        record = {
            'url': url,
            'status': status,
            'title': title,
            'author': author,
            'published_date': published_date,
            'folder_name': folder_name,
            'timestamp': timestamp,
            'failure_reason': failure_reason,
            'source': source
        }
        
        try:
            # 使用内存缓冲生成 CSV 行字符串
            buffer = io.StringIO()
            writer = csv.DictWriter(buffer, fieldnames=self.HEADERS)
            
            # 如果文件不存在，理论上需要写表头，但这里是 append 模式且 init 保证了文件存在
            # 为了安全，如果文件真的被删了，aiofiles append 会创建新文件，此时缺表头
            # 但检测文件存在性是同步 IO，为了性能我们假设 _init_csv 已处理好
            # 或者我们可以简单判断一下:
            # if not os.path.exists(self.csv_path): ... (blocking)
            # 暂时忽略极端情况，直接写记录
            writer.writerow(record)
            csv_line = buffer.getvalue()
            
            # 使用协程锁保护异步写入文件，规避并发写冲突
            async with self._lock:
                async with aiofiles.open(self.csv_path, 'a', encoding='utf-8-sig') as f:
                    await f.write(csv_line)
                
        except Exception as e:
            logger.error(f"追加 CSV 记录失败: {e}")

    def _migrate_legacy_history(self):
        """
        从旧的 history.log 自动迁移数据到 CSV。
        为了兼容性，内部调用同步逻辑，但在初始化阶段运行是可以的。
        """
        if not os.path.exists(self.history_file):
            return

        logger.info(f"检测到旧版 {self.history_file}，开始执行自动迁移...")
        
        legacy_urls = []
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                legacy_urls = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"读取旧历史文件失败: {e}")
            return

        if not legacy_urls:
            return

        # 获取当前已有的 URL 避免迁移重复
        existing_urls = self.load_existing_urls()
        
        migrated_count = 0
        
        # 批量迁移使用同步写入以简化逻辑（因为只在启动时运行一次）
        # 这里复用手动写入逻辑而不是 call async add_record，因为我们在 __init__ 中不能 await
        try:
            with open(self.csv_path, 'a', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.HEADERS)
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                for url in legacy_urls:
                    if url not in existing_urls:
                        writer.writerow({
                            'url': url,
                            'status': 'success',
                            'title': '[Migrated]', 
                            'author': '', 'published_date': '', 'folder_name': '',
                            'timestamp': timestamp, 'failure_reason': '',
                            'source': 'history_migration'
                        })
                        self.processed_urls.add(url)
                        migrated_count += 1
                        
            if migrated_count > 0:
                logger.info(f"成功迁移 {migrated_count} 条记录到 CSV。")
            
            # 归档旧文件
            backup_name = f"{self.history_file}.bak"
            if os.path.exists(backup_name):
                os.remove(backup_name) 
            os.rename(self.history_file, backup_name)
            logger.info(f"旧历史文件已更名为 {backup_name}")
            
        except Exception as e:
            logger.error(f"迁移数据失败: {e}")

    def rebuild_from_folder(self, output_dir: str):
        """
        离线模式：扫描 output 目录，全量重建 CSV。
        """
        import json
        logger.info(f"正在全量扫描目录以重建资产清单: {output_dir}")
        
        records = []
        output_path = Path(output_dir)
        
        if not output_path.exists():
            logger.error(f"目录不存在: {output_dir}")
            return

        # 扫描 metadata.json
        for meta_file in output_path.glob("**/metadata.json"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    
                    folder_name = meta_file.parent.name
                    # 尝试从元数据中获取下载时间作为 timestamp
                    timestamp = meta.get('download_time', '')
                    
                    records.append({
                        'url': meta.get('original_url', ''),
                        'status': 'success',
                        'title': meta.get('title', ''),
                        'author': meta.get('author', ''),
                        'published_date': meta.get('publish_date', ''),
                        'folder_name': folder_name,
                        'timestamp': timestamp,
                        'failure_reason': '',
                        'source': 'offline_scan'
                    })
            except Exception as e:
                logger.warning(f"读取元数据失败 {meta_file}: {e}")

        # 按时间排序 (从旧到新)
        records.sort(key=lambda x: x['timestamp'], reverse=False)

        # 去重逻辑：基于 URL 去重，保留时间戳最新的那条记录
        unique_records_map = {}
        for r in records:
            url = r.get('url')
            if url:
                unique_records_map[url] = r
        
        final_records = list(unique_records_map.values())

        # 覆盖写入 CSV
        try:
            with open(self.csv_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.HEADERS)
                writer.writeheader()
                for r in final_records:
                    writer.writerow(r)
            
            # 刷新内存缓存
            self.load_existing_urls()
            logger.info(f"资产清单重建完成，共计 {len(final_records)} 条独立记录。")
        except Exception as e:
            logger.error(f"重建 CSV 失败: {e}")
