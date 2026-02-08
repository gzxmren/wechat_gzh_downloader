# 程序使用指南 (Program Usage Guide)

> **文档目的**: 详细说明所有可执行程序、测试程序、检测调试工具的运行方式、参数配置和使用目的。
> 
> **最后更新**: 2026-02-09 (v5.0.0)

---

## 📑 目录

1. [主程序](#1-主程序)
2. [辅助工具程序](#2-辅助工具程序)
3. [测试程序](#3-测试程序)
4. [调试与检测工具](#4-调试与检测工具)
5. [完整使用流程示例](#5-完整使用流程示例)

---

## 1. 主程序

### 1.1 `get_wx_gzh.py` - 微信公众号文章下载器

#### 📌 程序目的
批量下载微信公众号文章并转换为本地 HTML/Markdown/PDF 文件，支持图片本地化、断点续传和异步并发。

#### 🚀 基本运行方式

```bash
# 1. 交互式模式 (New) - 推荐用于复杂 URL
# 直接运行，程序会提示粘贴 URL（无需加引号）
python get_wx_gzh.py

# 2. 智能文件读取 (New)
# 直接传入文件路径，自动识别为批量模式
python get_wx_gzh.py input/urls.txt

# 3. 智能单篇下载 (New)
# 直接传入 URL，自动识别为单篇模式
python get_wx_gzh.py https://mp.weixin.qq.com/s/xxxxx

# 4. 从聊天记录导出文件下载（推荐）
python get_wx_gzh.py --chat-log input/messages.txt

# 5. (传统方式) 显式指定输入文件
python get_wx_gzh.py -i input/urls.txt
```

#### 📋 完整参数列表

##### 基础参数

| 参数 | 类型 | 默认值 | 说明 | 示例 |
|------|------|--------|------|------|
| `url` | 位置参数 | - | **智能参数**: 可是单个 URL 或 URL 文件路径 | `python get_wx_gzh.py input/urls.txt` |
| `-i, --input` | 文件路径 | `input/urls.txt` | (传统) 输入 URL 文件路径 | `-i input/my_urls.txt` |
| `-o, --output` | 目录路径 | `output` | 输出目录路径 | `-o /path/to/output` |
| `-u, --user` | 字符串 | `MyWeChatUser` | 微信用户名前缀 | `-u MyAccount` |

##### 并发控制参数

| 参数 | 类型 | 默认值 | 说明 | 示例 |
|------|------|--------|------|------|
| `--concurrency` | 整数 | `3` | 全局并发处理文章数（建议 3-5） | `--concurrency 5` |

> **💡 提示**: 并发数过高可能触发微信反爬虫机制，建议保持在 3-5 之间。

##### 输入模式参数

| 参数 | 类型 | 默认值 | 说明 | 示例 |
|------|------|--------|------|------|
| `--chat-log` | 文件路径 | - | 指定导出的聊天记录文件（txt 格式） | `--chat-log input/messages.txt` |

##### 输出格式参数

| 参数 | 类型 | 默认值 | 说明 | 示例 |
|------|------|--------|------|------|
| `--markdown` | 开关 | `False` | 启用 Markdown 生成 | `--markdown` |
| `--pdf` | 开关 | `False` | 启用 PDF 生成（需要 wkhtmltopdf） | `--pdf` |
| `--no-images` | 开关 | `False` | 禁用图片下载（仅保存文本） | `--no-images` |

> **📝 注意**: 默认只生成 HTML 文件。如需 Markdown 或 PDF，必须显式指定参数。

##### 运行控制参数

| 参数 | 类型 | 默认值 | 说明 | 示例 |
|------|------|--------|------|------|
| `--retry` | 整数 | `1` | 单次运行的失败重试次数 | `--retry 3` |
| `--force` | 开关 | `False` | 强制处理所有 URL（忽略历史记录） | `--force` |

#### 💼 使用场景与示例

##### 场景 1: 从聊天记录批量下载（最常用）

```bash
# 1. 在 PC 微信收藏夹全选文章 -> 转发给"文件传输助手"
# 2. 使用工具（如留痕/MemoTrace）导出聊天记录为 messages.txt
# 3. 运行下载（默认生成 HTML）
python get_wx_gzh.py --chat-log input/messages.txt

# 同时生成 Markdown 和 PDF
python get_wx_gzh.py --chat-log input/messages.txt --markdown --pdf
```

**目的**: 最简单的批量下载方式，无需手动提取 URL。

---

##### 场景 2: 从 URL 列表下载

```bash
# 从默认文件 input/urls.txt 下载
python get_wx_gzh.py

# 从自定义文件下载
python get_wx_gzh.py input/my_articles.txt --markdown

# 设置并发数为 5
python get_wx_gzh.py input/urls.txt --concurrency 5
```

**目的**: 适合已有 URL 列表的情况。

---

##### 场景 3: 下载单篇文章

```bash
# 直接指定 URL
python get_wx_gzh.py https://mp.weixin.qq.com/s/xxxxx --markdown --pdf
```

**目的**: 快速下载单篇文章进行测试或临时保存。

---

##### 场景 4: 强制重新下载

```bash
# 忽略历史记录，强制重新处理所有 URL
python get_wx_gzh.py input/urls.txt --force

# 重新下载并重试 3 次
python get_wx_gzh.py input/urls.txt --force --retry 3
```

**目的**: 重新下载已处理过的文章，或修复之前失败的下载。

---

#### ⚙️ 配置文件与环境变量

程序会自动读取以下配置：

1. **`.env` 文件**（推荐）
   ```ini
   CONCURRENCY=3
   PAGE_SIZE=20
   LOG_LEVEL=INFO
   ```

2. **`config.json` 文件**（高级配置）
   ```json
   {
     "headers": {
       "User-Agent": "Mozilla/5.0 ...",
       "Cookie": "your_cookie_here"
     }
   }
   ```

3. **`cookies.txt` 文件**（登录凭证）
   ```
   直接粘贴浏览器中的 Cookie 字符串
   ```

**优先级**: 命令行参数 > `.env` 文件 > 程序默认值

---

#### 📊 输出结果

运行后会在 `output/` 目录生成：

```
output/
├── 文章标题_2026-02-07/
│   ├── 文章标题_2026-02-07.html      # 主 HTML 文件（默认）
│   ├── 文章标题_2026-02-07.md        # Markdown 文件（可选）
│   ├── 文章标题_2026-02-07.pdf       # PDF 文件（可选）
│   ├── metadata.json                  # 文章元数据
│   └── assets/                        # 本地化的图片
├── index.html                         # 全局索引页 (SPA单页应用)
├── all_records.json                   # 索引数据源
```

---

## 2. 辅助工具程序

### 2.1 `wechat_db_tool.py` - 数据库提取工具

#### 📌 程序目的
专门用于处理微信本地数据库 (`Favorite.db`)，支持解密并提取文章链接，作为下载的前置步骤。

#### 🚀 运行方式

```bash
# 1. 解密并提取 (Standard)
python wechat_db_tool.py --db-path input/Favorite.db --key "YOUR_KEY" -o input/db_urls.txt

# 2. 从已解密数据库提取
python wechat_db_tool.py --decrypted-db input/decrypted.db -o input/db_urls.txt
```

#### 📋 参数列表

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `-o, --output` | 路径 (必需) | 导出 URL 的目标文件 | `-o input/db_urls.txt` |
| `--db-path` | 路径 | 加密的 Favorite.db 路径 | `--db-path input/Favorite.db` |
| `--key` | 字符串 | 64位 Hex 密钥 (配合 --db-path) | `--key "abcdef..."` |
| `--decrypted-db` | 路径 | 直接指定已解密的数据库 | `--decrypted-db out.db` |

**依赖**: 运行解密模式需要系统安装 `sqlcipher`。

---

### 2.2 `regenerate_index.py` - 索引重建工具

#### 📌 程序目的
扫描 `output/` 目录下的所有文章，重新生成全局 HTML 索引页面（`index.html`）。

#### 🚀 运行方式

```bash
# 使用默认配置重建索引
python regenerate_index.py

# 指定每页显示 50 条记录
python regenerate_index.py --page-size 50

# 指定输出目录
python regenerate_index.py -o /path/to/output

# 组合使用
python regenerate_index.py -o output --page-size 30
```

#### 📋 参数列表

| 参数 | 类型 | 默认值 | 说明 | 示例 |
|------|------|--------|------|------|
| `-o, --output` | 目录路径 | `output` | 指定输出目录 | `-o /path/to/output` |
| `--page-size` | 整数 | 从 `.env` 读取（默认 20） | 临时覆盖每页记录数 | `--page-size 50` |

#### 💼 使用场景

##### 场景 1: 手动整理文章后重建索引

```bash
# 1. 手动删除或移动了 output/ 目录下的某些文章
# 2. 重建索引以反映最新状态
python regenerate_index.py
```

**目的**: 同步索引页与实际文件状态。

---

##### 场景 2: 修改分页配置后重建

```bash
# 1. 修改 .env 文件中的 PAGE_SIZE=50
# 2. 重建索引以应用新配置
python regenerate_index.py

# 或临时指定分页大小（不修改 .env）
python regenerate_index.py --page-size 50
```

**目的**: 调整索引页的分页显示。

---

##### 场景 3: 索引页损坏或丢失

```bash
# 重新生成索引页
python regenerate_index.py
```

**目的**: 恢复丢失或损坏的索引文件。

---

#### 📊 输出结果

```
output/
├── index.html              # 全局 SPA 索引页 (包含所有记录)
├── all_records.json        # 索引数据源 (JSON)
```

---

### 2.2 `export_records.py` - 资产清单导出工具

#### 📌 程序目的
扫描 `output/` 目录，全量重建 `wechat_records.csv` 资产清单，提供结构化的文章数据。

#### 🚀 运行方式

```bash
# 默认扫描并导出
python export_records.py

# 指定输出目录
python export_records.py -o /path/to/output
```

#### 📋 参数列表

| 参数 | 类型 | 默认值 | 说明 | 示例 |
|------|------|--------|------|------|
| `-o, --output` | 目录路径 | `output` | 指定输出目录 | `-o /path/to/output` |

#### 💼 使用场景

##### 场景 1: 生成文章清单用于统计分析

```bash
# 导出 CSV 清单
python export_records.py

# 使用 Excel 或其他工具打开 wechat_records.csv 进行分析
```

**目的**: 获取结构化的文章数据，便于统计、筛选和分析。

---

##### 场景 2: 数据迁移或备份

```bash
# 导出清单作为备份索引
python export_records.py -o backup/output
```

**目的**: 创建文章资产的备份清单。

---

#### 📊 输出结果

生成 `wechat_records.csv` 文件，包含以下字段：

| 字段 | 说明 |
|------|------|
| URL | 文章原始链接 |
| 标题 | 文章标题 |
| 作者 | 公众号名称 |
| 发布日期 | 文章发布时间 |
| 本地路径 | 本地存储路径 |
| 下载时间 | 下载时间戳 |
| 状态 | 处理状态 |

---

### 2.3 `clean_messages.py` - 聊天记录清洗工具

#### 📌 程序目的
从原始聊天记录或杂乱文本中提取干净的微信文章 URL，自动去重并保存为标准格式。

#### 🚀 运行方式

```bash
# 使用默认路径（input/messages.txt -> input/urls.txt）
python clean_messages.py

# 指定输入文件
python clean_messages.py input/my_messages.txt

# 指定输入和输出文件
python clean_messages.py input/messages.txt output/clean_urls.txt
```

#### 📋 参数列表

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| 第 1 个位置参数 | 文件路径 | `input/messages.txt` | 输入文件路径 |
| 第 2 个位置参数 | 文件路径 | `input/urls.txt` | 输出文件路径 |

#### 💼 使用场景

##### 场景 1: 从聊天记录提取 URL

```bash
# 1. 导出"文件传输助手"聊天记录为 messages.txt
# 2. 提取所有微信文章链接
python clean_messages.py

# 3. 生成的 input/urls.txt 可直接用于下载
python get_wx_gzh.py -i input/urls.txt
```

**目的**: 自动化提取 URL，避免手动复制粘贴。

---

##### 场景 2: 从杂乱文本提取 URL

```bash
# 从任意包含微信链接的文本文件提取
python clean_messages.py messy_text.txt clean_urls.txt
```

**目的**: 从混乱的文本中提取有效链接。

---

#### 🔍 处理逻辑

1. 使用正则表达式匹配微信文章 URL
2. 去除空格、引号、括号等干扰字符
3. 自动去重（保留首次出现）
4. 输出干净的 URL 列表（每行一个）

#### 📊 输出示例

```
https://mp.weixin.qq.com/s/xxxxx1
https://mp.weixin.qq.com/s/xxxxx2
https://mp.weixin.qq.com/s/xxxxx3
```

---

### 2.4 `clean_urls.py` - URL 去重工具

#### 📌 程序目的
清洗 URL 文件，去重并保持原始顺序，同时保留注释和空行。

#### 🚀 运行方式

```bash
# 默认处理 input/urls.txt（原地覆盖）
python clean_urls.py

# 指定输入文件
python clean_urls.py -i input/urls.txt

# 指定输出文件（不覆盖原文件）
python clean_urls.py -i input/urls.txt -o input/urls_clean.txt
```

#### 📋 参数列表

| 参数 | 类型 | 默认值 | 说明 | 示例 |
|------|------|--------|------|------|
| `-i, --input` | 文件路径 | `input/urls.txt` | 要处理的 URL 文件路径 | `-i input/urls.txt` |
| `-o, --output` | 文件路径 | 覆盖原文件 | 输出文件路径 | `-o input/urls_clean.txt` |

#### 💼 使用场景

##### 场景 1: 去除重复 URL

```bash
# 原地去重
python clean_urls.py -i input/urls.txt
```

**目的**: 清理重复的 URL，避免重复下载。

---

##### 场景 2: 保留原文件并生成新文件

```bash
# 生成新的去重文件
python clean_urls.py -i input/urls.txt -o input/urls_dedup.txt
```

**目的**: 保留原始文件作为备份。

---

#### 🔍 处理特点

- ✅ 保留注释行（以 `#` 开头）
- ✅ 保留空行
- ✅ 去重但保持原始顺序
- ✅ 不改变文件格式

#### 📊 输入/输出示例

**输入** (`urls.txt`):
```
# 重要文章
https://mp.weixin.qq.com/s/xxxxx1
https://mp.weixin.qq.com/s/xxxxx2

# 技术文章
https://mp.weixin.qq.com/s/xxxxx1  # 重复
https://mp.weixin.qq.com/s/xxxxx3
```

**输出**:
```
# 重要文章
https://mp.weixin.qq.com/s/xxxxx1
https://mp.weixin.qq.com/s/xxxxx2

# 技术文章
https://mp.weixin.qq.com/s/xxxxx3
```

---

### 2.5 `triage_tool.py` - 故障分诊管理工具

#### 📌 程序目的
管理解析失败的文章样本，支持人工分诊和测试用例生成，用于持续改进解析器质量。

#### 🚀 运行方式

```bash
# 列出所有失败样本
python triage_tool.py list

# 人工分诊交互模式（推荐）
python triage_tool.py review

# 手动提升样本为测试用例
python triage_tool.py promote <folder_name> -n <fixture_name>
```

#### 📋 子命令详解

##### 子命令 1: `list` - 列出失败样本

```bash
python triage_tool.py list
```

**输出示例**:
```
时间                 | 原因                 | URL (部分)
-------------------------------------------------------------------------------------
2026-02-07_10:30:15 | ParseError          | https://mp.weixin.qq.com/s/xxx...
  目录: triage_samples/2026-02-07_10:30:15_ParseError
-------------------------------------------------------------------------------------
```

**目的**: 快速查看所有捕获的失败样本。

---

##### 子命令 2: `review` - 人工分诊交互模式（推荐）

```bash
python triage_tool.py review
```

**交互流程**:

1. **自动打开浏览器**: 显示失败样本的 HTML 内容
2. **输入预期结果**: 
   - 标题（必填）
   - 作者（可选，默认 "Unknown_Account"）
   - 发布日期（可选，默认 "2026-01-01"）
3. **生成测试用例**: 自动创建 HTML + JSON 对到 `tests/fixtures/`
4. **清理原始样本**: 可选删除已处理的样本

**示例对话**:
```
>>> 正在分诊样本: 2026-02-07_10:30:15_ParseError
>>> 原始 URL: https://mp.weixin.qq.com/s/xxxxx
>>> 正在打开浏览器供你查看文章内容...

--- 请输入该文章的期望解析结果 (直接回车表示跳过或保持默认) ---
标题 [原捕获: ParseError]: AI 技术发展趋势
作者: TechInsight
发布日期 (YYYY-MM-DD): 2026-02-05

✅ 已成功将用例存入测试库: regression_AI技术发展趋势
是否删除原始 Triage 样本? (y/n): y
🗑️ 原始样本已清理。

是否继续处理下一个? (y/n): n
```

**目的**: 将失败样本转化为回归测试用例，持续改进解析器。

---

##### 子命令 3: `promote` - 手动提升样本

```bash
python triage_tool.py promote <folder_name> -n <fixture_name>
```

**参数**:
| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `folder_name` | 位置参数 | `triage_samples/` 下的文件夹名 | `2026-02-07_10:30:15_ParseError` |
| `-n, --name` | 可选 | 指定生成的 fixture 文件名 | `-n my_test_case` |

**示例**:
```bash
python triage_tool.py promote 2026-02-07_10:30:15_ParseError -n image_detail_case
```

**目的**: 快速将样本移动到测试库（不需要交互）。

---

#### 💼 使用场景

##### 场景 1: 定期检查失败样本

```bash
# 每周运行一次，查看是否有新的失败样本
python triage_tool.py list
```

**目的**: 监控解析器的健康状况。

---

##### 场景 2: 构建回归测试库

```bash
# 人工分诊所有失败样本
python triage_tool.py review

# 生成的测试用例会自动添加到 tests/fixtures/
# 运行测试验证
python3 -m unittest tests.test_parsers
```

**目的**: 持续改进解析器质量，防止回归。

---

#### 📊 输出结果

在 `tests/fixtures/` 目录生成：

```
tests/fixtures/
├── regression_AI技术发展趋势.html    # 原始 HTML
└── regression_AI技术发展趋势.json    # 真理文件
```

**真理文件示例** (`*.json`):
```json
{
  "_comment": "这是测试真理文件。title/author/date 是预期解析结果。",
  "title": "AI 技术发展趋势",
  "author": "TechInsight",
  "publish_date": "2026-02-05",
  "url": "https://mp.weixin.qq.com/s/xxxxx",
  "type": "standard",
  "expect_failure": false,
  "reason": "Normal article"
}
```

---

## 3. 测试程序

### 3.1 `tests/test_parsers.py` - 解析器测试

#### 📌 测试目的
验证所有解析器（标准解析器、图片频道解析器）的正确性，确保能准确提取文章元数据。

#### 🚀 运行方式

```bash
# 运行所有解析器测试
python3 -m unittest tests.test_parsers

# 运行特定测试类
python3 -m unittest tests.test_parsers.TestStandardParser

# 运行特定测试方法
python3 -m unittest tests.test_parsers.TestStandardParser.test_parse_standard_article

# 详细输出模式
python3 -m unittest tests.test_parsers -v
```

#### 📋 测试内容

| 测试类 | 测试范围 | 测试数量 |
|--------|---------|---------|
| `TestStandardParser` | 标准解析器 | 多个 fixtures |
| `TestImageDetailParser` | 图片频道解析器 | 多个 fixtures |
| `TestParserRegistry` | 解析器注册表 | 动态选择逻辑 |

#### 💼 使用场景

##### 场景 1: 代码重构后验证

```bash
# 修改了解析器代码后，运行测试确保没有破坏现有功能
python3 -m unittest tests.test_parsers -v
```

**目的**: 回归测试，防止代码改动引入 Bug。

---

##### 场景 2: 添加新测试用例后验证

```bash
# 使用 triage_tool.py review 添加新测试用例后
python3 -m unittest tests.test_parsers
```

**目的**: 验证新测试用例是否通过。

---

#### 📊 测试输出示例

```
test_parse_standard_article (tests.test_parsers.TestStandardParser) ... ok
test_parse_image_detail_article (tests.test_parsers.TestImageDetailParser) ... ok
test_registry_selection (tests.test_parsers.TestParserRegistry) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.234s

OK
```

---

### 3.2 `tests/test_app_flow.py` - 应用流程测试

#### 📌 测试目的
端到端集成测试，验证完整的下载→解析→保存流程。

#### 🚀 运行方式

```bash
# 运行所有应用流程测试
python3 -m unittest tests.test_app_flow

# 详细输出
python3 -m unittest tests.test_app_flow -v
```

#### 📋 测试内容

- 完整下载流程
- 多格式输出（HTML/Markdown/PDF）
- 断点续传功能
- 错误处理和重试机制

#### 💼 使用场景

```bash
# 发布新版本前运行完整测试
python3 -m unittest tests.test_app_flow -v
```

**目的**: 确保核心功能正常工作。

---

### 3.3 `tests/test_downloader_mock.py` - 下载器 Mock 测试

#### 📌 测试目的
使用 Mock 隔离测试下载器模块，不依赖真实网络请求。

#### 🚀 运行方式

```bash
# 运行下载器 Mock 测试
python3 -m unittest tests.test_downloader_mock

# 详细输出
python3 -m unittest tests.test_downloader_mock -v
```

#### 📋 测试内容

- HTTP 请求逻辑
- 错误处理
- 重试机制
- 超时处理

---

### 3.4 `tests/test_async_downloader.py` - 异步下载器测试

#### 📌 测试目的
验证异步并发下载功能的正确性和性能。

#### 🚀 运行方式

```bash
# 运行异步下载器测试
python3 -m unittest tests.test_async_downloader

# 详细输出
python3 -m unittest tests.test_async_downloader -v
```

#### 📋 测试内容

- 并发下载逻辑
- 异步任务调度
- 资源管理
- 并发控制

---

### 3.5 运行所有测试

#### 🚀 运行方式

```bash
# 自动发现并运行所有测试
python3 -m unittest discover tests

# 详细输出
python3 -m unittest discover tests -v

# 仅运行特定模式的测试
python3 -m unittest discover tests -p "test_parser*.py"
```

#### 📊 完整测试输出示例

```
test_parse_standard_article (tests.test_parsers.TestStandardParser) ... ok
test_parse_image_detail_article (tests.test_parsers.TestImageDetailParser) ... ok
test_app_download_flow (tests.test_app_flow.TestAppFlow) ... ok
test_downloader_retry (tests.test_downloader_mock.TestDownloader) ... ok
test_async_concurrency (tests.test_async_downloader.TestAsyncDownloader) ... ok

----------------------------------------------------------------------
Ran 5 tests in 1.234s

OK
```

---

## 4. 调试与检测工具

### 4.1 日志系统

#### 📌 目的
记录程序运行过程中的所有信息，便于调试和问题排查。

#### 🚀 配置方式

##### 方式 1: 通过 `.env` 文件

```ini
# .env
LOG_LEVEL=DEBUG  # 可选: DEBUG, INFO, WARNING, ERROR
```

##### 方式 2: 查看日志文件

```bash
# 实时查看日志
tail -f app.log

# 查看最后 100 行
tail -n 100 app.log

# 搜索错误日志
grep "ERROR" app.log

# 搜索特定 URL 的日志
grep "https://mp.weixin.qq.com/s/xxxxx" app.log
```

#### 📋 日志级别说明

| 级别 | 用途 | 示例场景 |
|------|------|---------|
| `DEBUG` | 详细调试信息 | 开发调试时使用 |
| `INFO` | 常规运行信息 | 日常使用（默认） |
| `WARNING` | 警告信息 | 非致命问题 |
| `ERROR` | 错误信息 | 下载失败、解析错误 |

#### 💼 使用场景

##### 场景 1: 调试解析失败问题

```bash
# 1. 设置 DEBUG 级别
echo "LOG_LEVEL=DEBUG" > .env

# 2. 运行程序
python get_wx_gzh.py https://mp.weixin.qq.com/s/xxxxx

# 3. 查看详细日志
tail -f app.log
```

**目的**: 获取详细的解析过程信息。

---

##### 场景 2: 排查下载失败原因

```bash
# 查看所有错误日志
grep "ERROR" app.log | tail -n 20

# 查看特定 URL 的日志
grep "https://mp.weixin.qq.com/s/xxxxx" app.log
```

**目的**: 快速定位问题原因。

---

### 4.2 故障样本自动捕获

#### 📌 目的
自动捕获解析失败的文章样本，供后续分析和测试。

#### 🚀 工作原理

程序运行时，如果遇到解析失败，会自动：

1. 保存原始 HTML 到 `triage_samples/`
2. 记录失败原因和 URL
3. 生成时间戳目录

#### 📋 捕获的样本结构

```
triage_samples/
└── 2026-02-07_10:30:15_ParseError/
    ├── source.html        # 原始 HTML
    ├── metadata.json      # 失败信息
    └── error.log          # 错误日志
```

#### 💼 使用场景

```bash
# 1. 运行下载程序（自动捕获失败样本）
python get_wx_gzh.py -i input/urls.txt

# 2. 查看捕获的样本
python triage_tool.py list

# 3. 人工分诊
python triage_tool.py review
```

**目的**: 持续改进解析器，构建测试用例库。

---

### 4.3 手动调试技巧

#### 技巧 1: 测试单个 URL

```bash
# 使用 DEBUG 级别测试单个 URL
echo "LOG_LEVEL=DEBUG" > .env
python get_wx_gzh.py https://mp.weixin.qq.com/s/xxxxx
```

---

#### 技巧 2: 强制重新下载

```bash
# 忽略历史记录，强制重新处理
python get_wx_gzh.py https://mp.weixin.qq.com/s/xxxxx --force
```

---

#### 技巧 3: 禁用图片下载加快调试

```bash
# 仅下载文本，加快调试速度
python get_wx_gzh.py https://mp.weixin.qq.com/s/xxxxx --no-images
```

---

#### 技巧 4: 使用 Python 交互式调试

```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或使用 ipdb（更友好）
import ipdb; ipdb.set_trace()
```

---

## 5. 完整使用流程示例

### 流程 1: 从零开始批量下载文章

```bash
# 步骤 1: 准备聊天记录
# 在 PC 微信中：收藏夹 -> 全选 -> 转发给"文件传输助手"
# 使用工具导出聊天记录为 input/messages.txt

# 步骤 2: 清洗聊天记录（可选）
python clean_messages.py

# 步骤 3: 去重 URL（可选）
python clean_urls.py -i input/urls.txt

# 步骤 4: 下载文章
python get_wx_gzh.py --chat-log input/messages.txt --markdown --pdf

# 步骤 5: 查看结果
# 打开 output/index.html 浏览所有文章
```

---

### 流程 2: 处理失败样本并改进解析器

```bash
# 步骤 1: 运行下载（自动捕获失败样本）
python get_wx_gzh.py -i input/urls.txt

# 步骤 2: 查看失败样本
python triage_tool.py list

# 步骤 3: 人工分诊
python triage_tool.py review

# 步骤 4: 运行测试验证
python3 -m unittest tests.test_parsers -v

# 步骤 5: 如果测试失败，修改解析器代码并重新测试
# （重复步骤 4 直到所有测试通过）
```

---

### 流程 3: 重新整理文章并更新索引

```bash
# 步骤 1: 手动整理 output/ 目录
# 删除不需要的文章，或移动到其他位置

# 步骤 2: 重建索引
python regenerate_index.py

# 步骤 3: 导出资产清单
python export_records.py

# 步骤 4: 查看结果
# 打开 output/index.html 和 wechat_records.csv
```

---

### 流程 4: 调试特定文章的解析问题

```bash
# 步骤 1: 启用 DEBUG 日志
echo "LOG_LEVEL=DEBUG" > .env

# 步骤 2: 下载单篇文章
python get_wx_gzh.py https://mp.weixin.qq.com/s/xxxxx --force

# 步骤 3: 查看详细日志
tail -f app.log

# 步骤 4: 如果失败，查看捕获的样本
python triage_tool.py list

# 步骤 5: 在浏览器中查看原始 HTML
# 打开 triage_samples/<folder_name>/source.html

# 步骤 6: 修改解析器代码并重新测试
python get_wx_gzh.py https://mp.weixin.qq.com/s/xxxxx --force
```

---

## 📝 附录

### A. 常见问题排查

#### 问题 1: 下载失败，提示反爬虫

**解决方案**:
```bash
# 1. 配置 Cookie 和 User-Agent
cp config.sample.json config.json
# 编辑 config.json，填入浏览器的 Cookie

# 2. 降低并发数
python get_wx_gzh.py -i input/urls.txt --concurrency 1

# 3. 增加重试次数
python get_wx_gzh.py -i input/urls.txt --retry 3
```

---

#### 问题 2: PDF 生成失败

**解决方案**:
```bash
# 1. 检查 wkhtmltopdf 是否安装
which wkhtmltopdf

# 2. 安装 wkhtmltopdf
sudo apt install wkhtmltopdf

# 3. 如果仍然失败，仅生成 HTML 和 Markdown
python get_wx_gzh.py -i input/urls.txt --markdown
```

---

#### 问题 3: 索引页显示不正确

**解决方案**:
```bash
# 重建索引
python regenerate_index.py

# 清空浏览器缓存后刷新
```

---

### B. 性能优化建议

1. **并发数设置**: 建议 3-5，过高可能触发反爬虫
2. **禁用图片下载**: 使用 `--no-images` 可显著提升速度
3. **仅生成 HTML**: 不使用 `--markdown` 和 `--pdf` 可节省时间
4. **批量处理**: 使用文件模式比单个 URL 模式更高效

---

### C. 快速命令参考卡

```bash
# 下载
python get_wx_gzh.py --chat-log input/messages.txt
python get_wx_gzh.py -i input/urls.txt --markdown --pdf
python get_wx_gzh.py <URL> --force

# 维护
python regenerate_index.py --page-size 50
python export_records.py
python clean_messages.py
python clean_urls.py -i input/urls.txt

# 调试
python triage_tool.py list
python triage_tool.py review
tail -f app.log

# 测试
python3 -m unittest discover tests -v
python3 -m unittest tests.test_parsers
```

---

**文档维护**: 请在程序功能发生变化时更新本文档。
