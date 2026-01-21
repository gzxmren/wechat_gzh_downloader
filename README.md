# WeChat Fav Downloader (微信收藏文章下载器)

一个基于 Python 的工具，用于将微信公众号文章批量下载并保存为本地 Markdown 文件。支持图片本地化存储，生成独立的内容包，完美支持离线阅读。

## ✨ 核心功能

*   **批量下载**: 支持从文本文件导入文章 URL 列表。
*   **格式转换**: 将复杂的 HTML 转换为干净的 Markdown。
*   **离线阅读**: 自动下载文章内的所有图片到本地 `assets/` 目录，并修正 Markdown 链接。
*   **智能归档**: 按 `日期/文章标题` 生成独立的内容包文件夹。
*   **去重机制**: 图片基于 MD5 哈希去重，避免重复下载。

## 🚀 快速开始

### 1. 环境准备
确保您的系统已安装 Python 3.10+。

```bash
# 安装依赖
pip install -r requirements.txt

# (可选) 如果需要生成 PDF，请安装 wkhtmltopdf
sudo apt install wkhtmltopdf
```

### 2. 配置文章链接
在 `input/urls.txt` 文件中填入您想要下载的微信文章链接，每行一个。
```text
https://mp.weixin.qq.com/s/example_link_1
https://mp.weixin.qq.com/s/example_link_2
```

### 3. 运行程序
```bash
python get_wx_gzh.py
```

### 4. 查看结果
下载完成后，请查看 `output/` 目录。

...

## ⚙️ 配置说明

您可以在 `get_wx_gzh.py` 顶部修改以下配置：

| 变量 | 说明 | 默认值 |
| :--- | :--- | :--- |
| `WECHAT_USERNAME` | 用于生成文件夹前缀的用户名 | `"MyWeChatUser"` |
| `DOWNLOAD_IMAGES` | 是否开启图片本地化下载 | `True` |
| `GENERATE_PDF` | 是否生成 PDF (暂未实装) | `True` |

## 🗺️ 项目路线图 (Roadmap)

*   [x] **v1.0**: 基础 Markdown 转换与批量 URL 下载。
*   [x] **v2.0**: 图片本地化下载、独立内容包打包。
*   [x] **v2.1**: PDF 格式同步导出 (基于 pdfkit)。
*   [ ] **v3.0 (TODO)**: 自动读取微信收藏夹数据库。
    *   支持 Windows PC 端微信密钥自动获取。
    *   实现 `EnMicroMsg.db` / `FTSFavorite.db` 的 SQLCipher 解密。
    *   自动提取“收藏文章”分类下的所有 URL。
*   [ ] **v3.1 (TODO)**: 视频与多媒体内容识别（仅记录链接，暂不下载）。

## 📝 许可证
MIT License
