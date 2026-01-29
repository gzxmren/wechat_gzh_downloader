# 技术架构说明书 (Technical Architecture) v4.6

本文档描述 **WeChat Fav Downloader** 的最新架构，重点介绍 v4.6 引入的应用化封装、动态解析器注册表以及配置中心化机制。

## 1. 架构图 (v4.6 Refactored)

```mermaid
graph TD
    CLI[CLI Entry Point] --> App[WeChatDownloaderApp]
    
    subgraph Core Logic
    App --> Config[Config Manager (.env/config.py)]
    App --> Logger[Structured Logger]
    App --> Downloader[Async Downloader]
    App --> Converter[Converter]
    App --> Indexer[Index Manager (Jinja2)]
    end
    
    subgraph Parser System
    Downloader -- Find & Parse --> Registry[Parser Registry]
    Registry -- Can Handle? --> P1[ImageDetailParser]
    Registry -- Can Handle? --> P2[StandardParser]
    Registry -- ... --> P3[Future Parsers]
    end
    
    subgraph Output
    App --> FS[File System (HTML/MD/PDF)]
    Indexer --> Template[Jinja2 Templates]
    end
```

## 2. 核心组件 (Core Components)

### 2.1 应用控制器 (`core.app.WeChatDownloaderApp`)
- **职责**: 取代了原先的“上帝脚本”，负责应用程序的生命周期管理。
- **功能**:
    - 初始化环境与配置。
    - 加载历史记录 (`load_history`)。
    - 调度并发下载任务 (`process_single_url`)。
    - 统一错误处理与日志记录。

### 2.2 动态解析器注册表 (`core.parsers.registry`)
- **设计模式**: 注册表模式 (Registry Pattern) + 责任链 (Chain of Responsibility) 思想。
- **机制**:
    - **自动注册**: 使用 `@register_parser` 装饰器，新解析器只需定义即可自动加入系统。
    - **鲁棒选择 (`find_and_parse`)**: 系统会遍历所有已注册解析器，不仅询问 `can_handle`，还会尝试执行 `parse`。如果首选解析器失败（例如误判），系统会自动回退到下一个可用解析器（如 StandardParser），极大地提高了在大规模抓取时的容错率。

### 2.3 配置与模板 (`core.config` & `templates/`)
- **配置中心化**: `Config` 类统一管理环境变量 (`.env`)、JSON 配置与 CLI 参数默认值。
- **视图分离**: HTML 生成逻辑不再硬编码在 Python 字符串中，而是迁移到了 `templates/` 目录下的 **Jinja2** 模板文件中 (`index.html`, `pagination.html`)，便于前端样式的独立维护。

### 2.4 异步并发 (Async Core)
- **下载**: `aiohttp` + `Semaphore` 控制并发。
- **I/O**: `aiofiles` 实现非阻塞文件写入。
- **图片**: 单篇文章内的图片采用 `asyncio.gather` 并行下载。

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