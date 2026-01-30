import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    """
    Centralized Configuration Manager.
    Loads from Environment variables > Config file (TODO) > Defaults.
    """
    
    # Project Paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    OUTPUT_DIR = BASE_DIR / "output"
    TEMPLATE_DIR = BASE_DIR / "templates"
    INPUT_DIR = BASE_DIR / "input"
    
    # App Settings
    APP_NAME = "WeChat Fav Downloader"
    VERSION = "4.6.0"
    
    # Index / Pagination
    PAGE_SIZE = int(os.getenv("PAGE_SIZE", 20))
    
    # Concurrency & Network
    CONCURRENCY = int(os.getenv("CONCURRENCY", 3))
    TIMEOUT = int(os.getenv("TIMEOUT", 30))
    USER_AGENT_PREFIX = os.getenv("USER_AGENT_PREFIX", "MyWeChatUser")
    
    import json
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE = os.getenv("LOG_FILE", "app.log")

    def __init__(self):
        self.HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://mp.weixin.qq.com/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        self.REQUEST_SETTINGS = {
            "timeout": int(self.TIMEOUT),
            "sleep_min": 3,
            "sleep_max": 6
        }
        self._load_user_config()

    def _load_user_config(self):
        """Load config.json and merge into settings."""
        config_path = self.BASE_DIR / "config.json"
        if not config_path.exists():
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            
            # 1. Merge Headers
            if "headers" in user_config:
                self.HEADERS.update(user_config["headers"])
            
            # 2. Merge Request Settings
            if "request_settings" in user_config:
                self.REQUEST_SETTINGS.update(user_config["request_settings"])

            # 3. Handle Cookie File
            if "cookie_file" in user_config and user_config["cookie_file"]:
                self._load_cookie_file(user_config["cookie_file"])

        except Exception as e:
            # Since logger depends on config, we use stderr here or just ignore
            print(f"[Config] Warning: Failed to load config.json: {e}")

    def _load_cookie_file(self, cookie_file_path):
        """Parse Netscape format cookie file."""
        # Resolve path
        file_path = Path(cookie_file_path)
        if not file_path.is_absolute():
            file_path = self.BASE_DIR / cookie_file_path
        
        if not file_path.exists():
            print(f"[Config] Warning: Cookie file not found: {file_path}")
            return

        try:
            cookie_parts = []
            with open(file_path, 'r', encoding='utf-8') as cf:
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
                # Deduplicate
                cookie_dict = {}
                for cp in cookie_parts:
                    if '=' in cp:
                        name, val = cp.split('=', 1)
                        cookie_dict[name] = val
                
                final_cookies = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
                self.HEADERS["Cookie"] = final_cookies
                print(f"[Config] Loaded {len(cookie_dict)} cookies from: {file_path.name}")

        except Exception as e:
            print(f"[Config] Warning: Failed to parse cookie file: {e}")

    @classmethod
    def get_template_path(cls, template_name):
        return cls.TEMPLATE_DIR / template_name

# Singleton instance (optional usage style)
settings = Config()
