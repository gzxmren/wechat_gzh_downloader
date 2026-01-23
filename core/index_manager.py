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

def generate_global_index(output_root):
    """
    扫描 output 目录，基于 metadata.json 重建全局索引。
    """
    index_path = os.path.join(output_root, "README.md") # 索引文件放在 output 根目录
    
    records = []
    
    # 遍历所有子目录
    for root, dirs, files in os.walk(output_root):
        if "metadata.json" in files:
            meta_path = os.path.join(root, "metadata.json")
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    
                    # 寻找同级目录下的 MD 文件
                    md_filename = f"{meta['title']}.md"
                    # 这里我们需要一个相对路径，从 output_root 开始
                    # root 是 output/Title_Date/
                    # 我们需要 output/Title_Date/Title.md 相对于 output/ 的路径
                    # 即 Title_Date/Title.md
                    
                    # 修正：文件名可能经过了 sanitize_filename 处理
                    # 最安全的方法是查找当前目录下唯一的 .md 文件 (排除 README.md)
                    target_md = None
                    for file in files:
                        if file.endswith(".md") and file != "README.md":
                            target_md = file
                            break
                    
                    if target_md:
                        rel_dir = os.path.relpath(root, output_root)
                        rel_path = os.path.join(rel_dir, target_md).replace("\\", "/")
                        
                        records.append({
                            "date": meta.get("publish_date", "Unknown"),
                            "title": meta.get("title", "No Title"),
                            "author": meta.get("author", "Unknown"),
                            "path": rel_path,
                            "url": meta.get("original_url", "")
                        })
            except Exception as e:
                print(f"[Warning] Failed to read metadata in {root}: {e}")

    # 按日期倒序排序
    records.sort(key=lambda x: x["date"], reverse=True)
    
    # 写入文件
    try:
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(f"# 文章归档 (Total: {len(records)})\n\n")
            f.write(f"> 最后更新: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("| 发布日期 | 文章标题 | 公众号 | 本地阅读 | 原文 |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")
            
            for r in records:
                safe_title = r["title"].replace("|", "\|")
                safe_author = r["author"].replace("|", "\|")
                url_safe_path = quote(r["path"])
                f.write(f"| {r['date']} | {safe_title} | {safe_author} | [阅读](./{url_safe_path}) | [链接]({r['url']}) |\n")
                
        print(f"[Index] 全局索引已重建: {index_path}")
        return True
    except Exception as e:
        print(f"[Error] 索引重建失败: {e}")
        return False