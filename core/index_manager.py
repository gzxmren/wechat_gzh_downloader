import os
import datetime
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