import re
import datetime
from bs4 import BeautifulSoup
from .base import BaseParser

class StandardParser(BaseParser):
    """
    标准图文解析器。
    负责解析普通的微信文章结构，以及提取通用的元数据（标题、日期、作者）。
    """
    
    def parse(self, html, url):
        soup = BeautifulSoup(html, "lxml")
        
        # --- 1. 元数据提取 (无论是否有正文，都尝试提取这些) ---
        
        # 标题 (Title Fallback Logic)
        title = "Untitled_Article"
        title_tag = soup.find("h1", class_="rich_media_title")
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            if title_text: title = title_text
        
        if title == "Untitled_Article":
            meta_og = soup.find("meta", property="og:title")
            if meta_og and meta_og.get("content"):
                title = meta_og["content"]
            else:
                meta_tw = soup.find("meta", property="twitter:title")
                if meta_tw and meta_tw.get("content"):
                    title = meta_tw["content"]

        # 发布日期
        publish_date = None
        ct_match = re.search(r'(?:var\s+ct|window\.ct)\s*=\s*["\\]?(\d{10})["\\]?', html)
        if ct_match:
            publish_date = datetime.datetime.fromtimestamp(int(ct_match.group(1))).strftime("%Y-%m-%d")
        
        if not publish_date:
            pt_match = re.search(r'publish_time\s*=\s*["\\]?(\d{4}-\d{2}-\d{2})["\\]?', html)
            if pt_match: publish_date = pt_match.group(1)
            
        # 作者
        author_tag = soup.find("a", class_="rich_media_meta rich_media_meta_nickname")
        author = author_tag.get_text(strip=True) if author_tag else "Unknown_Account"

        # --- 2. 正文提取 ---
        content_div = soup.find("div", class_="rich_media_content")
        if not content_div: content_div = soup.find(id="js_content")
        if not content_div: content_div = soup.find(id="img-content")
        
        content_html = str(content_div) if content_div else None
        
        return {
            "title": title,
            "author": author,
            "publish_date": publish_date,
            "content_html": content_html,
            "original_url": url
        }
