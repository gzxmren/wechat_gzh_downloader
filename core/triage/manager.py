import os
import json
import hashlib
import datetime
import aiofiles
from pathlib import Path
from typing import Optional, Any, Dict

class TriageManager:
    """
    故障分诊管理器 (Triage Manager)
    独立组件，负责捕获、保存和管理解析失败的样本。
    """
    def __init__(self, storage_dir: str = "triage_samples"):
        self.base_dir = Path(os.getcwd())
        self.storage_dir = self.base_dir / storage_dir
        self.ensure_storage_exists()

    def ensure_storage_exists(self):
        """确保存储目录存在"""
        if not self.storage_dir.exists():
            self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def capture(self, url: str, html: Optional[str], reason: str, 
                      exception: Optional[Exception] = None, 
                      context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        捕获并保存一个失败样本现场。
        
        Args:
            url: 文章原始 URL
            html: 原始 HTML 源码
            reason: 失败原因分类 (如 NO_PARSER_MATCHED, EMPTY_TITLE, PARSE_EXCEPTION)
            exception: 捕获到的异常对象 (可选)
            context: 额外的上下文信息 (可选)
            
        Returns:
            str: 样本保存的目录名，如果失败则返回 None
        """
        if not html:
            return None

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 使用 URL 和原因生成短哈希，防止同一页面同一原因被无限重复采集
        # 允许同一 URL 不同原因被多次采集（例如先是解析不了，后来是标题为空）
        url_id = hashlib.md5(f"{url}{reason}".encode()).hexdigest()[:8]
        folder_name = f"{timestamp}_{reason}_{url_id}"
        sample_dir = self.storage_dir / folder_name
        
        try:
            sample_dir.mkdir(exist_ok=True)

            # 1. 保存原始 HTML (source.html)
            async with aiofiles.open(sample_dir / "source.html", mode='w', encoding='utf-8') as f:
                await f.write(html)

            # 2. 保存元数据 (metadata.json)
            metadata = {
                "url": url,
                "reason": reason,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "exception": str(exception) if exception else None,
                "context": context or {}
            }
            
            async with aiofiles.open(sample_dir / "metadata.json", mode='w', encoding='utf-8') as f:
                await f.write(json.dumps(metadata, indent=4, ensure_ascii=False))

            return folder_name
        except Exception as e:
            # Triage 本身不应抛出异常干扰主流程
            print(f"[Triage Error] Failed to capture sample: {e}")
            return None

    def list_samples(self) -> list:
        """列出当前所有失败样本摘要"""
        samples = []
        if not self.storage_dir.exists():
            return samples
            
        for d in sorted(self.storage_dir.iterdir(), reverse=True):
            if d.is_dir() and (d / "metadata.json").exists():
                try:
                    with open(d / "metadata.json", 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                        meta['folder_name'] = d.name
                        samples.append(meta)
                except:
                    continue
        return samples
