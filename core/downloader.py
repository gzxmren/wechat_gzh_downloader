import aiohttp
import asyncio
import random
import json
import os
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from .parsers import find_and_parse

def clean_url(url):
    """
    清理微信 URL 中可能触发风控或无用的参数。
    保留核心参数：__biz, mid, idx, sn
    尝试移除：scene, chksm, poc_token, etc.
    """
    try:
        parsed = urlparse(url)
        # 如果是短链接 /s/xxxx，直接返回
        if "/s/" in parsed.path:
            return url
            
        query = parse_qs(parsed.query)
        
        # 核心参数列表
        core_params = ['__biz', 'mid', 'idx', 'sn']
        new_query = {}
        
        for k in core_params:
            if k in query:
                new_query[k] = query[k]
                
        # 重组 URL
        if new_query:
            new_parts = list(parsed)
            new_parts[4] = urlencode(new_query, doseq=True)
            return urlunparse(new_parts)
        return url
    except Exception:
        return url

def load_config():
    """
    加载项目根目录下的 config.json
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config.json")
    
    default_config = {
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://mp.weixin.qq.com/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
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
                
                # 1. Load standard headers and settings
                if "headers" in user_config:
                    default_config["headers"].update(user_config["headers"])
                if "request_settings" in user_config:
                    default_config["request_settings"].update(user_config["request_settings"])

                # 2. Handle Netscape cookie file (Overwrites 'Cookie' in headers if valid)
                if "cookie_file" in user_config and user_config["cookie_file"]:
                    cookie_file = user_config["cookie_file"]
                    # Resolve relative path
                    if not os.path.isabs(cookie_file):
                        cookie_file = os.path.join(base_dir, cookie_file)
                    
                    if os.path.exists(cookie_file):
                        try:
                            cookie_parts = []
                            with open(cookie_file, 'r', encoding='utf-8') as cf:
                                for line in cf:
                                    if line.strip().startswith('#') or not line.strip():
                                        continue
                                    fields = line.strip().split('\t')
                                    if len(fields) >= 7:
                                        domain = fields[0]
                                        # Filter for wechat related domains
                                        if "weixin.qq.com" in domain or "qq.com" in domain:
                                            cookie_parts.append(f"{fields[5]}={fields[6].strip()}")
                            
                            if cookie_parts:
                                # Use a dict to deduplicate by cookie name (last one wins)
                                cookie_dict = {}
                                for cp in cookie_parts:
                                    if '=' in cp:
                                        name, val = cp.split('=', 1)
                                        cookie_dict[name] = val
                                
                                final_cookies = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
                                default_config["headers"]["Cookie"] = final_cookies
                                print(f"[Config] Loaded {len(cookie_dict)} cookies from file: {user_config['cookie_file']}")
                                # print(f"[Debug] Final Cookie String: {final_cookies[:100]}...") 
                        except Exception as e:
                            print(f"[Warning] Failed to parse cookie file: {e}")
                    else:
                        print(f"[Warning] Cookie file not found: {cookie_file}")

        except Exception as e:
            print(f"[Warning] Failed to load config.json: {e}")

    return default_config

# 全局配置
GLOBAL_CONFIG = load_config()

async def fetch_article(url, session=None):
    """
    异步执行网络请求并调用解析器。
    :param url: 微信文章 URL
    :param session: aiohttp.ClientSession 实例，若为 None 则创建一个临时的
    """
    settings = GLOBAL_CONFIG["request_settings"]
    headers = GLOBAL_CONFIG["headers"]

    # 随机延迟 (异步版本)
    delay = random.uniform(settings.get("sleep_min", 3), settings.get("sleep_max", 6))
    print(f"  [Anti-Bot] 等待 {delay:.1f} 秒...", flush=True)
    await asyncio.sleep(delay)
    
    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True
        
    # print(f"[Debug] Request Headers: {headers}")
    try:
        async with session.get(url, headers=headers, timeout=settings.get("timeout", 15)) as response:
            if response.status != 200:
                print(f"[Error] HTTP {response.status} for {url}")
                return None
            
            # aiohttp 默认会根据 Content-Type 自动猜测编码，
            # 微信公众号通常是 utf-8
            html = await response.text(encoding='utf-8')
            
            # Anti-Bot Detection
            if "verify.html" in html or "weui-msg" in html:
                print(f"[Error] 访问被拒绝/需要验证。请更新 config.json 中的 Cookie。")
                return None
                
            # --- 调用解析器模块 (支持多解析器回退) ---
            article_data = find_and_parse(html, url)
            
            if not article_data:
                print(f"[Error] No content found for {url} (All parsers failed)")
                # Debug: 保存失败的 HTML 以便分析
                with open("debug_failed_html.txt", "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"[Debug] Saved raw HTML to debug_failed_html.txt")
                return None
                
            return article_data

    except Exception as e:
        print(f"[Exception] Failed to fetch {url}: {e}")
        return None
    finally:
        if close_session:
            await session.close()