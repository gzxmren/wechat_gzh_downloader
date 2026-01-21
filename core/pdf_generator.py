import pdfkit
import os

def generate_pdf(html_content, title, output_path, assets_dir):
    """
    将微信文章 HTML 转换为 PDF 文件。
    
    Args:
        html_content (str): 已经过图片本地化处理的 HTML 片段 (js_content)
        title (str): 文章标题
        output_path (str): PDF 保存的完整路径
        assets_dir (str): 本地图片目录的绝对路径，用于渲染
    """
    # 1. 构造完整的 HTML 文档
    # 注意：在 f-string 中，CSS 的花括号必须双写 {{ }} 以转义
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>
            body {{ font-family: "PingFang SC", "Microsoft YaHei", sans-serif; line-height: 1.6; color: #333; padding: 20px; }}
            img {{ max-width: 100%; height: auto; display: block; margin: 10px 0; }}
            .rich_media_title {{ font-size: 24px; font-weight: bold; margin-bottom: 20px; }}
            blockquote {{ border-left: 4px solid #eee; padding-left: 10px; color: #666; }}
            
            /* 关键修复：强制显示内容，覆盖微信默认的 visibility: hidden */
            #js_content, .rich_media_content {{ visibility: visible !important; opacity: 1 !important; }}
            
            /* 代码块与引用样式增强 */
            pre, code {{ font-family: Consolas, "Courier New", monospace; background-color: #f6f8fa; padding: 3px; border-radius: 3px; }}
            pre {{ display: block; padding: 10px; overflow-x: auto; white-space: pre-wrap; border: 1px solid #ddd; background-color: #f6f8fa; color: #333; }}
            pre code {{ padding: 0; border: none; background: none; }}
            
            /* 微信特定的代码块容器修复 */
            .code-snippet__rich_wrap, section[data-role="code"] {{ 
                background-color: #f6f8fa !important; 
                border: 1px solid #e1e4e8 !important;
                padding: 10px !important;
                margin: 10px 0 !important;
                border-radius: 4px !important;
                display: block !important;
                visibility: visible !important;
            }}
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
    
    # 2. 修正图片路径：pdfkit 渲染时需要绝对路径才能找到 assets 里的图片
    if assets_dir:
        abs_assets_dir = os.path.abspath(assets_dir)
        # 将 src="assets/xxx" 替换为 src="file:///abs/path/assets/xxx"
        # 注意：这里要处理可能的斜杠方向问题，但在 Linux 下通常没问题
        full_html = full_html.replace('src="assets/', f'src="file://{abs_assets_dir}/')
    
    # 3. 配置选项
    options = {
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': "UTF-8",
        'enable-local-file-access': None, # 关键：允许读取本地 assets 文件夹
        'no-outline': None,
        'quiet': ''
    }
    
    try:
        pdfkit.from_string(full_html, output_path, options=options)
        return True
    except Exception as e:
        print(f"[Error] PDF conversion failed: {e}")
        if "wkhtmltopdf" in str(e).lower():
            print(">>> 提示: 请确保系统已安装 wkhtmltopdf。在 Ubuntu/WSL 上运行: sudo apt install wkhtmltopdf")
        return False