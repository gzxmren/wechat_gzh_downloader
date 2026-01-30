import aiohttp
import asyncio
import random
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from .config import settings
from .logger import logger

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

async def download_html(url, session=None):
    """
    异步执行网络请求，仅获取 HTML 源码。
    :param url: 微信文章 URL
    :param session: aiohttp.ClientSession 实例，若为 None 则创建一个临时的
    :return: html_content (str) or None
    """
    req_settings = settings.REQUEST_SETTINGS
    headers = settings.HEADERS

    # 随机延迟 (异步版本)
    delay = random.uniform(req_settings.get("sleep_min", 3), req_settings.get("sleep_max", 6))
    logger.debug(f"[Anti-Bot] Waiting {delay:.1f}s before fetching {url[:30]}...")
    await asyncio.sleep(delay)
    
    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True
        
    try:
        async with session.get(url, headers=headers, timeout=req_settings.get("timeout", 15)) as response:
            if response.status != 200:
                logger.error(f"HTTP {response.status} for {url}")
                return None
            
            # aiohttp 默认会根据 Content-Type 自动猜测编码，
            # 微信公众号通常是 utf-8
            html = await response.text(encoding='utf-8')
            
            # Anti-Bot Detection
            if "verify.html" in html or "weui-msg" in html:
                logger.error(f"访问被拒绝/需要验证。请检查是否需要更新 Cookie。URL: {url}")
                return None
                
            return html

    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None
    finally:
        if close_session:
            await session.close()
