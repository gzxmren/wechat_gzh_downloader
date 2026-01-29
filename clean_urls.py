import os
import argparse

def clean_urls(input_file, output_file=None):
    """
    清洗 URL 文件：去重并保持原始顺序，保留注释和空行。
    """
    if not os.path.exists(input_file):
        print(f"[Error] 文件不存在: {input_file}")
        return

    seen_urls = set()
    cleaned_lines = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            # 如果是空行或注释，直接保留
            if not stripped or stripped.startswith('#'):
                cleaned_lines.append(line)
                continue
            
            # 如果是 URL，进行去重判断
            url = stripped
            if url not in seen_urls:
                seen_urls.add(url)
                cleaned_lines.append(line)
            else:
                # 重复的 URL 被跳过
                pass

    # 如果未指定输出文件，则覆盖原文件
    target_file = output_file if output_file else input_file
    
    with open(target_file, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    
    print(f"[Success] 处理完成！")
    print(f"  原始行数: {sum(1 for _ in open(input_file)) if output_file else 'N/A'}") # 仅在非原地操作时方便对比
    print(f"  保留的唯一 URL 数: {len(seen_urls)}")
    print(f"  结果已保存至: {target_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="URL 文件去重辅助工具")
    parser.add_argument("-i", "--input", default="input/urls.txt", help="要处理的 URL 文件路径 (默认: input/urls.txt)")
    parser.add_argument("-o", "--output", help="输出文件路径 (默认覆盖原文件)")
    
    args = parser.parse_args()
    clean_urls(args.input, args.output)
