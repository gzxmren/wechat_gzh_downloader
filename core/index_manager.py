import os
import datetime
import json
from urllib.parse import quote
from jinja2 import Environment, FileSystemLoader
from .config import settings
from .logger import logger

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
    # test github sync
    
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
                        
                        # 提取下载时间，若不存在则回退到发布日期
                        display_date = meta.get("download_time", meta.get("publish_date", "Unknown"))
                        
                        records.append({
                            "date": display_date,
                            "publish_date": meta.get("publish_date", "Unknown"),
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

    # 按显示日期（现在是下载时间）从新到旧排序
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

    # 5. 准备全量数据 JSON 字符串 (用于直接嵌入 HTML 绕过 CORS 限制)
    all_records_json = json.dumps(records, ensure_ascii=False)
    
    # 6. 生成页面
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
                all_records_json=all_records_json,  # 注入全量数据
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

    # 6. 导出全量数据 JSON (用于前端搜索和排序)
    json_path = os.path.join(output_root, "all_records.json")
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        logger.info(f"已导出全量数据到 all_records.json ({total_records} 条记录)")
    except Exception as e:
        logger.warning(f"导出 JSON 失败: {e}")
    
    logger.info(f"全局索引已生成，共 {total_pages} 页")
    return True
