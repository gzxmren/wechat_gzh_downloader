# 微信公众号媒体处理逻辑说明 (WeChat Media Handling Logic)

本文档详细说明了微信公众号文章中视频、音频及图片的处理逻辑，包括技术实现路径、标准转换方式及潜在风险评估。

## 1. 核心实现逻辑 (Core Implementation Logic)

微信网页使用了一系列自定义标签（如 `<mpvoice>`）和流媒体技术，本项目通过“标准化 (Standardization)”流程将其转化为通用 HTML5 格式。

### A. 音频处理 (Audio Handling)

1.  **普通音频 (`<audio>`)**
    *   **场景**：作者直接上传的 MP3/M4A 音频。
    *   **处理**：提取 `src` 链接，下载至 `assets/` 目录，并将 HTML 中的路径替换为本地相对路径。
2.  **微信语音 (`<mpvoice>`)**
    *   **场景**：录音或语音消息。
    *   **特征**：源码中仅有 `voice_encode_fileid` 属性，无 `src`。
    *   **破解路径**：利用微信接口构造下载链接：`https://res.wx.qq.com/voice/getvoice?mediaid={voice_encode_fileid}`。
    *   **标准化**：将 `<mpvoice>` 标签替换为标准的 `<audio controls>` 标签，确保在非微信环境下可播放。

### B. 视频处理 (Video Handling)

1.  **直传小视频 (`<video>`)**
    *   **场景**：作者直接上传到微信后台的小视频文件。
    *   **处理**：直接下载其 `src` 指向的 MP4 文件，本地化存储并更新 HTML 引用。
2.  **腾讯视频嵌入 (`<iframe>`)**
    *   **场景**：插入的腾讯视频（长视频、高清视频）。
    *   **局限**：此类视频通常采用 HLS (m3u8) 分片协议及加密技术。
    *   **策略**：本项目目前**不涉及**流媒体抓取（不调用 ffmpeg 合并切片），在生成的 HTML 中将保留原始 iframe，用户需在联网环境下观看。

---

## 2. 风险评估与技术边界 (Risk Assessment & Technical Boundaries)

### A. 腾讯视频支持 (Tencent Video Support)
*   **重度依赖问题**：下载嵌入式腾讯视频需要引入 `yt-dlp` 或 `ffmpeg`，这会增加项目体积（100MB+）并降低处理速度。
*   **结论**：本项目专注于“资源型资产”的离线化，不尝试破解复杂的流媒体系统。

### B. 防盗链与链接过期 (Anti-Hotlink & Expiration)
*   **Referer 校验**：微信服务器（如 `res.wx.qq.com`）对请求头有严格校验。
    *   **方案**：在下载请求中伪装 `Referer: https://mp.weixin.qq.com/`。
*   **有效期限制**：部分媒体链接（尤其是视频）包含有时效性的 `token`。
    *   **方案**：采取“即时下载”策略，在解析文章的同时完成下载，避免链接失效。

---

## 3. 待实施计划 (Next Steps)

1.  **重构资源管理器**：将 `core/image_handler.py` 升级为 `core/media_handler.py`，支持多格式下载。
2.  **增强转换逻辑**：在 `core/converter.py` 中增加对 `mpvoice` 标签的正则表达式解析与 HTML 转换逻辑。
3.  **路径映射优化**：确保 HTML、Markdown 及 PDF 都能正确指向本地化的多媒体资源。
