#!/usr/bin/env python3
import os
import argparse
import sys
from core.config import settings
from core.logger import logger
from core.record_manager import RecordManager

def main():
    """
    离线扫描工具：扫描 output 目录，全量重建 wechat_records.csv 资产清单。
    """
    parser = argparse.ArgumentParser(description="微信文章资产清单重建工具 (CSV Exporter)")
    parser.add_argument("-o", "--output", default=None, help=f"指定输出目录 (默认: {settings.OUTPUT_DIR})")
    
    args = parser.parse_args()

    # 1. 确定输出目录路径
    output_dir = args.output if args.output else settings.OUTPUT_DIR
    output_dir = os.path.abspath(output_dir)

    # 检查目录是否存在
    if not os.path.exists(output_dir):
        logger.error(f"错误: 目标目录不存在 -> {output_dir}")
        sys.exit(1)

    logger.info(f"正在启动资产清单重建任务...")
    
    # 2. 实例化管理器并执行重建
    try:
        rm = RecordManager()
        rm.rebuild_from_folder(output_dir)
        logger.info("✅ 资产清单 wechat_records.csv 已更新！")
            
    except Exception as e:
        logger.error(f"💥 发生未预期异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n[User Interrupt] 操作已取消。")
