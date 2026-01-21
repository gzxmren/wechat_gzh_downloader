import sqlite3
import xml.etree.ElementTree as ET
import os

def parse_favorite_db(db_path):
    """
    解析解密后的微信收藏夹数据库。
    
    Returns:
        list: 包含 {'title': str, 'url': str} 的字典列表
    """
    if not os.path.exists(db_path):
        print(f"[Error] 数据库文件不存在: {db_path}")
        return []

    articles = []
    conn = None
    
    try:
        # 微信收藏夹数据通常存储在 FavItems 表中
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # type = 3 通常代表“网页”或“公众号文章”
        # xml 字段存储了详细的元数据
        query = "SELECT xml FROM FavItems WHERE type = 3"
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            xml_str = row[0]
            if not xml_str:
                continue
                
            try:
                # 微信的 XML 有时包含编码声明或特殊字符，直接解析可能报错
                # 尝试简单清理后解析
                root = ET.fromstring(xml_str)
                
                # 微信收藏 XML 结构通常为:
                # <favitem ...> <item> <title>标题</title> <link>URL</link> </item> </favitem>
                item_node = root.find('item')
                if item_node is not None:
                    title_node = item_node.find('title')
                    link_node = item_node.find('link')
                    
                    if link_node is not None and link_node.text:
                        articles.append({
                            'title': title_node.text if title_node is not None else "Untitled",
                            'url': link_node.text
                        })
            except Exception as xml_err:
                # 忽略个别解析失败的条目
                continue
                
    except Exception as e:
        print(f"[Error] 解析数据库失败: {e}")
    finally:
        if conn:
            conn.close()
            
    return articles

def save_urls_to_file(articles, output_path):
    """
    将提取到的 URL 保存到 input/urls.txt，供后续下载引擎使用
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for item in articles:
                f.write(f"{item['url']}\n")
        return True
    except Exception as e:
        print(f"[Error] 保存 URL 列表失败: {e}")
        return False
