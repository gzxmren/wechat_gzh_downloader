import re
import datetime
from .base import BaseParser
from .registry import register_parser

@register_parser
class ShareTextParser(BaseParser):
    """
    针对微信“纯文字分享/发表动态” (common_share_text_content) 的解析器。
    """
    
    def can_handle(self, html, url) -> bool:
        # 特征：引入了 common_share_text_content 脚本
        return 'common_share_text_content' in html

    def parse(self, html, url):
        # 1. 提取标题 (优先使用 og:title)
        title, author, publish_date = self.extract_common_metadata(html)
        
        # 2. 提取更精准的作者 (JS 变量提取兜底)
        if author == "Unknown_Account":
            author_match = re.search(
                r'nick_name\s*=\s*(?:\(xml\s*\?\s*getXmlValue\(\'nick_name\.DATA\'\)\s*:\s*)?[\'"]([^\'"]+)[\'"]', 
                html
            )
            if author_match:
                author = self.decode_wechat_text(author_match.group(1))
                
        # 3. 提取发布日期
        if not publish_date:
            ct_match = re.search(
                r'(?:d\.ct|window\.ct|var\s+ct)\s*=\s*(?:[\'"]?[^\'"]*[\'"]|["\\])?(\d{10})', 
                html
            )
            if ct_match:
                publish_date = datetime.datetime.fromtimestamp(int(ct_match.group(1))).strftime("%Y-%m-%d")
        
        if not title or title == "Untitled_Article":
            return None
            
        # 4. 纯文字动态的 title 就是它的全部正文内容
        content_html = f'<div class="rich_media_content" id="js_content"><p>{title}</p></div>'

        return {
            "title": title,
            "author": author,
            "publish_date": publish_date,
            "content_html": content_html,
            "original_url": url,
            "type": "share_text"
        }
