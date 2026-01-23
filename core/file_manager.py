import os
import re
import json

def sanitize_filename(name):
    """清理文件名中的非法字符"""
    # 允许中文、英文、数字和部分符号
    # 替换所有非法字符为下划线
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    # 替换文件名中不允许在开头或结尾出现的字符
    name = re.sub(r'^\.|\.$', "_", name)
    name = re.sub(r'^\s+|\s+$', '', name) # 移除前后空格
    # 确保没有连续的空格
    name = re.sub(r'\s+', ' ', name)
    # 截断标题到100字符，这是针对文件名的长度限制
    if len(name) > 100:
        name = name[:100]
    return name.strip()


def prepare_article_dir(user_name, date_str, title, base_output_dir="output"):
    """
    为单篇文章准备独立的目录结构。
    结构: output/{Title}_{Date}/
    """
    # 清理标题，防止路径过长或包含非法字符
    safe_title = sanitize_filename(title)
        
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

def save_metadata(file_path, metadata):
    """
    保存元数据到 JSON 文件。
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[Error] Failed to save metadata {file_path}: {e}")
        return False
