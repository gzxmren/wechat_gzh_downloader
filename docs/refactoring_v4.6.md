# Refactoring Report v4.6.0

## 1. 概述
本次重构的主要目标是将项目从“单文件脚本”架构迁移到“模块化应用程序”架构，以解决日益增长的维护难度和功能扩展瓶颈。重点解决了硬编码 HTML、配置分散、解析逻辑耦合过紧等问题。

## 2. 核心变更

### 2.1 应用化封装 (Application Class)
- **旧架构**: `get_wx_gzh.py` 承担了参数解析、状态管理、下载循环等所有职责，代码行数过多且难以测试。
- **新架构**: 
    - `get_wx_gzh.py`: 仅负责 `argparse` 参数解析，作为轻量级入口。
    - `core.app.WeChatDownloaderApp`: 封装了完整的应用生命周期（启动 -> 加载历史 -> 任务调度 -> 结果统计 -> 索引生成）。
    - 收益：核心逻辑可复用，方便编写集成测试。

### 2.2 动态解析器注册 (Dynamic Parser Registry)
- **旧架构**: 在 `downloader.py` 中使用 `if/else` 硬编码判断使用哪个解析器。新增解析器需要修改核心代码。
- **新架构**:
    - 引入 `core.parsers.registry` 和 `@register_parser` 装饰器。
    - 实现了 `find_and_parse` 机制：自动遍历所有注册的解析器，如果首选解析器（如 ImageDetail）虽然匹配但解析失败（返回 None），系统会自动回退到 StandardParser。
    - 收益：提高了鲁棒性，新增解析器（如 VideoParser）无需修改任何现有代码（OCP原则）。

### 2.3 视图层分离 (Templating)
- **旧架构**: `index_manager.py` 和 `html_saver.py` 中充斥着大量的 Python 字符串拼接 HTML 代码，维护 UI 极其痛苦。
- **新架构**:
    - 引入 **Jinja2** 模板引擎。
    - 创建 `templates/` 目录，存放 `index.html` 和 `pagination.html`。
    - 收益：前端样式与后端逻辑彻底分离，支持更复杂的页面逻辑（如分页）。

### 2.4 配置中心化 (Configuration)
- **旧架构**: 配置散落在 `get_wx_gzh.py` (CLI), `downloader.py` (JSON), `index_manager.py` (Hardcoded) 中。
- **新架构**:
    - `core.config.Config`: 统一从 `.env` 读取环境变量，并提供默认值。
    - 收益：统一管理 `PAGE_SIZE`, `CONCURRENCY` 等关键参数。

### 2.5 索引管理增强 (Index Manager)
- **去重逻辑**: 在生成索引时，新增了基于 `original_url` 的去重步骤。即使输出目录中存在多份相同文章的副本（例如文件夹重命名后残留），索引页也只会展示一条记录，保持界面整洁。
- **独立工具**: 新增 `regenerate_index.py` 脚本，复用了核心的索引生成逻辑。允许用户在不运行爬虫的情况下，随时基于现有的 `metadata.json` 文件快速重建索引 HTML。

## 3. 测试策略
本次重构同步引入了自动化测试体系：
- `tests/test_parsers.py`: 验证解析器注册表选择逻辑和内容提取准确性。
- `tests/test_app_flow.py`: 使用 Mock 模拟网络请求，验证 App 类的全流程（历史记录跳过、文件保存调用）。

## 4. 未来展望
当前的架构为 Phase 3（引入 SQLite）奠定了坚实基础。App 类可以轻松替换 `load_history` 方法以从数据库读取，而无需修改下载核心。
