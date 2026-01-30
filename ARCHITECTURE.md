# 技术架构说明书 (Technical Architecture) v4.6

本文档描述 **WeChat Fav Downloader** 的最新架构，重点介绍 v4.6 引入的应用化封装、动态解析器注册表以及配置中心化机制。

## 1. 架构图 (v4.6 Refactored)

```mermaid
graph TD
    CLI[CLI Entry Point] --> App[WeChatDownloaderApp]
    
    subgraph Core Logic
    App --> Config[Config Manager (.env/config.py)]
    App --> Logger[Structured Logger]
    App -- Download Only --> Downloader[Async Downloader]
    App -- Parse Result --> Registry[Parser Registry]
    App --> Converter[Converter]
    App --> Indexer[Index Manager (Jinja2)]
    end
    
    subgraph Parser System
    Registry -- Can Handle? --> P1[ImageDetailParser]
    Registry -- Can Handle? --> P2[StandardParser]
    Registry -- ... --> P3[Future Parsers]
    P1 -- Hybrid Mode --> P1_Result[JS Images + HTML Text]
    end
    
    subgraph Output
    App --> FS[File System (HTML/MD/PDF)]
    Indexer --> Template[Jinja2 Templates]
    end
```

## 2. 核心组件 (Core Components)

### 2.1 应用控制器 (`core.app.WeChatDownloaderApp`)
- **职责**: 应用程序的生命周期管理者与指挥官。
- **重构**: 现在显式协调 `Downloader` 获取源码与 `Registry` 执行解析，确保了 I/O 与逻辑的清晰分离。

### 2.2 动态解析器注册表 (`core.parsers.registry`)
- **设计模式**: 注册表模式 (Registry Pattern) + 责任链 (Chain of Responsibility) 思想。
- **解析器策略**:
    - **ImageDetailParser (混合解析)**: 针对图片频道。不仅提取 `picture_page_info_list` 里的高清图，还会智能检测并提取 `js_content` 里的传统正文。如果两者并存（混合模式文章），则合并输出，确保信息零丢失。
    - **StandardParser**: 作为万能回退方案，提取标准的 HTML 正文。

### 2.3 配置与模板 (`core.config` & `templates/`)
- **单一事实来源**: `Config` 类统一管理 `.env`、`config.json` 与 `cookies.txt`。所有配置加载逻辑收敛于此。
- **视图分离**: HTML 生成基于 Jinja2，便于样式的独立迭代。

### 2.4 异步并发 (Async Core)
- **下载器 (`core.downloader.download_html`)**: 现在是一个纯粹的异步 HTTP 客户端包装器，专注于高效、安全（防爬）地获取网页源码。
- **I/O**: `aiofiles` 实现非阻塞文件写入。

## 3. 关键流程

### 3.1 文章抓取与解析
1. **Fetch**: `Downloader` 获取 HTML 源码。
2. **Select**: 调用 `find_and_parse(html, url)`。
3. **Try**: 优先尝试特异性解析器（如 `ImageDetailParser`）。
4. **Fallback**: 如果失败，回退到 `StandardParser`。
5. **Return**: 返回统一的元数据字典。

### 3.2 索引生成
1. **Scan**: 扫描 `output/` 目录下的 `metadata.json`。
2. **Paginate**: 根据 `.env` 中的 `PAGE_SIZE` 进行分页。
3. **Render**: 使用 Jinja2 渲染 HTML 页面，包含导航栏。

## 4. 下一步计划 (Roadmap)
*   [ ] **Phase 3: SQLite 持久化**: 引入 SQLite 数据库替代 `history.log` 和全量文件扫描，解决万级文章后的性能瓶颈。
*   [ ] **Phase 4: 多媒体支持**: 基于新的解析器架构，轻松扩展视频和音频下载功能。