import re
import os
import sys

def extract_wechat_urls(input_file, output_file):
    """
    从原始聊天记录或杂乱文本中提取干净的微信文章 URL。
    """
    if not os.path.exists(input_file):
        print(f"错误: 找不到输入文件 '{input_file}'")
        return

    # 匹配微信公众号文章 URL 的正则表达式
    # 排除空格、引号、括号、中文等字符
    url_pattern = re.compile(r'https?://mp\.weixin\.qq\.com/s[^\s\u4e00-\u9fa5"\'\(\)\<\>\[\]]+')
    
    urls = []
    seen = set()
    
    try:
        print(f"正在读取: {input_file} ...")
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                matches = url_pattern.findall(line)
                for url in matches:
                    # 进一步清理末尾可能的标点符号
                    clean_url = url.rstrip('.,;)!?')
                    if clean_url not in seen:
                        urls.append(clean_url)
                        seen.add(clean_url)
        
        if not urls:
            print("未发现有效的微信文章链接。")
            return

        # 写入输出文件
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_file, 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(url + '\n')
        
        print(f"清洗完成！")
        print(f"共提取到 {len(urls)} 个唯一的微信文章链接。")
        print(f"结果已保存至: {output_file}")
        
    except Exception as e:
        print(f"处理过程中出现错误: {e}")

if __name__ == "__main__":
    # 默认路径配置
    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_input = os.path.join(base_dir, "input/messages.txt")
    default_output = os.path.join(base_dir, "input/urls.txt")
    
    # 支持命令行参数: python clean_messages.py [input_file] [output_file]
    input_path = sys.argv[1] if len(sys.argv) > 1 else default_input
    output_path = sys.argv[2] if len(sys.argv) > 2 else default_output
    
    extract_wechat_urls(input_path, output_path)
