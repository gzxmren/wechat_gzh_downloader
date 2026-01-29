#!/usr/bin/env python3
import os
import argparse
import sys
from core.config import settings
from core.logger import logger
from core.index_manager import generate_global_index

def main():
    """
    手动重建全局索引的辅助程序。
    它会扫描输出目录下的 metadata.json 文件，并根据 Jinja2 模板重新生成分页的 index.html。
    """
    parser = argparse.ArgumentParser(description="微信文章索引重建工具 (Index Regenerator)")
    parser.add_argument("-o", "--output", default=None, help=f"指定输出目录 (默认: {settings.OUTPUT_DIR})")
    parser.add_argument("--page-size", type=int, default=None, help="临时覆盖每页记录数 (默认从 .env 读取)")
    
    args = parser.parse_args()

    # 1. 确定输出目录路径
    output_dir = args.output if args.output else settings.OUTPUT_DIR
    output_dir = os.path.abspath(output_dir)

    # 检查目录是否存在
    if not os.path.exists(output_dir):
        logger.error(f"错误: 目标目录不存在 -> {output_dir}")
        sys.exit(1)

    # 2. 如果指定了 page_size，临时修改设置
    if args.page_size:
        settings.PAGE_SIZE = args.page_size
        logger.info(f"临时设置 PAGE_SIZE = {args.page_size}")

    logger.info(f"正在启动索引重建任务...")
    logger.info(f"目标目录: {output_dir}")
    logger.info(f"当前配置: PAGE_SIZE={settings.PAGE_SIZE}")

    # 3. 调用核心索引生成逻辑
    try:
        success = generate_global_index(output_dir)
        
        if success:
            logger.info("✅ 索引重建完成！请刷新浏览器查看 index.html")
        else:
            logger.error("❌ 索引重建过程中出现错误。")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 发生未预期异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n[User Interrupt] 操作已取消。")
