from typing import List, Type, Optional
from .base import BaseParser

_PARSER_REGISTRY: List[Type[BaseParser]] = []

def register_parser(cls):
    """
    装饰器：注册解析器类。
    """
    _PARSER_REGISTRY.append(cls)
    return cls

def find_and_parse(html: str, url: str) -> Optional[dict]:
    """
    遍历注册表，尝试每一个适用的解析器，直到有一个成功解析并返回数据。
    """
    for parser_cls in _PARSER_REGISTRY:
        parser = parser_cls()
        if parser.can_handle(html, url):
            try:
                data = parser.parse(html, url)
                if data:
                    return data
            except Exception as e:
                from . import logger # 延迟导入避免循环
                import logging
                logging.getLogger("WeChatDownloader").warning(f"{parser_cls.__name__} 解析失败: {e}")
                continue
    return None
