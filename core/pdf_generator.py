import pdfkit
import os

def generate_pdf(html_content, title, output_path, assets_dir):
    """
    将微信文章 HTML 转换为 PDF。具备环境自适应能力：
    优先尝试生成带目录和页码的高级 PDF，若环境不支持则退化为普通 PDF。
    """
    # 1. 构造完整的 HTML 文档
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>
            @page {{ margin: 20mm; }}
            body {{ 
                font-family: "PingFang SC", "Microsoft YaHei", sans-serif; 
                line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto;
            }}
            h1, h2, h3, h4, h5, h6 {{ page-break-after: avoid; color: #2c3e50; }}
            img {{ max-width: 100%; height: auto; display: block; margin: 15px 0; border-radius: 4px; }}
            .rich_media_title {{ font-size: 28px; font-weight: bold; margin-bottom: 30px; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
            pre, blockquote {{ page-break-inside: avoid; }}
            blockquote {{ border-left: 5px solid #dfe2e5; padding: 10px 15px; color: #6a737d; background: #fafbfc; margin: 20px 0; }}
            #js_content, .rich_media_content {{ visibility: visible !important; opacity: 1 !important; }}
            pre {{ display: block; padding: 16px; overflow-x: auto; white-space: pre-wrap; background-color: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 6px; font-size: 13px; }}
        </style>
    </head>
    <body>
        <div class="rich_media_title">{title}</div>
        <div class="content">
            {html_content}
        </div>
    </body>
    </html>
    """
    
    # 2. 修正图片路径
    if assets_dir:
        abs_assets_dir = os.path.abspath(assets_dir)
        full_html = full_html.replace('src="assets/', f'src="file://{abs_assets_dir}/')
    
    # 3. 基础配置
    base_options = {
        'page-size': 'A4',
        'encoding': "UTF-8",
        'enable-local-file-access': None,
        'quiet': ''
    }
    
    # 4. 高级配置（可能在某些 Linux 环境下不被支持）
    advanced_options = {
        **base_options,
        'footer-center': '[page] / [toPage]',
        'footer-font-size': '9',
        'outline-depth': '3',
    }
    
    toc = {
        'toc-header-text': '目录',
        'disable-dotted-lines': None,
    }
    
    try:
        # 尝试一：带目录和页码
        pdfkit.from_string(full_html, output_path, options=advanced_options, toc=toc)
        return True
    except Exception as e:
        # 尝试二：退化为普通 PDF
        if "unpatched qt" in str(e).lower() or "switch" in str(e).lower():
            try:
                pdfkit.from_string(full_html, output_path, options=base_options)
                print(f"  [Info] 环境限制，已生成不带目录和页码的普通 PDF")
                return True
            except Exception as e2:
                print(f"[Error] PDF conversion fallback failed: {e2}")
        else:
            print(f"[Error] PDF conversion failed: {e}")
        return False