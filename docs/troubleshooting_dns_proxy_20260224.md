# 技术故障排查报告：DNS 解析失败与代理配置问题 (2026-02-24)

## 问题描述
在执行 `batch_get_wechat_gzh.sh` 批量下载微信文章时，程序大规模报错：
- `Download failed (Anti-bot or Network)`
- `Failed to fetch ...: Name or service not known` (DNS 解析失败)
- 部分请求被重定向至 `verify.html` (触发微信验证码)

## 根本原因分析
1. **aiohttp 环境感知失效**：代码中 `aiohttp.ClientSession` 未设置 `trust_env=True`，导致程序忽略了系统环境变量中的 `http_proxy` 配置。
2. **DNS 路由冲突**：在开启 `v2rayN/singbox` 且设为 **Global (全局)** 模式时，DNS 解析完全依赖代理隧道。由于 `aiohttp` 尝试绕过代理进行直连，但在虚拟网卡环境下无法正常获取 DNS 解析结果，导致 `Name or service not known`。
3. **IP 风控触发**：全局模式下使用海外 IP 访问微信，极易触发微信的反爬虫验证（302 重定向）。

## 解决方案
1. **代码修复 (Surgical Fix)**：
   - 在 `core/app.py`、`core/downloader.py` 和 `core/image_handler.py` 中，统一为 `aiohttp.ClientSession` 增加了 `trust_env=True` 参数。
   - 优化了错误日志输出，支持捕获具体的 Python 异常类名，解决了“错误信息为空”的问题。
2. **环境配置优化 (Best Practice)**：
   - 建议将代理软件（如 v2rayN）设置为 **“绕过大陆 (Bypass Mainland China)”**。
   - 这样可以确保微信域名通过本地 DNS 解析并使用本地 IP 访问，既保证了 DNS 稳定性，又降低了被封锁的概率。

## 结论
`trust_env=True` 允许程序遵循系统的路由规则。在“绕过大陆”模式下，`aiohttp` 会自动根据路由表选择直连微信，从而获得最佳的下载稳定性和速度。
