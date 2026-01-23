# 实施计划：异步架构升级 (Asynchronous & Rate Limiting)

## 1. 目标概述
将现有的同步阻塞架构转换为基于 `asyncio` 的异步非阻塞架构。
*   **效率提升**：支持多任务并行（如：同时抓取多篇文章、并发下载单篇文章内的所有图片）。
*   **安全可控**：通过 `Semaphore` 控制全局并发数，并保留随机延迟机制。
*   **平滑回退**：对于 `wkhtmltopdf` 等不支持异步的外部工具，采用线程池隔离。

## 2. 受影响的文件列表
| 文件路径 | 变更类型 | 预期逻辑变更 |
| :--- | :--- | :--- |
| `requirements.txt` | 新增 | 添加 `aiohttp`, `aiofiles` 等依赖。 |
| `core/downloader.py` | 重构 | `requests` 替换为 `aiohttp.ClientSession`，核心函数变为 `async`。 |
| `core/image_handler.py` | 重构 | 图片下载逻辑改为异步并行，支持在一个协程池中批量下载图片。 |
| `core/pdf_generator.py` | 封装 | 使用 `asyncio.create_subprocess_exec` 或 `run_in_executor` 调用外部 CLI。 |
| `get_wx_gzh.py` | 重构 | 主循环改为 `asyncio.gather`，并使用 `Semaphore` 进行全局并发限制。 |

## 3. 详细实施步骤

### Step 1: 异步底层构建 (Downloader)
*   引入 `aiohttp.ClientSession` 管理长连接池。
*   实现异步请求重试逻辑（结合 `tenacity` 或自定义装饰器）。
*   **并发控制点**：在 `Downloader` 类中引入 `asyncio.Semaphore(n)`，确保同时发出的 HTTP 请求不超过 `n` 个。

### Step 2: 资源并行化 (ImageHandler)
*   **现状**：单篇文章的图片是逐个顺序下载的。
*   **优化**：将一篇文章的所有图片 URL 放入一个任务列表，使用 `asyncio.gather` 并行下载。
*   **优势**：由于图片分散在微信 CDN 的不同节点，并发下载可极速完成资源本地化。

### Step 3: CPU & 外部工具隔离
*   **解析逻辑**：BeautifulSoup 解析 DOM 是 CPU 密集型任务，虽不耗时，但在极高并发下会阻塞 Event Loop。计划在必要时使用 `loop.run_in_executor`。
*   **PDF 生成**：`wkhtmltopdf` 是进程密集型。将使用 `asyncio.Semaphore` 独立限制 PDF 生成的进程数（例如：最多同时启动 2 个 PDF 进程，以免压垮 CPU）。

### Step 4: 主调度器升级 (Orchestrator)
*   实现 `ProcessingQueue`：将所有待处理 URL 放入队列。
*   **令牌桶/漏桶算法**：在异步循环中插入 `await asyncio.sleep(random.uniform(min, max))`，确保整体频率符合人类行为特征。

## 4. 潜在风险评估

1.  **反爬风控 (High)**：并发过高可能导致触发微信的“验证码”页面。
    *   *应对*：默认全局并发数设置为 1-3，提供配置项供用户微调；强制在任务间加入随机休眠。
2.  **内存占用 (Medium)**：大量并发协程在内存中持有大型 HTML 字符串和图片数据。
    *   *应对*：限制同时处理的文章数量，及时释放 `BeautifulSoup` 对象。
3.  **连接泄露 (Low)**：异步连接池未正确关闭。
    *   *应对*：使用 `async with` 确保 `ClientSession` 自动回收。

## 5. 预期交付物
*   一个支持异步抓取的 `v4.5` 版本。
*   配置文件新增 `concurrency` 和 `delay_range` 参数。
*   日志系统能够清晰追踪异步任务的开始与完成。
