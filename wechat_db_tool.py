#!/usr/bin/env python3
import os
import argparse
import sys
from core.db_decrypter import decrypt_wechat_db
from core.db_parser import parse_favorite_db, save_urls_to_file
from core.utils import check_command_exists
from core.config import settings

def main():
    """
    微信数据库解密与提取工具 (WeChat DB Extractor)
    独立于主下载器，专注于从 Favorite.db 提取文章链接。
    """
    parser = argparse.ArgumentParser(
        description="微信数据库提取工具 - 解密 Favorite.db 并导出 URL",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # 必需参数
    parser.add_argument("-o", "--output", required=True, help="导出 URL 的目标文件路径 (如: input/db_urls.txt)")
    
    # 模式选择
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--db-path", help="加密的 Favorite.db 路径 (需要 --key)")
    group.add_argument("--decrypted-db", help="直接指定已解密的数据库路径")
    
    # 解密参数
    parser.add_argument("--key", help="微信数据库密钥 (配合 --db-path 使用)")
    
    args = parser.parse_args()

    # 1. 验证参数
    if args.db_path and not args.key:
        print("[Error] 使用 --db-path 时必须提供 --key")
        sys.exit(1)

    final_db_path = None
    temp_decrypted_db = "temp_decrypted.db"

    # 2. 解密流程 (如果需要)
    if args.db_path:
        # 检查 sqlcipher 依赖
        if not check_command_exists("sqlcipher"):
            print("[Error] 未找到 'sqlcipher' 命令，无法解密数据库。")
            print("请先安装 sqlcipher (如: sudo apt install sqlcipher) 或直接提供 --decrypted-db。")
            sys.exit(1)
            
        print(f"正在尝试解密数据库: {args.db_path}")
        if decrypt_wechat_db(args.db_path, args.key, temp_decrypted_db):
            final_db_path = temp_decrypted_db
            print(f"[Success] 数据库已解密至临时文件: {temp_decrypted_db}")
        else:
            print("[Error] 解密失败，请检查密钥是否正确。")
            sys.exit(1)
    else:
        # 直接使用已解密数据库
        if not os.path.exists(args.decrypted_db):
            print(f"[Error] 指定的数据库文件不存在: {args.decrypted_db}")
            sys.exit(1)
        final_db_path = args.decrypted_db

    # 3. 解析与提取
    print(f"正在解析数据库: {final_db_path} ...")
    articles = parse_favorite_db(final_db_path)
    
    if not articles:
        print("[Warning] 未提取到任何文章链接。")
        # 清理临时文件
        if args.db_path and os.path.exists(temp_decrypted_db):
            os.remove(temp_decrypted_db)
        sys.exit(0)

    # 4. 导出结果
    print(f"提取到 {len(articles)} 条文章记录，正在写入: {args.output}")
    
    # 确保输出目录存在
    output_dir = os.path.dirname(os.path.abspath(args.output))
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    if save_urls_to_file(articles, args.output):
        print(f"✅ 导出成功！")
        print(f"下一步：运行下载器 -> python get_wx_gzh.py {args.output}")
    else:
        print("[Error] 写入文件失败。")

    # 5. 清理临时文件
    if args.db_path and os.path.exists(temp_decrypted_db):
        try:
            os.remove(temp_decrypted_db)
            print(f"已清理临时解密文件: {temp_decrypted_db}")
        except Exception:
            pass

if __name__ == "__main__":
    main()
