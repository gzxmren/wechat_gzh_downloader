import aiohttp
import asyncio
import random
import json
import os
from .parsers import parse_html

def load_config():
    """
    加载项目根目录下的 config.json
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
                
            # --- 调用解析器模块 (保持同步) ---
            # 解析器处理内存中的字符串，不涉及 I/O，保持同步以维持稳定性和简单性
            article_data = parse_html(html, url)
            
            if not article_data:
                print(f"[Error] No content found for {url} (All parsers failed)")
                return None
                
            return article_data

    except Exception as e:
        print(f"[Exception] Failed to fetch {url}: {e}")
        return None
    finally:
        if close_session:
            await session.close()