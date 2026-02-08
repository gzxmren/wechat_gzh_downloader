# 技术架构说明书 (Technical Architecture) v4.9

本文档描述 **WeChat Fav Downloader** 的最新架构，重点介绍 v4.9 引入的安全加固、环境预检以及异步持久化机制。

## 1. 架构图 (v4.9 Hardened)

```mermaid
graph TD
    CLI[CLI Entry Point] --> App[WeChatDownloaderApp]
    
    subgraph Pre-run
    App -- Check Deps --> Utils[Utils: Dependency Checker]
    end

    subgraph Core Logic
    App --> Config[Config Manager (.env/config.py)]
    App --> Logger[Structured Logger]
    App -- Download with Retry --> Downloader[Async Downloader]
    App -- Parse Result --> Registry[Parser Registry]
    App --> RecordMgr[Async Record Manager]
    App --> Indexer[Index Manager (SPA)]
    end
    
    subgraph Parser System
    Registry -- Can Handle? --> P1[ImageDetailParser]
    Registry -- Can Handle? --> P2[StandardParser]
    Registry -- ... --> P3[Future Parsers]
    P1 -- Hybrid Mode --> P1_Result[JS Images + HTML Text]
    end
    
    subgraph Output
    App --> FS[File System (HTML/MD/PDF)]
    Indexer --> Template[Jinja2 SPA Template]
    end
```

## 2. 核心组件 (Core Components)

### 2.1 环境预检 (`core.app.pre_run_check`)
- **职责**: 确保运行环境满足要求。在实际任务开始前，检查 `wkhtmltopdf` (PDF 模式) 或 `sqlcipher` (数据库模式) 是否可用。

### 2.2 异步持久化 (`core.record_manager`)
- **非阻塞 I/O**: 基于 `aiofiles` 实现。通过内存缓冲区拼接 CSV 行并执行异步追加，确保高并发抓取时不会因磁盘写入延迟阻塞事件循环。

### 2.3 安全加固层
- **HTML 净化**: `pdf_generator.py` 会在生成前过滤 `file://` 协议，防止 SSRF。
- **XSS 防御**: `index_manager.py` 对嵌入数据执行 Unicode 转义。
- **SQLi 防护**: `db_decrypter.py` 严格校验 Hex 密钥并转义 SQL 路径中的单引号。

### 2.4 动态解析器注册表 (`core.parsers.registry`)
- **设计模式**: 注册表模式 (Registry Pattern) + 责任链 (Chain of Responsibility) 思想。
- **解析器策略**:
    - **ImageDetailParser (混合解析)**: 针对图片频道。不仅提取 `picture_page_info_list` 里的高清图，还会智能检测并提取 `js_content` 里的传统正文。
    - **StandardParser**: 作为万能回退方案，提取标准的 HTML 正文。

## 3. 关键流程

### 3.1 环境预检
1. **Check**: 检查命令行参数中开启的功能。
2. **Verify**: 调用 `shutil.which` 验证对应二进制文件是否存在。
3. **Abort**: 若缺失关键依赖，则终止运行并提示安装。

### 3.2 异步重试流程
1. **Attempt**: 发起异步下载请求。
2. **Retry**: 若捕获异常，根据线性退避策略等待 `attempt * 2` 秒。
3. **Max**: 达到 `--retry` 上限后记录正式失败。

### 3.3 索引生成 (SPA Architecture)
1. **Scan**: 扫描 `output/` 目录下的 `metadata.json`。
2. **Generate**: 将元数据序列化为 JSON 并执行 HTML 安全转义。
3. **Render**: 使用 Jinja2 生成单页 `index.html`，通过内嵌 JSON 数据实现纯前端的搜索、排序与分页 (CSR)。

## 4. 下一步计划 (Roadmap)
*   [ ] **Phase 3: 多媒体支持**: 基于新的解析器架构，轻松扩展视频和音频下载功能。
