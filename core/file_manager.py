import os
import re

def sanitize_filename(name):
    """清理文件名中的非法字符"""
    return re.sub(r'[\\/*?:"><|]', "", name).strip()

def prepare_article_dir(user_name, date_str, title, base_output_dir="output"):
    """
    为单篇文章准备独立的目录结构。
    结构: output/{Title}_{Date}/
    """
    # 清理标题，防止路径过长或包含非法字符
    safe_title = sanitize_filename(title)
    if len(safe_title) > 100: # 稍微放宽长度限制，但仍需截断
        safe_title = safe_title[:100] + "..."
        
    # 构造扁平化文件夹名称: 标题_日期
    folder_name = f"{safe_title}_{date_str}"
    
    # 最终完整路径
    article_dir = os.path.join(base_output_dir, folder_name)
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