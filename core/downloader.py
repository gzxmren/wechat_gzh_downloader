import requests
import time
import random
import re
import datetime
import json
import os
from bs4 import BeautifulSoup

def load_config():
    """
    尝试加载项目根目录下的 config.json
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config.json")
    
    default_config = {
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        },
        "request_settings": {
            "timeout": 15,
            "sleep_min": 3,
            "sleep_max": 6
        }
    }

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                if "headers" in user_config:
                    default_config["headers"].update(user_config["headers"])
                if "request_settings" in user_config:
                    default_config["request_settings"].update(user_config["request_settings"])
        except Exception as e:
            print(f"[Warning] Failed to load config.json: {e}")

    return default_config

GLOBAL_CONFIG = load_config()

def parse_image_detail(html, url, title, author, publish_date):
    """
    备用解析策略：针对微信图片频道 (image_detail) 的解析。
    采用对象拆分与首次匹配逻辑，确保图片数量精确。
    """
    clean_html = re.sub(r'\s+', '', html)
    
    start_marker = 'picture_page_info_list=['
    start_idx = clean_html.find(start_marker)
    if start_idx == -1:
        start_marker = 'window.picture_page_info_list=['
        start_idx = clean_html.find(start_marker)
        
    if start_idx == -1:
        return None
        
    array_start = start_idx + len(start_marker) - 1
    bracket_count = 0
    array_end = -1
    for i in range(array_start, len(clean_html)):
        if clean_html[i] == '[': bracket_count += 1
        elif clean_html[i] == ']':
            bracket_count -= 1
            if bracket_count == 0:
                array_end = i + 1
                break
    
    if array_end == -1:
        target_str = clean_html[array_start:array_start+100000]
    else:
        target_str = clean_html[array_start:array_end]
    
    # 移除最外层的 [ ]
    if target_str.startswith('['): target_str = target_str[1:]
    if target_str.endswith(']'): target_str = target_str[:-1]

    # --- 核心改进：拆分对象块 ---
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

    image_list = []
    seen_urls = set()
    
    # 对每个对象块，仅提取第一个 cdn_url (即正文大图)
    for block in raw_blocks:
        # 使用之前验证过的 robust 正则
        url_match = re.search(r'cdn_url:(?:JsDecode\()?(?:\'|")(.*?)(?:\'|")', block)
        if url_match:
            img_url = url_match.group(1)
            # 强力去重
            clean_key = img_url.split('://')[-1]
            clean_key = re.sub(r'[\s\r\n\t]', '', clean_key)
            if clean_key not in seen_urls:
                seen_urls.add(clean_key)
                image_list.append(img_url)

    if not image_list:
        return None
            
    content_html = '<div class="rich_media_content" id="js_content" style="visibility: visible;">'
    for cur_url in image_list:
        if '\\x' in cur_url or '\\u' in cur_url:
            try: cur_url = cur_url.encode('utf-8').decode('unicode_escape')
            except: pass
        content_html += f'<p><img data-src="{cur_url}" src="{cur_url}" style="max-width: 100%; height: auto; display: block; margin: 0 auto;" /></p><br/>'
    content_html += '</div>'
    
    print(f"  -> [Fallback] 成功识别图片频道，提取了 {len(image_list)} 张正文图片")
    return {
        "title": title, "author": author, "publish_date": publish_date,
        "content_html": content_html, "original_url": url
    }

def fetch_article(url):
    settings = GLOBAL_CONFIG["request_settings"]
    headers = GLOBAL_CONFIG["headers"]
    time.sleep(random.uniform(settings.get("sleep_min", 3), settings.get("sleep_max", 6)))
    
    try:
        response = requests.get(url, headers=headers, timeout=settings.get("timeout", 15))
        response.encoding = 'utf-8'
        html = response.text
        
        if "verify.html" in html or "weui-msg" in html:
            print(f"[Error] 访问被拒绝/需要验证。请更新 config.json 中的 Cookie。")
            return None
            
        soup = BeautifulSoup(html, "lxml")
        
        title = "Untitled_Article"
        title_tag = soup.find("h1", class_="rich_media_title")
        if title_tag and title_tag.get_text(strip=True):
            title = title_tag.get_text(strip=True)
        elif soup.find("meta", property="og:title"):
            title = soup.find("meta", property="og:title")["content"]

        publish_date = None
        ct_match = re.search(r'(?:var\s+ct|window\.ct)\s*=\s*["\\]?(\d{10})["\\]?', html)
        if ct_match:
            publish_date = datetime.datetime.fromtimestamp(int(ct_match.group(1))).strftime("%Y-%m-%d")
        
        author_tag = soup.find("a", class_="rich_media_meta rich_media_meta_nickname")
        author = author_tag.get_text(strip=True) if author_tag else "Unknown_Account"
        
        content_div = soup.find("div", class_="rich_media_content") or soup.find(id="js_content") or soup.find(id="img-content")
            
        if not content_div:
            fallback = parse_image_detail(html, url, title, author, publish_date)
            if fallback: return fallback
            print(f"[Error] No content found for {url}")
            return None

        return {
            "title": title, "author": author, "publish_date": publish_date,
            "content_html": str(content_div), "original_url": url
        }
    except Exception as e:
        print(f"[Exception] Failed to fetch {url}: {e}")
        return None