from abc import ABC, abstractmethod
import re
import datetime
import html as html_lib
from bs4 import BeautifulSoup

class BaseParser(ABC):
    """
    所有解析器的基类。
    """
    
    @abstractmethod
    def can_handle(self, html, url) -> bool:
        """
        判断该解析器是否适用于当前文章。
        """
        pass

    @abstractmethod
    def parse(self, html, url):
        """
        解析 HTML 内容。
        """
        pass

    def decode_wechat_text(self, text: str) -> str:
        """
        处理微信特有的 hex 转义 (如 \x26) 和标准 HTML 实体。
        使用正则替换以避免破坏已有的非 ASCII 字符（如中文）。
        """
        if not text: return text
        
        # 1. 处理 \xHH 格式的转义 (使用正则回调，安全且不影响中文)
        def _hex_decode(match):
            try:
                return chr(int(match.group(1), 16))
            except Exception:
                return match.group(0)
                
        if "\\x" in text:
            text = re.sub(r'\\x([0-9a-fA-F]{2})', _hex_decode, text)
            
        # 2. 处理标准的 HTML 实体 (如 &lt; -> <)
        return html_lib.unescape(text)

    def extract_common_metadata(self, html):
        """
        提取通用的元数据（标题、日期、作者）。
        """
        soup = BeautifulSoup(html, "lxml")
        
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
        
        title = self.decode_wechat_text(title)

        # 发布日期
        publish_date = None
        ct_match = re.search(r'(?:var\s+ct|window\.ct)\s*=\s*["\\]?(\d{10})["\\]?', html)
        if ct_match:
            publish_date = datetime.datetime.fromtimestamp(int(ct_match.group(1))).strftime("%Y-%m-%d")
        
        if not publish_date:
            pt_match = re.search(r'publish_time\s*=\s*["\\]?(\d{4}-\d{2}-\d{2})["\\]?', html)
            if pt_match: publish_date = pt_match.group(1)
            
        # 作者
        author_tag = soup.find(class_="rich_media_meta rich_media_meta_nickname")
        author = author_tag.get_text(strip=True) if author_tag else "Unknown_Account"
        author = self.decode_wechat_text(author)
        
        return title, author, publish_date
