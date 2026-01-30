import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.app import WeChatDownloaderApp

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
        # 清理生成的 history/csv logs
        for f in ["history.log", "error.log", "history.log.bak"]:
            if os.path.exists(f): os.remove(f)
        
        csv_in_output = os.path.join(self.test_output, "wechat_records.csv")
        if os.path.exists(csv_in_output): os.remove(csv_in_output)

    @patch("core.app.download_html", new_callable=AsyncMock)
    @patch("core.app.find_and_parse")
    @patch("core.app.html_to_markdown", new_callable=AsyncMock)
    @patch("core.app.save_full_html", new_callable=AsyncMock)
    @patch("core.app.save_metadata", new_callable=AsyncMock)
    @patch("core.app.save_markdown", new_callable=AsyncMock)
    async def test_run_success(self, mock_save_md, mock_save_meta, mock_save_html, mock_html2md, mock_parse, mock_download):
        """测试正常的下载流程"""
        
        # 1. 模拟 download_html 返回
        mock_download.return_value = "<html>Mock Content</html>"
        
        # 2. 模拟 find_and_parse 返回
        mock_parse.return_value = {
            "title": "Test Article",
            "author": "Test Author",
            "publish_date": "2023-01-01",
            "content_html": "<div>Content</div>",
            "original_url": "http://example.com/article1"
        }
        
        # 3. 模拟 html_to_markdown 返回
        mock_html2md.return_value = ("# Markdown Content", "<div>Processed HTML</div>")
        
        # 4. 模拟 save 函数返回 True
        mock_save_html.return_value = True
        
        # 运行 App
        app = WeChatDownloaderApp(self.mock_args)
        await app.run()
        
        # 验证
        self.assertEqual(mock_download.call_count, 2)
        self.assertEqual(mock_parse.call_count, 2)
        self.assertTrue(mock_save_meta.called)
        
        # 验证 CSV 是否在指定的 output 目录下生成
        csv_path = os.path.join(self.test_output, "wechat_records.csv")
        self.assertTrue(os.path.exists(csv_path), f"CSV should exist at {csv_path}")

    @patch("core.app.download_html", new_callable=AsyncMock)
    @patch("core.app.find_and_parse")
    async def test_history_skip(self, mock_parse, mock_download):
        """测试历史记录跳过功能 (通过旧 history.log 迁移)"""
        # 设置 Mock 返回值
        mock_download.return_value = "<html>Mock Content</html>"
        mock_parse.return_value = {
            "title": "Test Article 2",
            "author": "Test Author",
            "publish_date": "2023-01-02",
            "content_html": "<div>Content</div>",
            "original_url": "http://example.com/article2"
        }

        # 先写入一条旧版历史记录
        with open("history.log", "w") as f:
            f.write("http://example.com/article1\n")
            
        # 初始化 App
        app = WeChatDownloaderApp(self.mock_args)
        
        # 运行
        await app.run()
        
        # 因为 article1 被跳过
        self.assertEqual(mock_download.call_count, 1)
        self.assertTrue(os.path.exists("history.log.bak"))

if __name__ == '__main__':
    unittest.main()