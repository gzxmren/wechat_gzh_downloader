import os
import datetime
import argparse
import sys
import re
import asyncio
import aiohttp
import random
from core.downloader import fetch_article
from core.converter import html_to_markdown
from core.file_manager import prepare_article_dir, save_markdown, save_metadata, sanitize_filename
from core.pdf_generator import generate_pdf
from core.html_saver import save_full_html
from core.db_decrypter import decrypt_wechat_db
from core.db_parser import parse_favorite_db
from core.index_manager import generate_global_index

def parse_args():
    """解析命令行参数"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_input = os.path.join(base_dir, "input/urls.txt")
    default_output = os.path.join(base_dir, "output")

    parser = argparse.ArgumentParser(
        description="微信公众号文章批量下载工具 (WeChat Fav Downloader) v4.5 Async",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # 基础参数
    parser.add_argument("-i", "--input", default=default_input, help="输入 URL 文件路径")
    parser.add_argument("-o", "--output", default=default_output, help="输出目录路径")
    parser.add_argument("-u", "--user", default="MyWeChatUser", help="微信用户名前缀")
    
    # 并发控制
    parser.add_argument("--concurrency", type=int, default=3, help="全局并发处理文章数 (默认: 3)")
    
    # 模式选择
    parser.add_argument("--chat-log", help="指定导出的聊天记录文件 (txt格式)")
    parser.add_argument("--db", action="store_true", help="启用数据库读取模式")
    
    # 功能开关
    parser.add_argument("--markdown", action="store_true", help="启用 Markdown 生成 (默认关闭)")
    parser.add_argument("--pdf", action="store_true", help="启用 PDF 生成 (默认关闭)")
    parser.add_argument("--no-images", action="store_true", help="禁用图片下载")
    parser.add_argument("--retry", type=int, default=1, help="单次运行的失败重试次数")
    parser.add_argument("--force", action="store_true", help="强制处理所有 URL (忽略历史记录)")
    
    # 数据库模式参数
    db_group = parser.add_argument_group('数据库模式选项')
    db_group.add_argument("--key", help="微信数据库密钥")
    db_group.add_argument("--db-path", help="加密的 Favorite.db 路径")
    db_group.add_argument("--decrypted-db", help="直接指定已解密的数据库路径")
    
    return parser.parse_args()

def load_history(history_file="history.log"):
    """加载已成功处理的历史 URL"""
    if not os.path.exists(history_file):
        return set()
    with open(history_file, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def append_history(url, history_file="history.log"):
    """记录成功处理的 URL"""
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(f"{url}\n")

def log_error(url, reason, log_file="error.log"):
    """记录失败日志"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {url} -> {reason}\n")

def extract_urls_from_log(log_path):
    """从聊天记录文本中提取微信文章链接"""
    urls = []
    pattern = re.compile(r'https?://mp\.weixin\.qq\.com/s[^\s\u4e00-\u9fa5]*')
    if not os.path.exists(log_path): return []
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
    except: pass
    return urls

async def process_single_url(url, args, today_str, session, semaphore):
    """处理单个 URL 的异步核心逻辑"""
    async with semaphore:
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
            
            print(f"\n[Processing] {title}")
            
            # 2. 准备目录
            article_dir, assets_dir = prepare_article_dir(args.user, publish_date, title, args.output)
            safe_title = sanitize_filename(title)
            
            # 3. 转换 HTML 并本地化图片 (异步并行下载)
            download_images = not args.no_images
            
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
            if args.markdown:
                md_path = os.path.join(article_dir, f"{safe_title}.md")
                await save_markdown(md_path, md_content)

            # --- PDF 生成 ---
            if args.pdf:
                pdf_output_path = os.path.join(article_dir, f"{safe_title}.pdf")
                if not await generate_pdf(processed_html_content, title, pdf_output_path, assets_dir):
                    result.update({"stage": "pdf", "error": "PDF generation failed"})
                    return result

            result["success"] = True
            print(f"  -> [OK] {title} 处理完成")
            return result
        except Exception as e:
            result["error"] = str(e)
            return result

async def async_main():
    args = parse_args()
    print(f"--- 微信公众号文章下载器 v4.5 (Async Concurrency) ---")
    
    # 1. 加载历史记录
    history_file = "history.log"
    history_set = load_history(history_file)
    if not args.force:
        print(f"已加载历史记录，将跳过 {len(history_set)} 个链接。")
    
    # 2. 收集目标 URLs
    all_target_urls = []
    if args.db:
        # TODO: 数据库解密目前仍是同步的，后续可优化
        all_target_urls = [a['url'] for a in parse_favorite_db(args.decrypted_db)]
    elif args.chat_log:
        all_target_urls = extract_urls_from_log(args.chat_log)
    else:
        if os.path.exists(args.input):
            with open(args.input, "r", encoding="utf-8") as f:
                all_target_urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

    # 3. 过滤 URL
    target_urls = all_target_urls if args.force else [u for u in all_target_urls if u not in history_set]
    if not target_urls:
        print("[Info] 没有新任务需要处理。")
        generate_global_index(args.output)
        return

    print(f"待处理任务: {len(target_urls)} 个，并发数限制: {args.concurrency}")

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    semaphore = asyncio.Semaphore(args.concurrency)
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in target_urls:
            # 加入微小的 staggered start 延迟，避免瞬间爆发请求
            await asyncio.sleep(random.uniform(0.5, 1.5))
            tasks.append(process_single_url(url, args, today_str, session, semaphore))
        
        results = await asyncio.gather(*tasks)

    # 统计与扫尾
    success_count = 0
    failed_items = []
    for res in results:
        if res["success"]:
            success_count += 1
            append_history(res["url"], history_file)
        else:
            print(f"[Error] {res['url']} 失败 ({res['stage']}): {res['error']}")
            log_error(res["url"], f"Stage: {res['stage']}, Msg: {res['error']}")
            failed_items.append(res["url"])

    print(f"\n--- 处理摘要 ---")
    print(f"任务总数: {len(target_urls)}")
    print(f"成功: {success_count}")
    print(f"失败: {len(failed_items)}")
    
    print("\n正在更新全局索引...")
    generate_global_index(args.output)

if __name__ == "__main__":
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n[User Interrupt] 程序已停止。")
