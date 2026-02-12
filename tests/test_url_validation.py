import unittest
from core.downloader import validate_wx_url

class TestUrlValidation(unittest.TestCase):
    def test_valid_urls(self):
        valid_urls = [
            "http://mp.weixin.qq.com/s/abcdefg",
            "https://mp.weixin.qq.com/s/123456",
            "https://mp.weixin.qq.com/s?__biz=MzI...",
        ]
        for url in valid_urls:
            self.assertTrue(validate_wx_url(url), f"Should be valid: {url}")

    def test_invalid_urls(self):
        invalid_urls = [
            "hhttps://mp.weixin.qq.com/s/typo",
            "htpp://mp.weixin.qq.com/s/typo",
            "ftp://mp.weixin.qq.com/s/scheme",
            "https://www.google.com/search?q=weixin", # Wrong domain
            "mp.weixin.qq.com/s/no_scheme",
            "Just some text",
            "",
            None
        ]
        for url in invalid_urls:
            self.assertFalse(validate_wx_url(url), f"Should be invalid: {url}")

if __name__ == '__main__':
    unittest.main()
