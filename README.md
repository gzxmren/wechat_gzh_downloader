# WeChat Fav Downloader (微信收藏文章下载器)

一个基于 Python 的工具，用于将微信公众号文章批量下载并保存为本地 HTML、Markdown 和 PDF 文件。支持图片本地化存储，生成独立的内容包，并具备断点续传功能。

## ✨ 核心功能

*   **多模式导入**: 
    *   **聊天记录模式 (推荐)**: 自动提取“文件传输助手”导出文本中的链接。
    *   **数据库模式**: 自动解密并读取微信 `Favorite.db`。
    *   **文本模式**: 支持从 `urls.txt` 批量读取。
*   **多格式导出**: 
    *   **默认 HTML**: 默认生成包含所有样式和本地化资源的独立 HTML 文件。
    *   **可选 Markdown**: 可选生成干净的 **Markdown** (`--markdown`)。
    *   **可选 PDF**: 可选生成高质量的 **PDF** (`--pdf`)。
*   **资源本地化**: 自动下载图片到 `assets/` 目录，修正 HTML/Markdown/PDF 链接。
*   **内容清洗**: 自动移除广告、二维码和无关工具栏，生成纯净的阅读体验。
*   **数据资产化**: 为每篇文章生成 JSON 元数据，并自动维护一个全局可视化的 `index.html` 索引。
*   **断点续传**: 自动记录处理成功的 URL (`history.log`)，支持中断后继续运行。
*   **智能重试**: 内置失败重试机制，并记录错误日志 (`error.log`)。
*   **文件名智能截断**: 自动处理过长标题，防止文件系统错误。

## 🚀 快速开始

### 1. 环境准备
确保您的系统已安装 Python 3.10+。

```bash
# 安装依赖
pip install -r requirements.txt

# (可选，用于 PDF 输出) 导出 PDF 依赖 wkhtmltopdf
# 注意：默认安装的 wkhtmltopdf 可能不支持高级特性（如页码和目录）。
# 如果遇到问题，可尝试安装特定版本或接受程序自动降级为普通 PDF。
sudo apt install wkhtmltopdf
```

### 2. 模式 A：从聊天记录导出 (最简单)
1. 在 PC 微信收藏夹全选文章 -> 转发给“文件传输助手”。
2. 使用工具（如留痕/MemoTrace）导出与文件传输助手的聊天记录为 `messages.txt`。
3. 运行下载（默认生成 HTML）：
   ```bash
   python get_wx_gzh.py --chat-log input/messages.txt
   ```
   如果需要 Markdown 和 PDF：
   ```bash
   python get_wx_gzh.py --chat-log input/messages.txt --markdown --pdf
   ```

### 3. 模式 B：从数据库解密
```bash
python get_wx_gzh.py --db --key "YOUR_64_CHAR_KEY" --markdown --pdf
```

## ⚙️ 高级配置 (Advanced Config)

为了应对微信的反爬虫机制或下载特定权限的文章，您可以创建 `config.json` 来配置自定义 Header。

1. 将 `config.sample.json` 重命名为 `config.json`。
2. 在浏览器中获取您的 `Cookie` 和 `User-Agent`。
3. 填入 `config.json` 相应字段。

该文件已被 `.gitignore` 忽略，您的隐私数据不会被提交到仓库。

## ⚙️ 命令行参数

| 参数 | 说明 | 默认值 |
| :--- | :--- | :--- |
| `-i, --input` | 输入 URL 文件路径 | `input/urls.txt` |
| `--chat-log` | 指定聊天记录导出文件 (txt) | - |
| `--db` | 启用数据库读取模式 | - |
| `--markdown` | 启用 Markdown 生成 | `False` |
| `--pdf` | 启用 PDF 生成 | `False` |
| `--no-images` | 禁用图片下载 | `False` |
| `--retry` | 失败重试次数 | `1` |
| `--force` | 忽略 history.log，强制重新处理 | `False` |

## 🗺️ 项目路线图 (Roadmap)

*   [x] **v1.x/2.x**: Markdown 转换、图片本地化、PDF 导出。
*   [x] **v3.0/3.1**: 数据库读取、聊天记录正则提取。
*   [x] **v3.3**: 增加 `history.log` 实现断点续传和自动重试。
*   [x] **v3.4**: 渲染逻辑重构，优化正文提取与扁平目录结构。
*   [x] **v4.0**: 默认 HTML 输出、可选 Markdown/PDF、文件名智能截断、PDF 容错排版。
*   [x] **v4.1**: 元数据生成、全局 HTML 索引、正文内容智能清洗。
*   [x] **v4.2 (Current)**: 外部配置化支持 (Cookie/User-Agent)，增强反爬应对能力。
*   [ ] **v5.0 (Planned)**: 多媒体深度支持（视频/语音下载）。

## 📝 许可证
MIT License