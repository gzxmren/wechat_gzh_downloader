#!/usr/bin/env python3
import os
import argparse
import shutil
import json
import webbrowser
from pathlib import Path
from core.triage.manager import TriageManager

def main():
    parser = argparse.ArgumentParser(description="微信文章下载器 - 故障分诊管理工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 1. List samples
    subparsers.add_parser("list", help="列出所有失败样本")

    # 2. Promote sample (Legacy mode)
    promote_parser = subparsers.add_parser("promote", help="将样本提升为测试用例 (手动模式)")
    promote_parser.add_argument("folder_name", help="triage_samples 下的文件夹名")
    promote_parser.add_argument("-n", "--name", help="指定生成的 fixture 文件名")

    # 3. Review samples (The Human Loop - Interactive Mode)
    subparsers.add_parser("review", help="人工分诊交互模式 (The Human Loop)")

    args = parser.parse_args()
    manager = TriageManager()

    if args.command == "list":
        samples = manager.list_samples()
        if not samples:
            print("目前没有捕获到任何失败样本。")
            return
        print(f"{ '时间':<20} | { '原因':<20} | { 'URL (部分)':<40}")
        print("-" * 85)
        for s in samples:
            url_display = s['url'][:37] + "..." if len(s['url']) > 40 else s['url']
            print(f"{s['timestamp']:<20} | {s['reason']:<20} | {url_display:<40}")
            print(f"  目录: {s['folder_name']}")
            print("-" * 85)

    elif args.command == "review":
        samples = manager.list_samples()
        if not samples:
            print("☕ 没有需要分诊的样本，休息一下吧！")
            return

        print(f"发现 {len(samples)} 个待处理样本。开始分诊流程...\n")
        
        for s in samples:
            folder_name = s['folder_name']
            sample_dir = manager.storage_dir / folder_name
            html_path = sample_dir / "source.html"
            
            print(f"\n>>> 正在分诊样本: {folder_name}")
            print(f">>> 原始 URL: {s['url']}")
            
            # 自动打开浏览器供用户查看
            print(f">>> 正在打开浏览器供你查看文章内容...")
            webbrowser.open(f"file://{html_path.absolute()}")
            
            print("\n--- 请输入该文章的期望解析结果 (直接回车表示跳过或保持默认) ---")
            title = input(f"标题 [原捕获: {s.get('exception') or '未知'}]: ").strip()
            if not title:
                print("跳过此样本。" )
                continue
                
            author = input("作者: ").strip() or "Unknown_Account"
            publish_date = input("发布日期 (YYYY-MM-DD): ").strip() or "2026-01-01"
            
            # 生成“真理文件” (Ground Truth JSON)
            truth_data = {
                "_comment": "这是测试真理文件。title/author/date 是预期解析结果。若 expect_failure 为 true，则预期解析器返回 None。",
                "title": title,
                "author": author,
                "publish_date": publish_date,
                "url": s['url'],
                "type": "standard",
                "expect_failure": False,
                "reason": "Normal article"
            }
            
            # 确定存储名称 (将标题作为文件名的一部分)
            safe_name = "".join([c for c in title if c.isalnum()])[:20]
            fixture_base = f"regression_{safe_name}"
            
            fixtures_dir = Path("tests/fixtures")
            fixtures_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存 HTML 和 JSON 对
            shutil.copy(html_path, fixtures_dir / f"{fixture_base}.html")
            with open(fixtures_dir / f"{fixture_base}.json", 'w', encoding='utf-8') as f:
                json.dump(truth_data, f, indent=4, ensure_ascii=False)
                
            print(f"✅ 已成功将用例存入测试库: {fixture_base}")
            
            # 询问是否删除原始样本
            confirm = input("是否删除原始 Triage 样本? (y/n): ").lower()
            if confirm == 'y':
                shutil.rmtree(sample_dir)
                print("🗑️ 原始样本已清理。" )
            
            if input("\n是否继续处理下一个? (y/n): ").lower() != 'y':
                break

    elif args.command == "promote":
        # ... (保持原有的 promote 逻辑，略) ...
        sample_dir = manager.storage_dir / args.folder_name
        if not sample_dir.exists():
            print(f"错误: 样本目录不存在 -> {sample_dir}")
            return
        fixture_name = args.name if args.name else args.folder_name
        if not fixture_name.endswith(".html"):
            fixture_name += ".html"
        fixtures_dir = Path("tests/fixtures")
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(sample_dir / "source.html", fixtures_dir / fixture_name)
        print(f"✅ 已将样本移动至: {fixtures_dir / fixture_name}")

if __name__ == "__main__":
    main()