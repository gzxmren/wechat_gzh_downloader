import requests
import time
import random
import re
import datetime
from bs4 import BeautifulSoup

def fetch_article(url):
    """
    根据 URL 获取微信文章的 HTML 内容。
    为了避免触发微信反爬虫机制，每次请求前会随机休眠 2-5 秒。
    """
    # 随机延迟，模拟人类阅读行为
    delay = random.uniform(3, 6)
    print(f"  [Anti-Bot] 等待 {delay:.1f} 秒...", end="", flush=True)
    time.sleep(delay)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8' # 强制 utf-8
        
        if response.status_code != 200:
            print(f"[Error] HTTP {response.status_code} for {url}")
            return None
            
        html = response.text
        soup = BeautifulSoup(html, "lxml")
        
        # 1. 提取标题
        title_tag = soup.find("h1", class_="rich_media_title")
        title = title_tag.get_text(strip=True) if title_tag else "Untitled_Article"
        
        # 2. 提取发布日期
        # 优先尝试从 JavaScript 变量中提取 ct (creation time, Unix timestamp)
        publish_date = None
        ct_match = re.search(r'(?:var\s+ct|window\.ct)\s*=\s*["\\]?(\d{10})["\\]?', html)
        if ct_match:
            timestamp = int(ct_match.group(1))
            dt_object = datetime.datetime.fromtimestamp(timestamp)
            publish_date = dt_object.strftime("%Y-%m-%d")
        
        # 备选：尝试匹配 publish_time 字符串
        if not publish_date:
            pt_match = re.search(r'publish_time\s*=\s*["\\]?(\d{4}-\d{2}-\d{2})["\\]?', html)
            if pt_match:
                publish_date = pt_match.group(1)
        
        # 3. 提取作者/公众号名称
        account_tag = soup.find("a", class_="rich_media_meta rich_media_meta_nickname")
        author = account_tag.get_text(strip=True) if account_tag else "Unknown_Account"
        
        # 4. 提取正文容器
        content_div = soup.find("div", class_="rich_media_content")
        if not content_div: content_div = soup.find(id="js_content")
        if not content_div: content_div = soup.find(id="img-content")
            
        if not content_div:
            print(f"[Error] No content found for {url}")
            return None

        return {
            "title": title,
            "author": author,
            "publish_date": publish_date,
            "content_html": str(content_div),
            "original_url": url
        }

    except Exception as e:
        print(f"[Exception] Failed to fetch {url}: {e}")
        return None
