import unittest
import sys
import os
from datetime import datetime

# 添加项目根目录到 path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.parsers import find_and_parse, register_parser
from core.parsers.base import BaseParser
from core.parsers.standard import StandardParser
from core.parsers.image_detail import ImageDetailParser

class TestParsers(unittest.TestCase):
    
    def setUp(self):
        # 模拟标准文章 HTML
        self.std_html = """
        <html>
            <div id="js_content">
                <p>This is a standard article.</p>
            </div>
            <script>var ct = "1678888888";</script>
            <h1 class="rich_media_title">Test Title</h1>
            <a class="rich_media_meta rich_media_meta_nickname">Test Author</a>
        </html>
        """
        
        # 模拟图片频道 HTML
        self.img_html = """
        <html>
            <script>
                var picture_page_info_list = [
                    {cdn_url: "http://example.com/img1.jpg"},
                    {cdn_url: "http://example.com/img2.jpg"}
                ];
            </script>
            <meta name="description" content="Image Description">
        </html>
        """

    def test_registry_selection_standard(self):
        """测试注册表正确调用 StandardParser"""
        data = find_and_parse(self.std_html, "http://url")
        self.assertIsNotNone(data)
        self.assertEqual(data.get("title"), "Test Title")
        self.assertEqual(data.get("type"), "standard")

    def test_registry_selection_image(self):
        """测试注册表正确调用 ImageDetailParser"""
        data = find_and_parse(self.img_html, "http://url")
        self.assertIsNotNone(data)
        self.assertEqual(data.get("type"), "image_detail")
        self.assertIn("http://example.com/img1.jpg", data.get("content_html"))

    def test_standard_parser_extraction(self):
        """测试标准解析器的元数据提取"""
        parser = StandardParser()
        data = parser.parse(self.std_html, "http://url")
        
        self.assertEqual(data["title"], "Test Title")
        self.assertEqual(data["author"], "Test Author")
        self.assertEqual(data["publish_date"], "2023-03-15") # 1678888888 timestamp
        self.assertIn("This is a standard article", data["content_html"])

    def test_image_parser_extraction(self):
        """测试图片解析器的内容提取"""
        parser = ImageDetailParser()
        data = parser.parse(self.img_html, "http://url")
        
        self.assertEqual(data["type"], "image_detail")
        self.assertIn("http://example.com/img1.jpg", data["content_html"])
        self.assertIn("Image Description", data["content_html"])

if __name__ == '__main__':
    unittest.main()
