import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import io

# 确保可以导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wechat_db_tool import main

class TestWeChatDBTool(unittest.TestCase):
    
    def setUp(self):
        self.output_file = "tests/test_urls_output.txt"
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    def tearDown(self):
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        if os.path.exists("temp_decrypted.db"):
            os.remove("temp_decrypted.db")

    @patch("wechat_db_tool.parse_favorite_db")
    @patch("wechat_db_tool.save_urls_to_file")
    @patch("os.path.exists")
    def test_decrypted_db_flow(self, mock_exists, mock_save, mock_parse):
        """测试直接使用已解密数据库的流程"""
        # 1. 设置 Mock
        mock_exists.return_value = True
        mock_parse.return_value = [
            {"title": "Art1", "url": "http://link1"},
            {"title": "Art2", "url": "http://link2"}
        ]
        mock_save.return_value = True
        
        # 2. 模拟命令行参数
        test_args = [
            "wechat_db_tool.py",
            "--decrypted-db", "fake_decrypted.db",
            "-o", self.output_file
        ]
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=io.StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                
        # 3. 验证结果
        self.assertIn("提取到 2 条文章记录", output)
        self.assertIn("✅ 导出成功", output)
        mock_parse.assert_called_with("fake_decrypted.db")
        mock_save.assert_called_once()

    @patch("wechat_db_tool.decrypt_wechat_db")
    @patch("wechat_db_tool.parse_favorite_db")
    @patch("wechat_db_tool.save_urls_to_file")
    @patch("wechat_db_tool.check_command_exists")
    @patch("os.path.exists")
    def test_encrypted_db_flow(self, mock_exists, mock_cmd, mock_save, mock_parse, mock_decrypt):
        """测试加密数据库的完整解密提取流程"""
        # 1. 设置 Mock
        # 增加对 temp_decrypted.db 的存在性模拟，以便触发清理打印
        mock_exists.side_effect = lambda p: p in ["fake_encrypted.db", self.output_file, "temp_decrypted.db"]
        mock_cmd.return_value = True # 模拟 sqlcipher 已安装
        mock_decrypt.return_value = True # 模拟解密成功
        mock_parse.return_value = [{"title": "Art1", "url": "http://link1"}]
        mock_save.return_value = True
        
        # 2. 模拟命令行参数
        test_args = [
            "wechat_db_tool.py",
            "--db-path", "fake_encrypted.db",
            "--key", "a"*64,
            "-o", self.output_file
        ]
        
        # 模拟 temp_decrypted.db 存在以便清理逻辑运行
        with open("temp_decrypted.db", "w") as f: f.write("dummy")

        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=io.StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()

        # 3. 验证结果
        self.assertIn("正在尝试解密数据库", output)
        self.assertIn("数据库已解密至临时文件", output)
        mock_decrypt.assert_called_once()
        mock_parse.assert_called_with("temp_decrypted.db")
        # 验证临时文件清理 (由于 test 环境中文件可能没真的被删，我们主要看 output)
        self.assertIn("已清理临时解密文件", output)

    def test_missing_args(self):
        """测试参数缺失情况"""
        test_args = ["wechat_db_tool.py", "-o", self.output_file] # 缺少模式选择
        
        with patch.object(sys, 'argv', test_args):
            # argparse 在参数错误时会调用 sys.exit 并打印到 stderr
            with self.assertRaises(SystemExit):
                with patch('sys.stderr', new=io.StringIO()):
                    main()

if __name__ == "__main__":
    unittest.main()
