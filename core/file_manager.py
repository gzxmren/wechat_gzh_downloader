import os
import re

def sanitize_filename(name):
    """清理文件名中的非法字符"""
    return re.sub(r'[\\/*?:"><|]', "", name).strip()

def prepare_article_dir(user_name, date_str, title, base_output_dir="output"):
    """
    为单篇文章准备独立的目录结构。
    
    Returns:
        tuple: (article_dir, assets_dir)
        - article_dir: 文章根目录
        - assets_dir: 图片存放目录
    """
    # 1. 批次目录 (用户名 + 日期)
    batch_folder = f"{user_name}_{date_str}_Articles"
    
    # 2. 文章独立目录
    safe_title = sanitize_filename(title)
    if len(safe_title) > 50:
        safe_title = safe_title[:50] + "..."
    
    article_dir = os.path.join(base_output_dir, batch_folder, safe_title)
    assets_dir = os.path.join(article_dir, "assets")
    
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
        
    return article_dir, assets_dir

def save_markdown(file_path, content):
    """
    保存 Markdown 内容到指定路径。
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"[Error] Failed to save file {file_path}: {e}")
        return False