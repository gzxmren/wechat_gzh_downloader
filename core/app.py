import os
import datetime
import asyncio
import aiohttp
import random
import re
from typing import List, Set, Optional

from .config import settings
from .logger import logger
from .downloader import fetch_article, clean_url
from .converter import html_to_markdown
from .file_manager import prepare_article_dir, save_markdown, save_metadata, sanitize_filename
from .pdf_generator import generate_pdf
from .html_saver import save_full_html
from .index_manager import generate_global_index
from .db_parser import parse_favorite_db
from .record_manager import RecordManager

class WeChatDownloaderApp:
    def __init__(self, args):
        self.args = args
        
        # 确定 CSV 路径：优先使用 args.output，否则使用配置默认值
        output_dir = args.output if args.output else str(settings.OUTPUT_DIR)
        csv_path = os.path.join(output_dir, "wechat_records.csv")
        
        # 确保目录存在 (RecordManager 需要)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        self.record_manager = RecordManager(csv_path=csv_path)
        self.processed_urls: Set[str] = set()
        
    def extract_urls_from_log(self, log_path: str) -> List[str]:
        """从聊天记录文本中提取微信文章链接"""
        urls = []
        pattern = re.compile(r'https?://mp\.weixin\.qq\.com/s[^\s\u4e00-\u9fa5]*')
        if not os.path.exists(log_path):
            logger.warning(f"聊天记录文件不存在: {log_path}")
            return []
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
                found = pattern.findall(content)
                seen = set()
                for url in found:
                    url = url.strip('",;)')
                    if url not in seen:
                        urls.append(url)
                        seen.add(url)
        except Exception as e:
            logger.error(f"提取 URL 失败: {e}")
        return urls

    async def process_single_url(self, url: str, today_str: str, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore):
        """处理单个 URL 的异步核心逻辑"""
        async with semaphore:
            # 0. URL 清理
            original_url = url
            url = clean_url(url)
            if url != original_url:
                logger.debug(f"URL 已优化: {original_url[:40]}... -> {url[:40]}...")

            result = {"success": False, "stage": "init", "error": None, "url": url}
            try:
                # 1. 下载 (内部已有随机延迟)
                article_data = await fetch_article(url, session=session)
                if not article_data:
                    result.update({"stage": "download", "error": "Download failed"})
                    return result
                    
                title = article_data['title']
                author = article_data['author']
                publish_date = article_data.get('publish_date') or today_str
                
                logger.info(f"[Processing] {title}")
                
                # 2. 准备目录
                article_dir, assets_dir = prepare_article_dir(self.args.user, publish_date, title, self.args.output)
                safe_title = sanitize_filename(title)
                
                # 3. 转换 HTML 并本地化图片 (异步并行下载)
                download_images = not self.args.no_images
                
                md_content, processed_html_content = await html_to_markdown(
                    article_data['content_html'], title, article_data['original_url'],
                    assets_dir=assets_dir if download_images else None,
                    download_images=download_images,
                    session=session
                )
                
                # --- Metadata 保存 ---
                metadata = {
                    "title": title,
                    "author": author,
                    "publish_date": publish_date,
                    "original_url": article_data['original_url'],
                    "download_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                metadata_path = os.path.join(article_dir, "metadata.json")
                await save_metadata(metadata_path, metadata)

                # --- HTML 生成 (默认始终生成) ---
                html_output_path = os.path.join(article_dir, f"{safe_title}.html")
                if not await save_full_html(processed_html_content, title, html_output_path, assets_dir):
                    result.update({"stage": "save_html", "error": "HTML save failed"})
                    return result

                # --- Markdown 生成 ---
                if self.args.markdown:
                    md_path = os.path.join(article_dir, f"{safe_title}.md")
                    await save_markdown(md_path, md_content)

                # --- PDF 生成 ---
                if self.args.pdf:
                    pdf_output_path = os.path.join(article_dir, f"{safe_title}.pdf")
                    if not await generate_pdf(processed_html_content, title, pdf_output_path, assets_dir):
                        result.update({"stage": "pdf", "error": "PDF generation failed"})
                        return result

                result["success"] = True
                
                # 写入 CSV 成功记录
                self.record_manager.add_record(
                    url=url,
                    status='success',
                    title=title,
                    author=author,
                    published_date=publish_date,
                    folder_name=os.path.basename(article_dir),
                    source='downloader'
                )

                logger.info(f"  -> [OK] {title} 处理完成")
                return result
            except Exception as e:
                result["error"] = str(e)
                logger.error(f"处理失败 {url}: {e}")
                
                # 写入 CSV 失败记录
                self.record_manager.add_record(
                    url=url,
                    status='failed',
                    failure_reason=f"Stage: {result['stage']}, Msg: {str(e)}",
                    source='downloader'
                )
                return result

    async def run(self):
        logger.info(f"--- 微信公众号文章下载器 v{settings.VERSION} (Async) ---")
        
        # 1. 获取已处理 URL (RecordManager 在初始化时已自动迁移)
        self.processed_urls = self.record_manager.processed_urls
        
        # 2. 收集目标 URLs
        all_target_urls = []
        if self.args.url:
            all_target_urls = [self.args.url]
            logger.info(f"模式: 单 URL 处理 -> {self.args.url}")
        elif self.args.db:
            all_target_urls = [a['url'] for a in parse_favorite_db(self.args.decrypted_db)]
        elif self.args.chat_log:
            all_target_urls = self.extract_urls_from_log(self.args.chat_log)
        else:
            if os.path.exists(self.args.input):
                with open(self.args.input, "r", encoding="utf-8") as f:
                    for line in f:
                        stripped = line.strip()
                        if stripped and not stripped.startswith("#"):
                            all_target_urls.append(stripped)

        # 3. 过滤 URL (先去重并保持顺序)
        unique_all_urls = list(dict.fromkeys(all_target_urls))
        target_urls = unique_all_urls if self.args.force else [u for u in unique_all_urls if u not in self.processed_urls]
        
        if not target_urls:
            logger.info("没有新任务需要处理。")
            generate_global_index(self.args.output)
            return

        concurrency = self.args.concurrency or settings.CONCURRENCY
        logger.info(f"待处理任务: {len(target_urls)} 个，并发数限制: {concurrency}")

        today_str = datetime.date.today().strftime("%Y-%m-%d")
        semaphore = asyncio.Semaphore(concurrency)
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for url in target_urls:
                # 加入微小的 staggered start 延迟
                await asyncio.sleep(random.uniform(0.5, 1.5))
                tasks.append(self.process_single_url(url, today_str, session, semaphore))
            
            results = await asyncio.gather(*tasks)

        # 统计与扫尾
        success_count = 0
        failed_count = 0
        for res in results:
            if res["success"]:
                success_count += 1
            else:
                failed_count += 1

        logger.info(f"\n--- 处理摘要 ---")
        logger.info(f"任务总数: {len(target_urls)}")
        logger.info(f"成功: {success_count}")
        logger.info(f"失败: {failed_count}")
        
        logger.info("正在更新全局索引...")
        generate_global_index(self.args.output)
