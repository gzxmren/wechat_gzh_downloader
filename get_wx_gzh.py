import os
import datetime
import argparse
import sys
import getpass
import re
import time
from core.downloader import fetch_article
from core.converter import html_to_markdown
from core.file_manager import prepare_article_dir, save_markdown, sanitize_filename
from core.pdf_generator import generate_pdf
from core.db_decrypter import decrypt_wechat_db
from core.db_parser import parse_favorite_db, save_urls_to_file

def parse_args():
    """解析命令行参数"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_input = os.path.join(base_dir, "input/urls.txt")
    default_output = os.path.join(base_dir, "output")

    parser = argparse.ArgumentParser(
        description="微信公众号文章批量下载工具 (WeChat Fav Downloader)",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # 基础参数
    parser.add_argument("-i", "--input", default=default_input, help="输入 URL 文件路径")
    parser.add_argument("-o", "--output", default=default_output, help="输出目录路径")
    parser.add_argument("-u", "--user", default="MyWeChatUser", help="微信用户名前缀")
    
    # 模式选择
    parser.add_argument("--chat-log", help="指定导出的聊天记录文件 (txt格式)")
    parser.add_argument("--db", action="store_true", help="启用数据库读取模式")
    
    # 功能开关
    parser.add_argument("--no-images", action="store_true", help="禁用图片下载")
    parser.add_argument("--no-pdf", action="store_true", help="禁用 PDF 生成")
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

def process_single_url(url, args, today_str):
    """处理单个 URL 的核心逻辑"""
    result = {"success": False, "stage": "init", "error": None}
    try:
        # 1. 下载
        article_data = fetch_article(url)
        if not article_data:
            result.update({"stage": "download", "error": "Download failed"})
            return result
            
        title = article_data['title']
        print(f"  -> 标题: {title}")
        
        # 2. 准备目录
        article_dir, assets_dir = prepare_article_dir(args.user, today_str, title, args.output)
        
        # 3. 转换
        download_images = not args.no_images
        md_content, processed_html = html_to_markdown(
            article_data['content_html'], title, article_data['original_url'],
            assets_dir=assets_dir if download_images else None,
            download_images=download_images
        )
        
        # 4. 保存 Markdown
        safe_title = sanitize_filename(title)
        md_path = os.path.join(article_dir, f"{safe_title}.md")
        if not save_markdown(md_path, md_content):
            result.update({"stage": "save_md", "error": "Save Markdown failed"})
            return result
        print(f"  -> [OK] Markdown 保存成功")
        
        # 5. 生成 PDF
        if not args.no_pdf:
            pdf_path = os.path.join(article_dir, f"{safe_title}.pdf")
            if generate_pdf(processed_html, title, pdf_path, assets_dir):
                print(f"  -> [OK] PDF 生成成功")
            else:
                result.update({"stage": "pdf", "error": "PDF generation failed"})
                return result

        result["success"] = True
        return result
    except Exception as e:
        result["error"] = str(e)
        return result

def main():
    args = parse_args()
    print(f"--- 微信公众号文章下载器 v3.3 (断点续传) ---")
    
    # 1. 加载历史记录
    history_file = "history.log"
    history_set = load_history(history_file)
    if not args.force:
        print(f"已加载历史记录，将自动跳过 {len(history_set)} 个已处理链接。")
    
    # 2. 收集目标 URLs
    all_target_urls = []
    if args.db:
        all_target_urls = [a['url'] for a in parse_favorite_db(args.decrypted_db)] # 简化版逻辑
    elif args.chat_log:
        all_target_urls = extract_urls_from_log(args.chat_log)
    else:
        if os.path.exists(args.input):
            with open(args.input, "r", encoding="utf-8") as f:
                all_target_urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

    # 3. 过滤掉历史记录中的 URL
    if args.force:
        target_urls = all_target_urls
    else:
        target_urls = [u for u in all_target_urls if u not in history_set]
        skip_count = len(all_target_urls) - len(target_urls)
        if skip_count > 0:
            print(f"过滤完成：跳过 {skip_count} 个已处理链接，剩余 {len(target_urls)} 个新任务。")

    if not target_urls:
        print("[Info] 没有新任务需要处理。")
        return

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    failed_items = []
    success_count = 0
    
    # 第一轮主循环
    for i, url in enumerate(target_urls, 1):
        print(f"\n[{i}/{len(target_urls)}] 处理中: {url}")
        res = process_single_url(url, args, today_str)
        
        if res["success"]:
            success_count += 1
            append_history(url, history_file)
        else:
            print(f"  -> [Error] 在 {res['stage']} 阶段失败: {res['error']}")
            log_error(url, f"Stage: {res['stage']}, Msg: {res['error']}")
            failed_items.append(url)

    # 自动重试逻辑 (同 v3.2)
    if failed_items and args.retry > 0:
        print(f"\n开始重试 {len(failed_items)} 个失败任务...")
        for i, url in enumerate(failed_items, 1):
            time.sleep(3)
            res = process_single_url(url, args, today_str)
            if res["success"]:
                success_count += 1
                append_history(url, history_file)
            
    print(f"\n--- 全部完成 ---")
    print(f"新处理成功: {success_count} / 本次任务: {len(target_urls)}")
    print(f"累计成功记录: {len(load_history(history_file))}")

if __name__ == "__main__":
    main()