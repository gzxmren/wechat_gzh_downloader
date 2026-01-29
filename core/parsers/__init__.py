from .registry import find_and_parse, register_parser
from .base import BaseParser

# 显式导入子模块以触发注册
# 注意：导入顺序决定了解析器的优先级 (Registry Order)
from . import image_detail
from . import standard
