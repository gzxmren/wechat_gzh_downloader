import unittest
import os
from datetime import datetime
from core.parsers import find_and_parse
from core.parsers.standard import StandardParser
from core.parsers.image_detail import ImageDetailParser

class TestParsers(unittest.TestCase):
    def setUp(self):
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')

    def load_fixture(self, filename):
        with open(os.path.join(self.fixtures_dir, filename), 'r', encoding='utf-8') as f:
            return f.read()

    def test_real_world_hybrid_tags(self):
        """测试真实的混合模式文章（包含 hex 转义标签）"""
        html = self.load_fixture('real_hybrid_tags.html')
        url = "https://mp.weixin.qq.com/s/tZbgK_jBVSeLTBSx0sy-MQ"
        
        result = find_and_parse(html, url)
        self.assertIsNotNone(result)
        
        # 1. 验证标题是否正确解码
        self.assertIn("NanoBanana的这50个顶级提示词", result['title'])
        
        # 2. 验证混合模式：既有文字又有图片
        # 该文章正文包含 "NanoBanana" 字样
        self.assertIn("NanoBanana", result['content_html'])
        # 该文章图片列表包含图片
        self.assertIn("<img", result['content_html'])
        
        # 3. 验证标签是否正确解码（无乱码）
        self.assertIn("#提升AI创作效率", result['content_html'])
        self.assertIn("wx_topic_link", result['content_html']) # 应该是链接形式

    def test_image_detail_hex_decoding(self):
        """测试图片频道中 hex 转义字符的解码，且不破坏中文"""
        # 模拟原始文件中的字面量 \x26 和中文混合
        html = '<html><meta name="description" content="\\x26lt;a\\x26gt;#提升AI创作效率\\x26lt;/a\\x26gt;" /><script>var picture_page_info_list = [{cdn_url: "http://img.com/1.jpg"}];</script></html>'
        
        result = find_and_parse(html, "http://test.com")
        self.assertIsNotNone(result)
        # 验证是否成功解码为 <a>#提升AI创作效率</a> 且中文无乱码
        self.assertIn("<a>#提升AI创作效率</a>", result['content_html'])

    def test_image_detail_parser(self):
        """测试图片频道(漫画/长图)的解析"""
        html = self.load_fixture('image_detail.html')
        url = "http://fake.url/comic"
        
        # 1. 验证识别能力
        parser = ImageDetailParser()
        self.assertTrue(parser.can_handle(html, url))
        
        # 2. 验证解析结果
        result = find_and_parse(html, url)
        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'image_detail')
        self.assertEqual(result['title'], "漫画：程序员的一天")
        
        # 3. 验证图片提取
        # 我们的 fixture 里有 3 张图
        self.assertEqual(result['content_html'].count('<img'), 3)
        self.assertIn('https://example.com/comic_1.jpg', result['content_html'])
        
        # 4. 验证导语提取
        self.assertIn("这是一个关于程序员日常生活的漫画", result['content_html'])

    def test_standard_parser_happy_path(self):
        """测试标准文章的完美解析"""
        html = self.load_fixture('standard.html')
        url = "http://fake.url/standard"
        
        # 1. 确保 StandardParser 能处理
        parser = StandardParser()
        self.assertTrue(parser.can_handle(html, url))
        
        # 2. 这里的 find_and_parse 应该自动找到 StandardParser
        result = find_and_parse(html, url)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], "测试标题：2026年微信架构演进")
        self.assertEqual(result['author'], "技术大牛")
        self.assertEqual(result['publish_date'], "2026-01-30")
        self.assertIn("这是正文的第一段", result['content_html'])

    def test_edge_case_parser(self):
        """测试元数据缺失时的回退机制"""
        html = self.load_fixture('edge_case.html')
        url = "http://fake.url/edge"
        
        result = find_and_parse(html, url)
        
        self.assertIsNotNone(result)
        # 标题应该从 meta og:title 获取
        self.assertEqual(result['title'], "这是一个从Meta标签获取的标题")
        # 作者缺失应有默认值
        self.assertEqual(result['author'], "Unknown_Account")
        # 日期应从 window.ct 获取 (2025-01-01)
        self.assertEqual(result['publish_date'], "2025-01-01")

if __name__ == '__main__':
    unittest.main()