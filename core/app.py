import os
import datetime
import asyncio
import aiohttp
import random
import re
from typing import List, Set, Optional

from .config import settings
from .logger import logger
from .downloader import download_html, clean_url, validate_wx_url
from .parsers import find_and_parse
from .converter import html_to_markdown
from .file_manager import prepare_article_dir, save_markdown, save_metadata, sanitize_filename
from .pdf_generator import generate_pdf
from .html_saver import save_full_html
from .index_manager import generate_global_index
from .record_manager import RecordManager
from .triage.manager import TriageManager
from .utils import check_command_exists

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
        self.triage_manager = TriageManager()
        self.processed_urls: Set[str] = set()
        
    def pre_run_check(self) -> bool:
        """运行前的环境检查"""
        # 1. 检查 PDF 依赖
        if self.args.pdf:
            if not check_command_exists("wkhtmltopdf"):
                logger.error("未找到 'wkhtmltopdf' 命令。请先安装它（如：sudo apt install wkhtmltopdf）或禁用 PDF 生成。")
                return False
        
        return True

    def _collect_target_urls(self) -> List[str]:
        """
        从多种来源（命令行、文件、聊天记录、交互输入）收集并校验目标 URL。
        返回已通过 validate_wx_url 校验的 URL 列表。
        """
        urls = []
        
        # 1. 处理 --url 参数 (可能是链接也可能是文件)
        if self.args.url:
            if os.path.isfile(self.args.url):
                logger.info(f"模式: 文件导入 -> {self.args.url}")
                urls.extend(self._read_urls_from_file(self.args.url))
            else:
                if validate_wx_url(self.args.url):
                    logger.info(f"模式: 单 URL 处理 -> {self.args.url}")
                    urls.append(self.args.url)
                else:
                    logger.error(f"提供的 URL 无效: {self.args.url} (格式错误或非微信域名)")
            
            # 如果指定了 --url 且已获取到任务（或报错），则不再继续读取默认 input
            if urls or not os.path.isfile(self.args.url):
                return urls

        # 2. 处理 --chat-log 参数
        if self.args.chat_log:
            raw_urls = self.extract_urls_from_log(self.args.chat_log)
            valid_urls = [u for u in raw_urls if validate_wx_url(u)]
            urls.extend(valid_urls)
            return urls

        # 3. 处理默认输入文件 (-i / input/urls.txt)
        if os.path.exists(self.args.input):
            urls.extend(self._read_urls_from_file(self.args.input))

        # 4. 交互模式：如果上述来源均未提供任务，则提示用户手动输入
        if not urls:
            print("\n" + "="*50)
            print("提示: 未检测到输入任务。")
            print("Tip: 若 URL 包含 '&' 等特殊字符，请在此处直接粘贴 (无需引号)。")
            print("="*50)
            try:
                raw_input = input("请输入文章 URL (回车确认): ").strip()
                if raw_input:
                    if validate_wx_url(raw_input):
                        urls.append(raw_input)
                    else:
                        logger.error(f"输入的 URL 无效: {raw_input} (格式错误或非微信域名)")
            except (EOFError, KeyboardInterrupt):
                pass
                
        return urls

    def _read_urls_from_file(self, file_path: str) -> List[str]:
        """从文件中读取并过滤 URL"""
        valid_urls = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#"):
                        if validate_wx_url(stripped):
                            valid_urls.append(stripped)
                        else:
                            logger.warning(f"跳过无效 URL: {stripped} (格式错误或非微信域名)")
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
        return valid_urls

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
        """处理单个 URL 的异步核心逻辑 (包含重试机制)"""
        async with semaphore:
            # 0. URL 清理
            original_url = url
            url = clean_url(url)
            if url != original_url:
                logger.debug(f"URL 已优化: {original_url[:40]}... -> {url[:40]}...")

            result = {"success": False, "stage": "init", "error": None, "url": url}
            
            # 重试循环: 尝试次数 = 1 (首次) + 重试次数
            max_attempts = self.args.retry + 1
            
            for attempt in range(1, max_attempts + 1):
                try:
                    # 1. 下载 (内部已有随机延迟)
                    html_content = await download_html(url, session=session)
                    if not html_content:
                        # 如果下载函数返回 None，通常意味着触发了验证码或网络错误
                        raise ValueError("Download failed (Anti-bot or Network)")
                    
                    # 2. 解析 (支持多解析器)
                    article_data = find_and_parse(html_content, url)
                    if not article_data:
                        await self.triage_manager.capture(url, html_content, "NO_PARSER_MATCHED")
                        logger.error(f"解析失败 (所有解析器均无法处理): {url}")
                        # 解析失败通常是内容问题，重试可能无用，但保持一致性还是抛出异常
                        raise ValueError("Parsing failed (No parser matched)")

                    title = article_data.get('title')
                    if not title:
                        await self.triage_manager.capture(url, html_content, "EMPTY_TITLE")
                        logger.error(f"解析失败 (标题为空): {url}")
                        raise ValueError("Parsing failed (Empty title)")

                    author = article_data['author']
                    publish_date = article_data.get('publish_date') or today_str
                    
                    logger.info(f"[Processing] {title}")
                    
                    # 3. 准备目录
                    article_dir, assets_dir = prepare_article_dir(self.args.user, publish_date, title, self.args.output)
                    safe_title = sanitize_filename(title)
                    
                    # 4. 转换 HTML 并本地化图片 (异步并行下载)
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
                        raise ValueError("HTML save failed")

                    # --- Markdown 生成 ---
                    if self.args.markdown:
                        md_path = os.path.join(article_dir, f"{safe_title}.md")
                        await save_markdown(md_path, md_content)

                    # --- PDF 生成 ---
                    if self.args.pdf:
                        pdf_output_path = os.path.join(article_dir, f"{safe_title}.pdf")
                        if not await generate_pdf(processed_html_content, title, pdf_output_path, assets_dir):
                            raise ValueError("PDF generation failed")

                    result["success"] = True
                    
                    # 写入 CSV 成功记录
                    await self.record_manager.add_record(
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
                    # 捕获所有异常用于重试逻辑
                    error_msg = str(e)
                    
                    # 如果是最后一次尝试，则记录失败并退出
                    if attempt == max_attempts:
                        result["error"] = error_msg
                        result["stage"] = "retry_exhausted" # 标记为重试耗尽
                        logger.error(f"处理失败 {url} (尝试 {attempt}/{max_attempts}): {e}")
                        
                        # 尝试捕获现场 (如果是解析相关错误，html_content 可能存在)
                        current_html = locals().get('html_content')
                        if current_html and "Parsing failed" in error_msg:
                             await self.triage_manager.capture(
                                url, current_html, "EXCEPTION_RETRY_EXHAUSTED", 
                                exception=e
                            )

                        # 写入 CSV 失败记录
                        await self.record_manager.add_record(
                            url=url,
                            status='failed',
                            failure_reason=f"Failed after {max_attempts} attempts: {error_msg}",
                            source='downloader'
                        )
                        return result
                    else:
                        # 还有重试机会，等待后继续
                        backoff = attempt * 2 # 线性退避: 2s, 4s, 6s...
                        logger.warning(f"处理出错 {url} (尝试 {attempt}/{max_attempts}): {e} - {backoff}秒后重试...")
                        await asyncio.sleep(backoff)

    async def run(self):
        logger.info(f"--- 微信公众号文章下载器 v{settings.VERSION} (Async) ---")
        
        # 0. 环境预检
        if not self.pre_run_check():
            return

        # 1. 获取已处理 URL (RecordManager 在初始化时已自动迁移)
        self.processed_urls = self.record_manager.processed_urls
        
        # 2. 收集目标 URLs
        all_target_urls = self._collect_target_urls()

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
