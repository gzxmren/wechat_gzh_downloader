import os
import aiofiles

async def save_full_html(html_content, title, output_path, assets_dir):
    """
    异步将处理后的 HTML 内容保存为独立的 HTML 文件。
    """
    # 构造完整的 HTML 文档
    full_html_doc = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>
            body {{ 
                font-family: "PingFang SC", "Microsoft YaHei", sans-serif; 
                line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto;
                padding: 20px;
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

    # 修正图片路径：HTML 文件中需要相对路径
    if assets_dir:
        # 修正可能存在的全路径引用
        full_html_doc = full_html_doc.replace(f'src="file://{os.path.abspath(assets_dir)}/', 'src="assets/')

    try:
        async with aiofiles.open(output_path, mode='w', encoding="utf-8") as f:
            await f.write(full_html_doc)
        return True
    except Exception as e:
        print(f"[Error] 保存 HTML 文件失败: {e}")
        return False