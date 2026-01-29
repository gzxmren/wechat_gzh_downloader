import os
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
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE = os.getenv("LOG_FILE", "app.log")

    @classmethod
    def get_template_path(cls, template_name):
        return cls.TEMPLATE_DIR / template_name

# Singleton instance (optional usage style)
settings = Config()
