import os
import argparse
import asyncio
from core.app import WeChatDownloaderApp
from core.logger import logger

def parse_args():
    """解析命令行参数"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_input = os.path.join(base_dir, "input/urls.txt")
    default_output = os.path.join(base_dir, "output")

    parser = argparse.ArgumentParser(
        description="微信公众号文章批量下载工具 (WeChat Fav Downloader) v4.6",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # 基础参数
    parser.add_argument("url", nargs="?", help="直接指定单个 URL (可选)")
    parser.add_argument("-i", "--input", default=default_input, help="输入 URL 文件路径")
    parser.add_argument("-o", "--output", default=default_output, help="输出目录路径")
    parser.add_argument("-u", "--user", default="MyWeChatUser", help="微信用户名前缀")
    
    # 并发控制
    parser.add_argument("--concurrency", type=int, default=None, help="全局并发处理文章数 (默认: 3)")
    
    # 模式选择
    parser.add_argument("--chat-log", help="指定导出的聊天记录文件 (txt格式)")
    parser.add_argument("--db", action="store_true", help="启用数据库读取模式")
    
    # 功能开关
    parser.add_argument("--markdown", action="store_true", help="启用 Markdown 生成 (默认关闭)")
    parser.add_argument("--pdf", action="store_true", help="启用 PDF 生成 (默认关闭)")
    parser.add_argument("--no-images", action="store_true", help="禁用图片下载")
    parser.add_argument("--retry", type=int, default=1, help="单次运行的失败重试次数")
    parser.add_argument("--force", action="store_true", help="强制处理所有 URL (忽略历史记录)")
    
    # 数据库模式参数
    db_group = parser.add_argument_group('数据库模式选项')
    db_group.add_argument("--key", help="微信数据库密钥")
    db_group.add_argument("--db-path", help="加密的 Favorite.db 路径")
    db_group.add_argument("--decrypted-db", help="直接指定已解密的数据库路径")
    
    return parser.parse_args()

async def main():
    args = parse_args()
    app = WeChatDownloaderApp(args)
    await app.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n[User Interrupt] 程序已停止。")
