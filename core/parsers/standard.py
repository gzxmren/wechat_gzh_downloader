from bs4 import BeautifulSoup
from .base import BaseParser
from .registry import register_parser

@register_parser
class StandardParser(BaseParser):
    """
    标准图文解析器。
    负责解析普通的微信文章结构，以及提取通用的元数据（标题、日期、作者）。
    作为 Fallback 解析器，应当最后被注册。
    """
    
    def can_handle(self, html, url) -> bool:
        # 作为一个通用的 Fallback，只要不是明确无法处理的（比如空内容），都尝试处理
        # 或者更严格一点：必须包含某些 ID
        return True

    def parse(self, html, url):
        # 1. 提取通用元数据
        title, author, publish_date = self.extract_common_metadata(html)

        # 2. 正文提取
        soup = BeautifulSoup(html, "lxml")
        content_div = soup.find("div", class_="rich_media_content")
        if not content_div: content_div = soup.find(id="js_content")
        if not content_div: content_div = soup.find(id="img-content")
        
        content_html = str(content_div) if content_div else None
        
        # 如果连正文都找不到，且没有标题，可能是无效页面
        if not content_html and title == "Untitled_Article":
            return None

        return {
            "title": title,
            "author": author,
            "publish_date": publish_date,
            "content_html": content_html,
            "original_url": url,
            "type": "standard"
        }