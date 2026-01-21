import os
import datetime
import argparse
import sys
from core.downloader import fetch_article
from core.converter import html_to_markdown
from core.file_manager import prepare_article_dir, save_markdown, sanitize_filename
from core.pdf_generator import generate_pdf

def parse_args():
    """解析命令行参数"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_input = os.path.join(base_dir, "input/urls.txt")
    default_output = os.path.join(base_dir, "output")

    parser = argparse.ArgumentParser(
        description="微信公众号文章批量下载工具 (WeChat Fav Downloader)",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=f"""
示例:
  python get_wx_gzh.py                          # 使用默认配置运行
  python get_wx_gzh.py -i my_urls.txt           # 指定输入文件
  python get_wx_gzh.py --no-pdf --no-images     # 仅下载 Markdown 文本
  python get_wx_gzh.py -u "Kevin" -o ./downloads # 指定用户名和下载目录
        """
    )
    
    parser.add_argument("-i", "--input", default=default_input, help="输入 URL 文件路径 (默认: input/urls.txt)")
    parser.add_argument("-o", "--output", default=default_output, help="输出目录路径 (默认: output)")
    parser.add_argument("-u", "--user", default="MyWeChatUser", help="微信用户名前缀 (默认: MyWeChatUser)")
    
    parser.add_argument("--no-images", action="store_true", help="禁用图片下载 (默认: 下载图片)")
    parser.add_argument("--no-pdf", action="store_true", help="禁用 PDF 生成 (默认: 生成 PDF)")
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    # 将命令行参数映射到配置变量
    INPUT_FILE = args.input
    OUTPUT_DIR = args.output
    WECHAT_USERNAME = args.user
    DOWNLOAD_IMAGES = not args.no_images
    GENERATE_PDF = not args.no_pdf
    
    print(f"--- 微信公众号文章下载器 v2.2 ---")
    print(f"配置信息:")
    print(f"  输入文件: {INPUT_FILE}")
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"  用户前缀: {WECHAT_USERNAME}")
    print(f"  图片下载: {'[开启]' if DOWNLOAD_IMAGES else '[关闭]'}")
    print(f"  PDF 生成: {'[开启]' if GENERATE_PDF else '[关闭]'}")
    print("-" * 30)
    
    if not os.path.exists(INPUT_FILE):
        print(f"[Error] 找不到输入文件: {INPUT_FILE}")
        print(f"请检查路径或使用 --input 指定正确的文件。")
        sys.exit(1)

    today_str = datetime.date.today().strftime("%Y-%m-%d")

    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    except Exception as e:
        print(f"[Error] 读取文件失败: {e}")
        sys.exit(1)
        
    if not urls:
        print("[Warning] 输入文件中没有找到有效的 URL。")
        return

    print(f"共发现 {len(urls)} 个链接，开始处理...")
    
    success_count = 0
    
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] 正在处理: {url}")
        
        # 1. 下载
        article_data = fetch_article(url)
        if not article_data:
            continue
            
        title = article_data['title']
        print(f"  -> 标题: {title}")
        
        # 2. 准备目录
        article_dir, assets_dir = prepare_article_dir(
            WECHAT_USERNAME, 
            today_str, 
            title, 
            OUTPUT_DIR
        )
        
        # 3. 转换 (Markdown + 图片下载 + 返回处理后的 HTML)
        md_content, processed_html = html_to_markdown(
            article_data['content_html'], 
            title,
            article_data['original_url'],
            assets_dir=assets_dir if DOWNLOAD_IMAGES else None,
            download_images=DOWNLOAD_IMAGES
        )
        
        # 4. 保存 Markdown
        safe_title = sanitize_filename(title)
        md_path = os.path.join(article_dir, f"{safe_title}.md")
        if save_markdown(md_path, md_content):
            print(f"  -> [OK] Markdown 保存成功")
        
        # 5. 生成 PDF
        if GENERATE_PDF:
            pdf_path = os.path.join(article_dir, f"{safe_title}.pdf")
            if generate_pdf(processed_html, title, pdf_path, assets_dir):
                print(f"  -> [OK] PDF 生成成功")
            else:
                print(f"  -> [Fail] PDF 生成失败")

        success_count += 1

    print(f"\n--- 处理完成 ---")
    print(f"成功处理: {success_count} / 总计: {len(urls)}")
    print(f"结果保存在: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()