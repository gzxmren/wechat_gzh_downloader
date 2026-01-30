import re
from .base import BaseParser
from .registry import register_parser

@register_parser
class ImageDetailParser(BaseParser):
    """
    针对微信“图片频道” (image_detail) 的解析器。
    使用括号平衡算法和对象块隔离逻辑。
    """
    
    def can_handle(self, html, url) -> bool:
        clean_html = re.sub(r'\s+', '', html)
        return 'picture_page_info_list=[' in clean_html or 'window.picture_page_info_list=[' in clean_html

    def parse(self, html, url):
        # 1. 提取通用元数据
        title, author, publish_date = self.extract_common_metadata(html)

        # 2. 全局预处理：移除所有空白字符
        clean_html = re.sub(r'\s+', '', html)
        
        # 3. 特征检测与定位
        start_marker = 'picture_page_info_list=['
        start_idx = clean_html.find(start_marker)
        
        if start_idx == -1:
            start_marker = 'window.picture_page_info_list=['
            start_idx = clean_html.find(start_marker)
            
        if start_idx == -1:
            return None
            
        # 4. 精确截取：括号平衡算法
        array_start = start_idx + len(start_marker) - 1 # 指向 '['
        bracket_count = 0
        array_end = -1
        
        for i in range(array_start, len(clean_html)):
            char = clean_html[i]
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    array_end = i + 1
                    break
        
        if array_end == -1:
            # Fallback: 如果没找到结束符，截取一段固定长度
            target_str = clean_html[array_start:array_start+100000]
        else:
            target_str = clean_html[array_start:array_end]
        
        # 移除最外层的 [ ]
        if target_str.startswith('['): target_str = target_str[1:]
        if target_str.endswith(']'): target_str = target_str[:-1]

        # 5. 拆分对象块
        raw_blocks = []
        curr_block = ""
        nest_level = 0
        for char in target_str:
            if char == '{': nest_level += 1
            if nest_level > 0: curr_block += char
            if char == '}':
                nest_level -= 1
                if nest_level == 0:
                    raw_blocks.append(curr_block)
                    curr_block = ""

        # 6. 提取 URL
        image_list = []
        seen_urls = set()
        
        for block in raw_blocks:
            # 在块内查找所有可能的 URL (因为可能存在空的占位符 cdn_url)
            block_urls = re.findall(r'cdn_url:(?:JsDecode\()?(?:\'|\")(.*?)(?:\'|\")', block)
            
            img_url = None
            for u in block_urls:
                if u and u.strip():
                    img_url = u
                    break
            
            if img_url:
                # 强力去重
                clean_key = img_url.split('://')[-1]
                clean_key = re.sub(r'[\s\r\n\t]', '', clean_key)
                
                if clean_key not in seen_urls:
                    seen_urls.add(clean_key)
                    image_list.append(img_url)

        if not image_list:
            return None
            
        # 7. 提取摘要/导语 (Description)
        desc_text = ""
        meta_desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html, re.IGNORECASE)
        if meta_desc_match:
            raw_desc = meta_desc_match.group(1)
            # 处理 hex 转义和 HTML 实体
            desc_text = self.decode_wechat_text(raw_desc)
            # 统一换行符
            desc_text = desc_text.replace('\n', '<br/>')
            
        # 8. 尝试提取正文 (混合模式支持)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        text_content_html = ""
        content_div = soup.find(id="js_content")
        if content_div:
            # 移除样式中的 hidden/opacity，确保显示
            if content_div.has_attr("style"):
                style = content_div["style"]
                style = style.replace("visibility: hidden", "visibility: visible")
                style = style.replace("opacity: 0", "opacity: 1")
                content_div["style"] = style
            text_content_html = str(content_div)

        # 9. 构建 HTML
        # 优先显示正文，然后是图片列表（或者反过来，视情况而定，通常正文在前）
        content_html = '<div class="rich_media_content" id="js_content_wrapper" style="visibility: visible;">'
        
        has_body_text = False
        if content_div:
            has_body_text = bool(content_div.get_text(strip=True))

        if desc_text and not has_body_text: # 如果有实质正文，通常不需要单独显示 meta description
            content_html += f'<div class="image_channel_desc" style="margin-bottom: 20px; font-size: 16px; line-height: 1.6; color: #333;">{desc_text}</div>'
            
        if text_content_html:
            content_html += text_content_html
            content_html += "<br/><hr/><br/>" # 分隔符

        for cur_url in image_list:
            if '\\x' in cur_url or '\\u' in cur_url:
                try: cur_url = cur_url.encode('utf-8').decode('unicode_escape')
                except: pass
            content_html += f'<p><img data-src="{cur_url}" src="{cur_url}" style="max-width: 100%; height: auto; display: block; margin: 0 auto;" /></p><br/>'
        content_html += '</div>'
        
        return {
            "title": title,
            "author": author,
            "publish_date": publish_date,
            "content_html": content_html,
            "original_url": url,
            "type": "image_detail"
        }
