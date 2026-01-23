from abc import ABC, abstractmethod

class BaseParser(ABC):
    """
    所有解析器的基类。
    """
    
    @abstractmethod
    def parse(self, html, url):
        """
        解析 HTML 内容。
        
        Args:
            html (str): 网页源码
            url (str): 文章 URL
            
        Returns:
            dict: 包含 title, author, publish_date, content_html, original_url 的字典
            None: 如果解析失败
        """
        pass
