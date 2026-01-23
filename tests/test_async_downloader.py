import asyncio
import sys
import os

# 将项目根目录添加到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.downloader import fetch_article

async def test():
    url = "https://mp.weixin.qq.com/s?__biz=MzI2NjMwODY4MQ==&mid=2247487672&idx=1&sn=69518e61820f8a5bd73d11ec7b8c3070"
    print(f"Testing async fetch for: {url}")
    result = await fetch_article(url)
    if result:
        print("Success!")
        print(f"Title: {result.get('title')}")
        print(f"Author: {result.get('author')}")
        print(f"Publish Time: {result.get('publish_time')}")
        print(f"Content preview: {result.get('content_html')[:100]}...")
    else:
        print("Failed to fetch article.")

if __name__ == "__main__":
    asyncio.run(test())
