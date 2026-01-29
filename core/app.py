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

class WeChatDownloaderApp:
    def __init__(self, args):
        self.args = args
        self.history_file = "history.log"
        self.error_file = "error.log"
        self.history_set: Set[str] = set()
        
    def load_history(self):
        """加载已成功处理的历史 URL"""
        if not os.path.exists(self.history_file):
            return
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                self.history_set = set(line.strip() for line in f if line.strip())
            if not self.args.force:
                logger.info(f"已加载历史记录，将跳过 {len(self.history_set)} 个链接。")
        except Exception as e:
            logger.error(f"加载历史记录失败: {e}")

    def append_history(self, url: str):
        """记录成功处理的 URL"""
        try:
            with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(f"{url}\n")
        except Exception as e:
            logger.error(f"写入历史记录失败: {e}")

    def log_error(self, url: str, reason: str):
        """记录失败日志"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.error_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {url} -> {reason}\n")
        except Exception as e:
            logger.error(f"写入错误日志失败: {e}")

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
                logger.info(f"  -> [OK] {title} 处理完成")
                return result
            except Exception as e:
                result["error"] = str(e)
                logger.error(f"处理失败 {url}: {e}")
                return result

    async def run(self):
        logger.info(f"--- 微信公众号文章下载器 v{settings.VERSION} (Async) ---")
        
        # 1. 加载历史记录
        self.load_history()
        
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
        target_urls = unique_all_urls if self.args.force else [u for u in unique_all_urls if u not in self.history_set]
        
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
        failed_items = []
        for res in results:
            if res["success"]:
                success_count += 1
                self.append_history(res["url"])
            else:
                logger.error(f"[Error] {res['url']} 失败 ({res['stage']}): {res['error']}")
                self.log_error(res["url"], f"Stage: {res['stage']}, Msg: {res['error']}")
                failed_items.append(res["url"])

        logger.info(f"\n--- 处理摘要 ---")
        logger.info(f"任务总数: {len(target_urls)}")
        logger.info(f"成功: {success_count}")
        logger.info(f"失败: {len(failed_items)}")
        
        logger.info("正在更新全局索引...")
        generate_global_index(self.args.output)
