# WeChat Fav Downloader (微信收藏文章下载器)

一个基于 Python 的工具，用于将微信公众号文章批量下载并保存为本地 HTML、Markdown 和 PDF 文件。支持图片本地化存储，生成独立的内容包，并具备断点续传功能。

## ✨ 核心功能

*   **多模式导入**: 
    *   **聊天记录模式 (推荐)**: 自动提取“文件传输助手”导出文本中的链接。
    *   **数据库模式 (通过辅助工具)**: 自动解密并读取微信 `Favorite.db`。
    *   **文本模式**: 支持从 `urls.txt` 批量读取。
*   **多格式导出**: 
    *   **默认 HTML**: 默认生成包含所有样式和本地化资源的独立 HTML 文件。
    *   **可选 Markdown**: 可选生成干净的 **Markdown** (`--markdown`)。
    *   **可选 PDF**: 可选生成高质量的 **PDF** (`--pdf`)。
*   **资源本地化**: 自动下载图片到 `assets/` 目录，修正 HTML/Markdown/PDF 链接。
*   **内容清洗**: 自动移除广告、二维码和无关工具栏，生成纯净的阅读体验。
*   **智能解析**: 自动适配标准图文与特殊图片频道 (`image_detail`)，解决部分文章无正文的问题。
*   **数据资产化**: 为每篇文章生成 JSON 元数据，并自动维护一个全局可视化的 `index.html` 索引。
*   **断点续传**: 自动记录处理成功的 URL (`wechat_records.csv`)，支持中断后继续运行。
*   **异步并发 (New)**: 基于 `asyncio` 的异步架构，支持多任务并行抓取和图片并行下载，显著提升处理效率。
*   **异步重试 (New)**: 完善的重试机制与线性退避策略，大幅提升弱网环境下的任务成功率。
*   **环境预检 (New)**: 启动时自动检测 `wkhtmltopdf` 等核心依赖，提供友好的错误提示。
    *   **交互式体验 (v5.2 New)**:
        *   **持续交互模式**: 使用 `--interactive` 进入循环会话，可持续处理 URL。
        *   **管道模式**: 支持从标准输入读取 URL (例如 `cat urls.txt | python get_wx_gzh.py`)，便于脚本集成。
## 🚀 快速开始

### 1. 环境准备
确保您的系统已安装 Python 3.10+。

```bash
# 安装依赖
pip install -r requirements.txt

# (可选，用于 PDF 输出) 导出 PDF 依赖 wkhtmltopdf
sudo apt install wkhtmltopdf
```

### 2. 模式 A：从聊天记录导出 (最简单)
1. 在 PC 微信收藏夹全选文章 -> 转发给“文件传输助手”。
2. 使用工具（如留痕/MemoTrace）导出与文件传输助手的聊天记录为 `messages.txt`。
3. 运行下载：
   ```bash
   python get_wx_gzh.py --chat-log input/messages.txt
   ```

### 3. 模式 B：从数据库提取 (Pipeline Workflow)
这是一个两步走流程：先提取链接，再批量下载。

**步骤 1: 提取链接**
使用专用工具 `wechat_db_tool.py` 从微信数据库提取 URL。
```bash
# 解密并提取 (需要 sqlcipher)
python wechat_db_tool.py --db-path input/Favorite.db --key "YOUR_KEY" -o input/db_urls.txt
```

**步骤 2: 批量下载**
将提取到的 URL 列表传给下载器。
```bash
python get_wx_gzh.py input/db_urls.txt --markdown --pdf
```

### 4. 模式 C：交互式与管道模式 (v5.2 New)

#### 持续交互模式 (推荐)
启动一个循环会话，可以连续输入 URL 进行处理，输入 `quit` 退出。
```bash
python get_wx_gzh.py --interactive
```

#### 管道模式 (推荐用于脚本)
支持从其他命令通过管道传递 URL 列表。
```bash
cat my_urls.txt | python get_wx_gzh.py
```

#### 智能参数模式
直接传入 URL 或文件名进行处理。
```bash
# 下载单篇文章
python get_wx_gzh.py https://mp.weixin.qq.com/s/xxxxx

# 从文件批量下载
python get_wx_gzh.py input/urls.txt
```

## ⚙️ 基础配置 (Basic Config)

支持使用项目根目录下的 `.env` 文件进行快速参数配置（推荐）。
常用配置项：
```ini
CONCURRENCY=3
PAGE_SIZE=20
LOG_LEVEL=INFO
```

## ⚙️ 命令行参数

| 参数 | 说明 | 默认值 |
| :--- | :--- | :--- |
| `url` | 智能参数 (URL 或 文件路径) | - |
| `-i, --input` | (传统) 输入 URL 文件路径 | `input/urls.txt` |
| `--concurrency` | 全局并发处理文章数 | `3` |
| `--chat-log` | 指定聊天记录导出文件 (txt) | - |
| `--markdown` | 启用 Markdown 生成 | `False` |
| `--pdf` | 启用 PDF 生成 | `False` |
| `--no-images` | 禁用图片下载 | `False` |
| `--retry` | 失败重试次数 | `1` |
| `--force` | 忽略 wechat_records.csv，强制重新处理 | `False` |

## 🛠️ 辅助工具 (Helper Tools)

### 数据库提取工具 (`wechat_db_tool.py`)
用于从加密的 `Favorite.db` 中导出文章链接。详见模式 B。

### 索引重建工具 (`regenerate_index.py`)
手动刷新全局 SPA 索引页面。
```bash
python regenerate_index.py
```

## 🗺️ 项目路线图 (Roadmap)

*   [x] **v4.5**: 异步架构升级，支持全局并发控制与图片并行下载。
*   [x] **v4.8**: 交互式体验升级与 SPA 索引重构。
*   [x] **v4.9**: 安全加固（XSS/SQLi/SSRF）与异步持久化。
*   [x] **v5.0 (Current)**: 数据库功能解耦，引入 `wechat_db_tool.py` 专用提取工具。
*   [ ] **v5.x (Planned)**: 多媒体深度支持（视频/语音下载）。

## 🧪 测试 (Testing)

```bash
# 运行全部自动化测试
python3 -m unittest discover tests
```

## 📝 许可证
MIT License
