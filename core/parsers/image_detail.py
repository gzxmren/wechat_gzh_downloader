import re
from .base import BaseParser
from .registry import register_parser

@register_parser
class ImageDetailParser(BaseParser):
    """
    针对微信“图片频道” (image_detail) 的解析器。
    支持新版 (2026) 的图片/文本混合布局。
    """
    
    def can_handle(self, html, url) -> bool:
        return 'picture_page_info_list' in html or 'album_info_list' in html

    def parse(self, html, url, soup=None):
        # 1. 提取通用元数据
        title, author, publish_date = self.extract_common_metadata(html, soup=soup)

        # 2. 全局预处理：移除所有空白字符
        clean_html = re.sub(r'\s+', '', html)
        
        # --- 3. 提取长正文 (content_noencode) ---
        long_content = ""
        # 匹配 JsDecode('...') 里的内容
        content_match = re.search(r'content_noencode:JsDecode\((?:\'|\")(.*?)(?:\'|\")\)', clean_html)
        if content_match:
            raw_long_content = content_match.group(1)
            long_content = self.decode_wechat_text(raw_long_content)
            # 处理 \x0a 换行并转为 <br/>
            long_content = long_content.replace('\\x0a', '\n').replace('\n', '<br/>')

        # --- 4. 特征检测与定位图片列表 ---
        start_marker = None
        for marker in ['picture_page_info_list=[', 'picture_page_info_list:[', 'window.picture_page_info_list=[']:
            if marker in clean_html:
                start_marker = marker
                break

        image_list = []
        if start_marker:
            start_idx = clean_html.find(start_marker)
            # 5. 精确截取：括号平衡算法
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
            
            target_str = clean_html[array_start:array_end] if array_end != -1 else clean_html[array_start:array_start+100000]
            
            # 移除最外层的 [ ]
            if target_str.startswith('['): target_str = target_str[1:]
            if target_str.endswith(']'): target_str = target_str[:-1]

            # 6. 拆分对象块
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

            # 极简正则 Fallback
            if not raw_blocks:
                raw_blocks = re.findall(r'\{[^{}]*cdn_url:[^{}]*\}', target_str)

            # 7. 提取 URL
            seen_urls = set()
            for block in raw_blocks:
                block_urls = re.findall(r'cdn_url:(?:JsDecode\()?(?:\'|\")(.*?)(?:\'|\")\)?', block)
                img_url = None
                for u in block_urls:
                    if u and u.strip():
                        img_url = u
                        break
                
                if img_url:
                    # 清理残留标记
                    img_url = img_url.replace("JsDecode('", "").replace("')", "").replace('JsDecode("', "").replace('")', "")
                    clean_key = img_url.split('://')[-1]
                    clean_key = re.sub(r'[\s\r\n\t]', '', clean_key)
                    if clean_key not in seen_urls:
                        seen_urls.add(clean_key)
                        image_list.append(img_url)

        # 8. 如果既没抓到图片也没抓到长文本，才认为失败
        if not image_list and not long_content:
            return None
            
        # 9. 提取摘要/导语 (Description)
        desc_text = ""
        meta_desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html, re.IGNORECASE)
        if meta_desc_match:
            desc_text = self.decode_wechat_text(meta_desc_match.group(1)).replace('\n', '<br/>')
            
        # 10. 尝试提取常规 HTML 正文 (混合模式)
        if soup is None:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
        text_content_html = ""
        content_div = soup.find(id="js_content")
        if content_div:
            # 确保内容可见
            if content_div.has_attr("style"):
                content_div["style"] = content_div["style"].replace("visibility: hidden", "visibility: visible").replace("opacity: 0", "opacity: 1")
            text_content_html = str(content_div)

        # 11. 构建 HTML
        content_html = '<div class="rich_media_content" id="js_content_wrapper" style="visibility: visible;">'
        
        # 优先显示长正文
        if long_content:
             content_html += f'<div class="image_channel_text" style="margin-bottom: 20px; font-size: 16px; line-height: 1.6; color: #333; background: #f9f9f9; padding: 15px; border-radius: 8px;">{long_content}</div><hr/>'

        has_body_text = bool(content_div.get_text(strip=True)) if content_div else False

        if desc_text and not has_body_text: 
            content_html += f'<div class="image_channel_desc" style="margin-bottom: 20px; font-size: 16px; line-height: 1.6; color: #333;">{desc_text}</div>'
            
        if text_content_html:
            content_html += text_content_html
            content_html += "<br/><hr/><br/>"

        for cur_url in image_list:
            if '\\x' in cur_url or '\\u' in cur_url:
                try: cur_url = cur_url.encode('utf-8').decode('unicode_escape')
                except: pass
            content_html += f'<p><img data-src="{cur_url}" src="{cur_url}" style="max-width: 100%; height: auto; display: block; margin: 0 auto;" /></p><br/>'
        content_html += '</div>'
        
        return {
            "title": title, "author": author, "publish_date": publish_date,
            "content_html": content_html, "original_url": url, "type": "image_text_mix"
        }
