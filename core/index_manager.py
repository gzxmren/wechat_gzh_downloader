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

    扫描 output 目录，基于 metadata.json 重建全局索引 HTML。

    """

    index_path = os.path.join(output_root, "index.html")

    

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

                        if file.endswith(".html") and file != "index.html":

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

                print(f"[Warning] Failed to read metadata in {root}: {e}")



    records.sort(key=lambda x: x["date"], reverse=True)

    

    # HTML 模板

    html_content = f"""<!DOCTYPE html>

<html lang="zh-CN">

<head>

    <meta charset="UTF-8">

    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>微信文章归档索引</title>

    <style>

        :root {{ --primary-color: #07c160; --text-color: #333; --bg-color: #f5f5f5; }}

        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: var(--bg-color); color: var(--text-color); margin: 0; padding: 20px; }}

        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}

        h1 {{ text-align: center; color: var(--primary-color); margin-bottom: 10px; }}

        .stats {{ text-align: center; color: #666; margin-bottom: 30px; font-size: 0.9em; }}

        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}

        th {{ background-color: #f8f9fa; text-align: left; padding: 12px; border-bottom: 2px solid #eee; }}

        td {{ padding: 12px; border-bottom: 1px solid #eee; }}

        tr:hover {{ background-color: #fcfcfc; }}

        .btn {{ display: inline-block; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-size: 0.85em; transition: 0.2s; }}

        .btn-read {{ background-color: var(--primary-color); color: white; }}

        .btn-read:hover {{ background-color: #06ad56; }}

        .btn-orig {{ color: #666; border: 1px solid #ddd; margin-left: 5px; }}

        .btn-orig:hover {{ background-color: #f0f0f0; }}

        .author {{ color: #888; font-size: 0.9em; }}

        .date {{ font-family: monospace; color: #555; }}

    </style>

</head>

<body>

    <div class="container">

        <h1>微信文章归档索引</h1>

        <div class="stats">共收录 {len(records)} 篇文章 | 最后更新: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>

        <table>

            <thead>

                <tr>

                    <th width="120">发布日期</th>

                    <th>文章标题</th>

                    <th width="150">本地阅读</th>

                </tr>

            </thead>

            <tbody>

"""

    for r in records:

        html_content += f"""

                <tr>

                    <td class="date">{r['date']}</td>

                    <td>

                        <div style="font-weight: 500;">{r['title']}</div>

                        <div class="author">{r['author']}</div>

                    </td>

                    <td>

                        <a href="./{quote(r['path'])}" class="btn btn-read">阅读</a>

                        <a href="{r['url']}" target="_blank" class="btn btn-orig">原文</a>

                    </td>

                </tr>"""



    html_content += """

            </tbody>

        </table>

    </div>

</body>

</html>"""

    

    try:

        with open(index_path, "w", encoding="utf-8") as f:

            f.write(html_content)

        print(f"[Index] 全局索引已生成: {index_path}")

        return True

    except Exception as e:

        print(f"[Error] 索引生成失败: {e}")

        return False
