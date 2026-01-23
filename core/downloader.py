import requests
import time
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

def fetch_article(url):
    """
    执行网络请求并调用解析器。
    """
    settings = GLOBAL_CONFIG["request_settings"]
    headers = GLOBAL_CONFIG["headers"]

    # 随机延迟
    delay = random.uniform(settings.get("sleep_min", 3), settings.get("sleep_max", 6))
    print(f"  [Anti-Bot] 等待 {delay:.1f} 秒...", end="", flush=True)
    time.sleep(delay)
    
    try:
        response = requests.get(url, headers=headers, timeout=settings.get("timeout", 15))
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"[Error] HTTP {response.status_code} for {url}")
            return None
            
        html = response.text
        
        # Anti-Bot Detection
        if "verify.html" in html or "weui-msg" in html:
            print(f"[Error] 访问被拒绝/需要验证。请更新 config.json 中的 Cookie。")
            return None
            
        # --- 核心变更：调用解析器模块 ---
        article_data = parse_html(html, url)
        
        if not article_data:
            print(f"[Error] No content found for {url} (All parsers failed)")
            return None
            
        return article_data

    except Exception as e:
        print(f"[Exception] Failed to fetch {url}: {e}")
        return None
