# 代码重构与架构升级记录 (v4.4 Refactoring)

## 1. 重构背景
随着项目功能的迭代，`downloader.py` 中的 `fetch_article` 函数逐渐变得臃肿。它同时承担了网络请求、反爬检测、标准 DOM 解析、特殊 JS 数据解析（图片频道）以及 Fail-Safe 调度等多重职责。这种“上帝函数”不仅难以维护，也阻碍了未来新功能（如视频解析）的扩展。

## 2. 目标架构：策略模式 (Strategy Pattern)
为了解耦各部分逻辑，我们引入了 **策略模式**。将具体的解析逻辑从下载器中剥离，封装为独立的“解析器类”，并通过统一的接口进行调度。

### 目录结构变更
```
wechat_fav_downloader/
└── core/
    ├── downloader.py       # (瘦身) 仅负责网络请求、反爬检测和调度
    ├── parsers/            # (新建) 解析器包
    │   ├── __init__.py     # 调度器 (Dispatcher)
    │   ├── base.py         # 抽象基类 (BaseParser)
    │   ├── standard.py     # 标准图文解析器 (StandardParser)
    │   └── image_detail.py # 图片频道解析器 (ImageDetailParser)
```

## 3. 详细实现方案

### 3.1 基类设计 (`parsers/base.py`)
定义了所有解析器必须遵守的接口契约：
```python
class BaseParser(ABC):
    @abstractmethod
    def parse(self, html, url):
        """
        输入 HTML 和 URL，返回标准化的文章数据字典。
        失败则返回 None。
        """
        pass
```

### 3.2 标准解析器 (`parsers/standard.py`)
*   **职责**：处理 90% 的普通图文消息。
*   **逻辑**：
    *   使用 `BeautifulSoup` 解析 DOM。
    *   提取 `<div class="rich_media_content">` 等标准容器。
    *   **增强**：整合了通用的元数据提取逻辑（标题、作者、日期），包括 Title Fallback（从 `og:title` 提取）。即使正文提取失败，也能返回基础信息供其他解析器复用。

### 3.3 图片频道解析器 (`parsers/image_detail.py`)
*   **职责**：处理基于 JS 渲染的“图片频道” (`image_detail`)。
*   **逻辑**：
    1.  **括号平衡算法**：从 `picture_page_info_list=[` 开始，通过计数 `[` 和 `]` 精准截取数组内容，彻底解决了正则非贪婪匹配导致的截断问题。
    2.  **对象块隔离**：将数组内容按 `{}` 切分为独立对象。
    3.  **首选匹配**：在每个对象块内，仅提取**首个** `cdn_url`，有效过滤了水印、缩略图等干扰项。
    4.  **HTML 重构**：将提取到的图片 URL 组装成标准的 HTML 结构 (`<div id="js_content">...</div>`)，确保下游转换器无缝兼容。

### 3.4 调度器 (`parsers/__init__.py`)
实现了 **Fail-Safe** 调度策略：
```python
def parse_html(html, url):
    # 1. 优先尝试标准解析 (提取元数据)
    std_result = StandardParser().parse(html, url)
    if std_result['content_html']:
        return std_result
        
    # 2. 如果正文为空，降级尝试图片频道解析
    img_result = ImageDetailParser().parse(html, url)
    if img_result:
        # 合并结果：使用 ImageDetail 的正文 + Standard 的标题/日期
        std_result['content_html'] = img_result['content_html']
        return std_result
        
    return None
```

### 3.5 下载器瘦身 (`downloader.py`)
`fetch_article` 函数现在只关注：
1.  加载配置 (`config.json`)。
2.  执行 HTTP 请求。
3.  反爬检测 (`verify.html` 检测)。
4.  调用 `parse_html` 获取结果。

## 4. 收益总结
1.  **可维护性大幅提升**：每个解析器只关注特定类型的页面，逻辑互不干扰。
2.  **扩展性增强**：未来如果需要支持“视频消息”，只需新增 `parsers/video.py` 并在调度器中注册即可，无需修改现有代码。
3.  **健壮性提高**：通过对象隔离和精准截取，彻底修复了图片重复和缺失的 Bug。
