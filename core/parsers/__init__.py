from .standard import StandardParser
from .image_detail import ImageDetailParser

def parse_html(html, url):
    """
    统一解析入口。使用策略模式尝试不同的解析器。
    """
    # 1. 总是先运行标准解析器，提取元数据 (Title, Date, Author)
    # 即使它找不到正文，元数据也是有用的
    std_parser = StandardParser()
    result = std_parser.parse(html, url)
    
    # 如果标准解析器找到了正文，直接返回
    if result and result.get('content_html'):
        return result
        
    # 2. 如果没找到正文，尝试 Image Detail 解析器 (Fail-Safe)
    img_parser = ImageDetailParser()
    img_result = img_parser.parse(html, url)
    
    if img_result and img_result.get('content_html'):
        # 合并结果：使用 ImageDetail 的正文，保留 Standard 的元数据
        print(f"  -> [Parser] 切换至图片频道解析策略")
        result['content_html'] = img_result['content_html']
        return result
        
    # 3. 未来扩展：VideoParser
    # vid_parser = VideoParser() ...
    
    # 彻底失败
    return None
