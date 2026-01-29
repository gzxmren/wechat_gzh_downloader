import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os
import asyncio
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.app import WeChatDownloaderApp
from core.config import settings

class TestAppFlow(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        # 准备一个临时输出目录
        self.test_output = "tests/test_output"
        if os.path.exists(self.test_output):
            shutil.rmtree(self.test_output)
        os.makedirs(self.test_output)
        
        # 模拟 args
        self.mock_args = MagicMock()
        self.mock_args.output = self.test_output
        self.mock_args.user = "TestUser"
        self.mock_args.concurrency = 2
        self.mock_args.url = None
        self.mock_args.input = "tests/mock_urls.txt"
        self.mock_args.force = False
        self.mock_args.markdown = True
        self.mock_args.pdf = False
        self.mock_args.no_images = True
        self.mock_args.chat_log = None
        self.mock_args.db = False

        # 创建 Mock URL 文件
        with open(self.mock_args.input, "w") as f:
            f.write("http://example.com/article1\n")
            f.write("http://example.com/article2\n")

    def tearDown(self):
        # 清理
        if os.path.exists(self.test_output):
            shutil.rmtree(self.test_output)
        if os.path.exists("tests/mock_urls.txt"):
            os.remove("tests/mock_urls.txt")
        # 清理生成的 history/error logs
        if os.path.exists("history.log"): os.remove("history.log")
        if os.path.exists("error.log"): os.remove("error.log")

    @patch("core.app.fetch_article", new_callable=AsyncMock)
    @patch("core.app.html_to_markdown", new_callable=AsyncMock)
    @patch("core.app.save_full_html", new_callable=AsyncMock)
    @patch("core.app.save_metadata", new_callable=AsyncMock)
    @patch("core.app.save_markdown", new_callable=AsyncMock)
    async def test_run_success(self, mock_save_md, mock_save_meta, mock_save_html, mock_html2md, mock_fetch):
        """测试正常的下载流程"""
        
        # 1. 模拟 fetch_article 返回数据
        mock_fetch.return_value = {
            "title": "Test Article",
            "author": "Test Author",
            "publish_date": "2023-01-01",
            "content_html": "<div>Content</div>",
            "original_url": "http://example.com/article1"
        }
        
        # 2. 模拟 html_to_markdown 返回
        mock_html2md.return_value = ("# Markdown Content", "<div>Processed HTML</div>")
        
        # 3. 模拟 save 函数返回 True
        mock_save_html.return_value = True
        
        # 运行 App
        app = WeChatDownloaderApp(self.mock_args)
        await app.run()
        
        # 验证
        # 应该调用了2次 fetch (因为 mock_urls.txt 有2个链接)
        self.assertEqual(mock_fetch.call_count, 2)
        
        # 应该调用了 save_metadata, save_html
        self.assertTrue(mock_save_meta.called)
        self.assertTrue(mock_save_html.called)
        self.assertTrue(mock_save_md.called) # 因为 args.markdown = True

    @patch("core.app.fetch_article", new_callable=AsyncMock)
    async def test_history_skip(self, mock_fetch):
        """测试历史记录跳过功能"""
        # 设置 Mock 返回值，防止运行时报错
        mock_fetch.return_value = {
            "title": "Test Article 2",
            "author": "Test Author",
            "publish_date": "2023-01-02",
            "content_html": "<div>Content</div>",
            "original_url": "http://example.com/article2"
        }

        # 先写入一条历史记录
        with open("history.log", "w") as f:
            f.write("http://example.com/article1\n")
            
        app = WeChatDownloaderApp(self.mock_args)
        
        # 运行
        await app.run()
        
        # 因为 article1 在历史记录中，article2 不在
        # 所以 fetch 应该只被调用 1 次 (针对 article2)
        self.assertEqual(mock_fetch.call_count, 1)

if __name__ == '__main__':
    unittest.main()
