# 技术笔记：CSV 解析风险与验证码 URL 处理 (2026-03-24)

## 1. 问题背景
在运行 `batch_get_wechat_gzh.sh` 脚本时，发现部分文章下载失败。通过日志分析，确认了两个核心诱因：
1. **CSV 解析错位**：原始脚本使用 `cut -d, -f5` 提取 URL，但在 CSV 格式中，如果标题包含半角英文逗号（`,`），该字段会被双引号包裹（如 `"Title, Part 2"`），导致 `cut` 误判列数。
2. **验证码重定向**：部分记录的第 5 列存入的是微信的反爬虫验证码页面 URL (`/mp/wappoc_appmsgcaptcha`)，而非文章正文链接。

## 2. 已实施的改进 (Code Changes)
在 `core/downloader.py` 中更新了 `validate_wx_url` 函数：
- **逻辑**：新增路径检查，明确拒绝包含 `/mp/wappoc_appmsgcaptcha` 的 URL。
- **效果**：防止程序浪费资源尝试下载并解析非文章页面，从源头过滤掉无效请求。

## 3. 待实施的建议 (Proposed Improvements)
虽然当前由于输入源标题改为中文逗号暂时规避了问题，但为增强健壮性，建议在未来进行以下修改：

### 3.1 替换 `cut` 为 Python CSV 解析器
在 Shell 脚本中，使用以下逻辑替代简单的 `cut` 操作：
```bash
tail -n 40 "$CSV_FILE" | python3 -c 'import csv, sys; reader = csv.reader(sys.stdin); [print(row[4] if (len(row) > 4 and "captcha" not in row[4]) else (row[5] if len(row) > 5 else "")) for row in reader]'
```
- **优点**：能够正确处理 CSV 中的引号引用和转义逗号，不再受标题内容影响。

### 3.2 URL 自动择优回退
- **策略**：如果 CSV 的第 5 列是验证码链接，自动尝试读取第 6 列（通常存有原始/干净的 URL）。
- **逻辑**：在上述 Python 脚本中已包含此回退判断。

## 4. 经验教训
- **中英文逗号差异**：在微信生态下，全角逗号 (`，`) 不会触发 CSV 引用，而半角逗号 (`,`) 会。
- **防御性提取**：对于来自第三方导出（如 Telegram 消息导出）的 CSV 数据，不能假设 URL 列始终有效，必须结合验证码特征进行过滤和列回退。
