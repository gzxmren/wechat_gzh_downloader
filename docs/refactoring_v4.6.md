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

### 2.6 资产清单管理 (Asset Management) [Planned]
- **CSV 数据持久化**: 计划引入 `output/wechat_records.csv` 替代纯文本的 `history.log`。
- **字段定义**: `url, status, title, author, published_date, folder_name, timestamp, failure_reason, source`。
- **记录管理器 (RecordManager)**: 将实现一个统一的数据访问层 (DAO) `core/record_manager.py`，负责处理 CSV 的读写操作。
    - **增量模式**: 主程序下载完成后，调用管理器追加一条记录。
    - **重建模式**: Helper 工具扫描文件系统元数据，全量重建 CSV，确保数据与磁盘一致。
- **收益**: 提供可分享、可分析的结构化资产列表，同时作为去重和断点续传的依据。

## 3. 测试策略
本次重构引入了基于 Python `unittest` 标准库的自动化测试体系，确保核心逻辑的稳定。

### 3.1 解析器单元测试 (`tests/test_parsers.py`)
- **目的**: 验证解析器的“识别”与“提取”逻辑是否准确。
- **核心逻辑**:
    - **Mock 数据**: 在内存中构造模拟的 HTML 片段（标准图文、图片频道）。
    - **注册表验证**: 检查 `find_and_parse` 是否能根据 HTML 特征准确选择对应的解析器类。
    - **字段校验**: 深入解析器内部，校验其提取的 `title`, `author`, `date` 等字段是否符合预期。
- **适用场景**: 修改解析逻辑（正则、选择器）或新增解析器类型时。

### 3.2 应用流程集成测试 (`tests/test_app_flow.py`)
- **目的**: 模拟用户真实使用场景，验证各模块（下载、转换、记录、索引）的协作。
- **核心逻辑**:
    - **外部依赖 Mock**: 使用 `unittest.mock` 拦截 `fetch_article` 和文件 IO 操作，避免真实的网络请求和磁盘污染。
    - **断点续传测试**: 模拟旧版 `history.log` 环境，验证 `RecordManager` 的自动迁移逻辑以及程序是否能正确跳过已下载链接。
    - **资产清单验证**: 确认在模拟下载完成后，`output/wechat_records.csv` 是否被正确创建并记录了任务状态。
- **适用场景**: 重构主流程、修改配置管理或升级资产管理系统时。

### 3.3 测试环境与副作用 (Side Effects)
- **`tests/test_parsers.py`**: 纯内存运行，不会在磁盘生成任何文件。
- **`tests/test_app_flow.py`**:
    - **临时文件**: 测试运行期间会在 `tests/test_output/` 生成模拟的 HTML/MD 文件及 `wechat_records.csv`。同时会创建临时的 `history.log` 用于验证迁移逻辑。
    - **自动清理**: 脚本内置了 `tearDown` 机制，在每个测试用例结束后会自动删除产生的临时目录和 `.bak` 文件，确保工作区整洁。
    - **异常处理**: 若测试中途崩溃，可能会残留 `tests/test_output/` 或 `history.log.bak`，手动删除即可。

### 3.4 如何运行测试与解读结果
```bash
# 运行全部自动化测试
python3 -m unittest discover tests
```
- **OK**: 逻辑正确，所有断言通过。
- **F (Fail)**: 逻辑错误，测试会指出预期值与实际值的差异。
- **E (Error)**: 代码崩溃，通常由语法错误、路径不存在或 Mock 配置不当引起。

## 4. 未来展望
当前的架构为 Phase 3（引入 SQLite）奠定了坚实基础。App 类可以轻松替换 `load_history` 方法以从数据库读取，而无需修改下载核心。
