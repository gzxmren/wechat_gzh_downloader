from core.record_manager import RecordManager
from core.index_manager import generate_global_index
from core.config import settings
import os

def main():
    output_dir = str(settings.OUTPUT_DIR)
    print(f"--- 正在执行离线资产清单同步 ---")
    print(f"目标目录: {output_dir}")
    
    # 1. 实例化管理器并执行物理扫描重建 CSV
    rm = RecordManager()
    rm.rebuild_from_folder(output_dir)
    
    # 2. 基于新的 CSV 生成 index.html
    print("正在刷新 index.html...")
    generate_global_index(output_dir)
    
    # 3. 统计结果
    with open(rm.csv_path, 'r', encoding='utf-8-sig') as f:
        count = sum(1 for line in f) - 1 # 减去表头
    
    print(f"--- 同步完成 ---")
    print(f"当前物理有效文章数: {count}")

if __name__ == "__main__":
    main()
