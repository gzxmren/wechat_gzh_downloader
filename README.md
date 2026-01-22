# WeChat Fav Downloader (微信收藏文章下载器)

一个基于 Python 的工具，用于将微信公众号文章批量下载并保存为本地 Markdown 和 PDF 文件。支持图片本地化存储，生成独立的内容包，并具备断点续传功能。

## ✨ 核心功能

*   **多模式导入**: 
    *   **聊天记录模式 (推荐)**: 自动提取“文件传输助手”导出文本中的链接。
    *   **数据库模式**: 自动解密并读取微信 `Favorite.db`。
    *   **文本模式**: 支持从 `urls.txt` 批量读取。
*   **双格式导出**: 同时生成干净的 **Markdown** 和高质量的 **PDF**。
*   **资源本地化**: 自动下载图片到 `assets/` 目录，修正 Markdown/PDF 链接。
*   **断点续传**: 自动记录处理成功的 URL (`history.log`)，支持中断后继续运行。
*   **自动重试**: 内置失败重试机制，并记录错误日志 (`error.log`)。

## 🚀 快速开始

### 1. 环境准备
确保您的系统已安装 Python 3.10+。

```bash
# 安装依赖
pip install -r requirements.txt

# (必须) 导出 PDF 依赖 wkhtmltopdf
sudo apt install wkhtmltopdf
```

### 2. 模式 A：从聊天记录导出 (最简单)
1. 在 PC 微信收藏夹全选文章 -> 转发给“文件传输助手”。
2. 使用工具（如留痕/MemoTrace）导出与文件传输助手的聊天记录为 `messages.txt`。
3. 运行下载：
   ```bash
   python get_wx_gzh.py --chat-log input/messages.txt
   ```

### 3. 模式 B：从数据库解密
```bash
python get_wx_gzh.py --db --key "YOUR_64_CHAR_KEY"
```

## ⚙️ 命令行参数

| 参数 | 说明 | 默认值 |
| :--- | :--- | :--- |
| `-i, --input` | 输入 URL 文件路径 | `input/urls.txt` |
| `--chat-log` | 指定聊天记录导出文件 (txt) | - |
| `--db` | 启用数据库读取模式 | - |
| `--retry` | 失败重试次数 | `1` |
| `--force` | 忽略 history.log，强制重新处理 | `False` |
| `--no-pdf` | 禁用 PDF 生成 | `False` |

## 🗺️ 项目路线图 (Roadmap)

*   [x] **v1.x/2.x**: Markdown 转换、图片本地化、PDF 导出。
*   [x] **v3.0/3.1**: 数据库读取、聊天记录正则提取。
*   [x] **v3.3**: 增加 `history.log` 实现断点续传和自动重试。
*   [x] **v3.4 (Current)**: 渲染逻辑重构，优化正文提取与扁平目录结构。
*   [ ] **v4.0 (TODO)**: 优化 PDF 排版（增加目录、页码支持）。

## 📝 许可证
MIT License