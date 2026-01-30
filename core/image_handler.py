import os
import aiohttp
import aiofiles
import hashlib
from urllib.parse import urlparse
from .logger import logger

def get_image_extension(url, content_type):
    """根据 URL 或 Content-Type 猜测图片扩展名"""
    path = urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
        return ext
    
    # 如果 URL 没有扩展名，尝试从 Content-Type 获取
    if 'jpeg' in content_type: return '.jpg'
    if 'png' in content_type: return '.png'
    if 'gif' in content_type: return '.gif'
    if 'webp' in content_type: return '.webp'
    
    return '.jpg' # 默认

async def download_image(url, save_dir, session=None):
    """
    异步下载图片并保存到指定目录。
    使用 URL 的 MD5 哈希作为文件名，避免重复下载。
    
    Args:
        url (str): 图片 URL
        save_dir (str): 保存目录 (assets 文件夹路径)
        session (aiohttp.ClientSession): 可选的 aiohttp 会话
        
    Returns:
        str: 相对文件名 (例如 'abc123.jpg')，如果下载失败返回 None
    """
    if not url:
        return None
        
    try:
        # 生成哈希文件名
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        
        # 确定扩展名 (初步根据 URL)
        path = urlparse(url).path
        ext = os.path.splitext(path)[1].lower()
        if not ext:
            ext = ".jpg" # 占位，稍后根据 response 修正
            
        filename = f"{url_hash}{ext}"
        save_path = os.path.join(save_dir, filename)
        
        # 如果文件已存在，直接返回（去重）
        if os.path.exists(save_path):
            return filename
            
        # 简单防盗链 Header
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://mp.weixin.qq.com/"
        }
        
        close_session = False
        if session is None:
            session = aiohttp.ClientSession()
            close_session = True
            
        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    return None
                
                content = await response.read()
                
                # 根据真实 Content-Type 修正扩展名
                real_ext = get_image_extension(url, response.headers.get('Content-Type', ''))
                if real_ext != ext:
                    filename = f"{url_hash}{real_ext}"
                    save_path = os.path.join(save_dir, filename)
                    if os.path.exists(save_path):
                        return filename
                
                # 异步写入文件
                async with aiofiles.open(save_path, mode='wb') as f:
                    await f.write(content)
                    
                return filename
        finally:
            if close_session:
                await session.close()
        
    except Exception as e:
        logger.warning(f"Image download failed: {url} -> {e}")
        return None
