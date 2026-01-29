import os
import datetime
import json
from urllib.parse import quote

def init_index_file(index_path):
    """初始化索引文件头"""
    if not os.path.exists(index_path):
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("# 微信文章归档索引 (WeChat Article Index)\n\n")
            f.write(f"最后更新: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("| 发布日期 | 文章标题 | 作者 | 本地路径 | 原始链接 |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")

def update_index(index_path, date_str, title, author, relative_path, url):
    """
    追加一条索引记录。
    
    Args:
        index_path (str): index.md 的完整路径
        date_str (str): 文章发布日期
        title (str): 文章标题
        author (str): 公众号名称
        relative_path (str): Markdown 文件的相对路径 (便于点击)
        url (str): 原始 URL
    """
    # 确保文件存在且有表头
    if not os.path.exists(index_path):
        init_index_file(index_path)
        
    # 处理标题中的管道符，防止破坏 Markdown 表格
    safe_title = title.replace("|", "||")
    safe_author = author.replace("|", "||")
    
    # 关键修复：对路径进行 URL 编码 (处理空格和中文)
    # relative_path 可能是 "output/User_Date/Title.md"
    # 我们需要将其转换为 URL 安全的格式
    url_safe_path = quote(relative_path)
    
    # 构造相对路径链接 [点击查看](./output/...)
    local_link = f"[查看本地]({url_safe_path})"
    
    # 构造行数据
    line = f"| {date_str} | {safe_title} | {safe_author} | {local_link} | [原文]({url}) |\n"
    
    # 追加模式写入
    try:
        with open(index_path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        print(f"[Warning] 更新索引失败: {e}")

import os
import datetime
import json
from urllib.parse import quote
from jinja2 import Environment, FileSystemLoader
from .config import settings
from .logger import logger

def init_index_file(index_path):
    """
    Deprecated: Initialization is now handled via template rendering.
    Kept for backward compatibility if needed by other modules (unlikely).
    """
    pass

def update_index(index_path, date_str, title, author, relative_path, url):
    """
    追加一条索引记录 (Legacy Mode).
    注意：在 v4.6+ 分页模式下，该函数仅用于单次追加，并不推荐混用。
    """
    # 简单的追加逻辑保留，但不再是核心路径
    if not os.path.exists(index_path):
        with open(index_path, "w", encoding="utf-8") as f:
             f.write(f"| {date_str} | {title} | {author} | [Link]({relative_path}) | [Orig]({url}) |\n")
    else:
        try:
            with open(index_path, "a", encoding="utf-8") as f:
                f.write(f"| {date_str} | {title} | {author} | [Link]({relative_path}) | [Orig]({url}) |\n")
        except Exception as e:
            logger.warning(f"更新索引失败: {e}")

def generate_global_index(output_root):
    """
    扫描 output 目录，基于 metadata.json 重建全局索引 HTML。
    使用 Jinja2 模板引擎与 core.config 配置。
    """
    # 1. 准备环境
    page_size = settings.PAGE_SIZE
    
    # 设置 Jinja2 环境
    env = Environment(loader=FileSystemLoader(str(settings.TEMPLATE_DIR)))
    # 注册 URL 编码过滤器
    env.filters['url_quote'] = quote
    
    try:
        template = env.get_template('index.html')
    except Exception as e:
        logger.error(f"无法加载模板 index.html: {e}")
        return False

    # 2. 收集数据
    records = []
    for root, dirs, files in os.walk(output_root):
        if "metadata.json" in files:
            meta_path = os.path.join(root, "metadata.json")
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    
                    # 寻找 HTML 文件
                    target_file = None
                    for file in files:
                        if file.endswith(".html") and file != "index.html" and not file.startswith("index_"):
                            target_file = file
                            break
                    
                    if target_file:
                        rel_dir = os.path.relpath(root, output_root)
                        rel_path = os.path.join(rel_dir, target_file).replace("\\", "/")
                        
                        records.append({
                            "date": meta.get("publish_date", "Unknown"),
                            "title": meta.get("title", "No Title"),
                            "author": meta.get("author", "Unknown"),
                            "path": rel_path,
                            "url": meta.get("original_url", "")
                        })
            except Exception as e:
                logger.warning(f"Failed to read metadata in {root}: {e}")

    # --- 去重逻辑 (Deduplication) ---
    seen_urls = set()
    unique_records = []
    for r in records:
        url = r.get("url")
        # 1. 如果有 URL，基于 URL 去重
        if url:
            if url not in seen_urls:
                seen_urls.add(url)
                unique_records.append(r)
        # 2. 如果没有 URL (异常数据)，则保留该记录
        else:
            unique_records.append(r)
    
    records = unique_records
    # -------------------------------

    records.sort(key=lambda x: x["date"], reverse=True)
    
    total_records = len(records)
    if total_records == 0:
        logger.info("No records found to index.")
        return True

    # 3. 分页计算
    total_pages = (total_records + page_size - 1) // page_size
    logger.info(f"Generating {total_pages} pages for {total_records} records (size={page_size}).")

    # 4. 清理旧的分页文件
    for f in os.listdir(output_root):
        if f.startswith("index_") and f.endswith(".html"):
            try:
                os.remove(os.path.join(output_root, f))
            except Exception:
                pass

    # 5. 生成页面
    update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for page in range(1, total_pages + 1):
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_records = records[start_idx:end_idx]
        
        filename = "index.html" if page == 1 else f"index_{page}.html"
        file_path = os.path.join(output_root, filename)
        
        # 渲染模板
        try:
            html_content = template.render(
                records=page_records,
                current_page=page,
                total_pages=total_pages,
                total_records=total_records,
                update_time=update_time
            )
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
                
        except Exception as e:
            logger.error(f"Failed to render/write {filename}: {e}")
            return False

    logger.info(f"全局索引已生成，共 {total_pages} 页")
    return True
