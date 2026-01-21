import os
import requests
import hashlib
from urllib.parse import urlparse

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

def download_image(url, save_dir):
    """
    下载图片并保存到指定目录。
    使用 URL 的 MD5 哈希作为文件名，避免重复下载。
    
    Args:
        url (str): 图片 URL
        save_dir (str): 保存目录 (assets 文件夹路径)
        
    Returns:
        str: 相对文件名 (例如 'image_abc123.jpg')，如果下载失败返回 None
    """
    if not url:
        return None
        
    try:
        # 生成哈希文件名
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        
        # 简单防盗链 Header
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://mp.weixin.qq.com/"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
            
        # 确定扩展名
        ext = get_image_extension(url, response.headers.get('Content-Type', ''))
        filename = f"{url_hash}{ext}"
        save_path = os.path.join(save_dir, filename)
        
        # 如果文件已存在，直接返回（去重）
        if os.path.exists(save_path):
            return filename
            
        with open(save_path, "wb") as f:
            f.write(response.content)
            
        return filename
        
    except Exception as e:
        print(f"[Warning] Image download failed: {url} -> {e}")
        return None
