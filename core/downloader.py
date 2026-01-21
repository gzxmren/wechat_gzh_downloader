import requests
import time
import random
from bs4 import BeautifulSoup

def fetch_article(url):
    """
    根据 URL 获取微信文章的 HTML 内容。
    为了避免触发微信反爬虫机制，每次请求前会随机休眠 2-5 秒。
    """
    # 随机延迟，模拟人类阅读行为
    delay = random.uniform(2, 5)
    print(f"  [Anti-Bot] 等待 {delay:.1f} 秒...", end="", flush=True)
    time.sleep(delay)
    print(" 开始下载")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8' # 强制 utf-8，虽然 requests 通常会自动识别
        
        if response.status_code != 200:
            print(f"[Error] HTTP {response.status_code} for {url}")
            return None
            
        soup = BeautifulSoup(response.text, "lxml")
        
        # 1. 提取标题
        title_tag = soup.find("h1", class_="rich_media_title")
        title = title_tag.get_text(strip=True) if title_tag else "Untitled_Article"
        
        # 2. 提取发布日期 (微信通常在 JS 中渲染日期，HTML 中可能需要从元数据提取)
        # 这里尝试从 script 标签或 meta 提取，简化版先取当前日期或页面上的publish_time
        # 为了稳健，我们暂时在文件名中使用 'UnknownDate' 或由调用者传入日期
        # 实际抓取中，publish_time 通常隐藏在 JS 变量 `ct` 中
        
        # 3. 提取作者/公众号名称
        account_tag = soup.find("a", class_="rich_media_meta rich_media_meta_nickname")
        author = account_tag.get_text(strip=True) if account_tag else "Unknown_Account"
        
        # 4. 提取正文容器
        # 策略 A: 优先查找标准的正文 div
        content_div = soup.find("div", class_="rich_media_content")
        
        # 策略 B: 查找 id="js_content" (不限标签)
        if not content_div:
            content_div = soup.find(id="js_content")
            
        # 策略 C: 查找更外层的 id="img-content"
        if not content_div:
            content_div = soup.find(id="img-content")
            
        if not content_div:
            # 最后的尝试：打印页面的部分结构以供调试
            print(f"[Error] No content found for {url}")
            # print(soup.prettify()[:1000]) # 调试用
            return None

        return {
            "title": title,
            "author": author,
            "content_html": str(content_div),
            "original_url": url
        }

    except Exception as e:
        print(f"[Exception] Failed to fetch {url}: {e}")
        return None
