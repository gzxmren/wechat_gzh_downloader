import asyncio
import sys
import os

# 将项目根目录添加到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.downloader import download_html

async def test():
    url = "https://mp.weixin.qq.com/s?__biz=MzI2NjMwODY4MQ==&mid=2247487672&idx=1&sn=69518e61820f8a5bd73d11ec7b8c3070"
    print(f"Testing async download for: {url}")
    html = await download_html(url)
    if html:
        print("Success! Downloaded HTML length:", len(html))
        print(f"Preview: {html[:100]}...")
    else:
        print("Failed to download HTML.")

if __name__ == "__main__":
    asyncio.run(test())