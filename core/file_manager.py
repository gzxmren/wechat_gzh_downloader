import os
import re
import json
import aiofiles

def sanitize_filename(name):
    """清理文件名中的非法字符"""
    name = re.sub(r'[\\/*?:"><|]', "_", name)
    name = re.sub(r'^\.|。$', "_", name)
    name = re.sub(r'^\s+|\s+$', '', name)
    name = re.sub(r'\s+', ' ', name)
    if len(name) > 100:
        name = name[:100]
    return name.strip()

def prepare_article_dir(user_name, date_str, title, base_output_dir="output"):
    """
    为单篇文章准备独立的目录结构。
    """
    safe_title = sanitize_filename(title)
    folder_name = f"{safe_title}_{date_str}"
    article_dir = os.path.join(base_output_dir, folder_name)
    assets_dir = os.path.join(article_dir, "assets")
    
    # 目录创建通常很快，可以保持同步，或者使用 loop.run_in_executor
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
        
    return article_dir, assets_dir

async def save_markdown(file_path, content):
    """
    异步保存 Markdown 内容。
    """
    try:
        async with aiofiles.open(file_path, mode='w', encoding="utf-8") as f:
            await f.write(content)
        return True
    except Exception as e:
        print(f"[Error] Failed to save file {file_path}: {e}")
        return False

async def save_metadata(file_path, metadata):
    """
    异步保存元数据到 JSON 文件。
    """
    try:
        content = json.dumps(metadata, ensure_ascii=False, indent=2)
        async with aiofiles.open(file_path, mode='w', encoding="utf-8") as f:
            await f.write(content)
        return True
    except Exception as e:
        print(f"[Error] Failed to save metadata {file_path}: {e}")
        return False