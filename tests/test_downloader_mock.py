import unittest
from unittest.mock import patch, AsyncMock
import asyncio
from core.downloader import download_html

class TestDownloaderMock(unittest.TestCase):
    
    def setUp(self):
        # 准备一个假的 Response 对象
        self.mock_response = AsyncMock()
        self.mock_response.status = 200
        # 默认返回一个简单的 HTML 字符串
        self.mock_response.text.return_value = "<html><body><h1>Hello World</h1></body></html>"
        self.mock_response.__aenter__.return_value = self.mock_response
        self.mock_response.__aexit__.return_value = None

    @patch('aiohttp.ClientSession.get')
    def test_download_success(self, mock_get):
        """测试正常的 200 OK 响应，应返回 HTML 字符串"""
        mock_get.return_value = self.mock_response
        
        # 运行异步测试
        html = asyncio.run(download_html("http://test.com/ok"))
        
        self.assertIsNotNone(html)
        self.assertIn("Hello World", html)
        # 验证是否真的调用了 get
        mock_get.assert_called_once()

    @patch('aiohttp.ClientSession.get')
    def test_download_404(self, mock_get):
        """测试 404 错误处理"""
        # 修改 Mock 状态码
        self.mock_response.status = 404
        mock_get.return_value = self.mock_response
        
        html = asyncio.run(download_html("http://test.com/404"))
        
        # 404 应该返回 None
        self.assertIsNone(html)

    @patch('aiohttp.ClientSession.get')
    def test_anti_bot_detection(self, mock_get):
        """测试微信风控页面检测"""
        self.mock_response.status = 200
        # 模拟返回风控页面
        self.mock_response.text.return_value = "<html><body>访问过于频繁，请稍后 verify.html </body></html>"
        mock_get.return_value = self.mock_response
        
        html = asyncio.run(download_html("http://test.com/block"))
        
        self.assertIsNone(html)

if __name__ == '__main__':
    unittest.main()