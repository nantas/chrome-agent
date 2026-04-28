# Scrapling Fetcher 指南

## 概览

Scrapling 是本仓库的默认抓取引擎，支持多种模式的 fetcher 以适应不同的页面类型和保护级别。

## Fetcher 选型

### `get` — 静态页面
**适用场景**: 低保护级别的静态页面、文章正文提取。
- 默认参数即可工作
- 支持 `impersonate` 参数模拟浏览器指纹
- 支持 `extraction_type`: `markdown`（默认）/ `text` / `html`
- 支持 `css_selector` 提取特定区域
- 支持 `main_content_only` 仅获取 body 内容

### `fetch` — SPA/动态页面
**适用场景**: 需要 JavaScript 渲染的页面、SPA、动态列表、分页内容。
- 使用 Playwright 浏览器获取页面
- 支持 `headless` / `headful` 模式
- 支持 `wait` / `wait_selector` / `network_idle` 等等待策略
- 支持 `disable_resources` 加速（排除字体、图片等非必要资源）
- 支持 `real_chrome` 使用本地安装的 Chrome

### `stealthy-fetch` — 受保护页面
**适用场景**: Cloudflare 挑战、WAF、高保护级别页面、反爬敏感目标。
- 包含指纹伪装和机器人检测绕过
- 支持 `solve_cloudflare` 自动解决 Cloudflare 挑战
- 支持 `hide_canvas` / `block_webrtc` 等隐私选项
- 支持 `proxy` 代理配置

### Bulk 变体

- `bulk_get`: 批量 GET 请求，适用于低保护的多 URL 场景
- `bulk_fetch`: 批量 Playwright 抓取，共享浏览器上下文
- `bulk_stealthy_fetch`: 批量反爬绕过抓取

### Session 变体

- 使用 `open_session` 创建持久浏览器会话
- 使用 `session_id` 复用已有会话
- 适用于认证会话复用、页面间 cookie 共享场景
- 会话用完后通过 `close_session` 释放

## 参数参考

### 通用参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `impersonate` | string | chrome | 浏览器指纹模拟版本 |
| `extraction_type` | string | markdown | 输出格式 |
| `main_content_only` | bool | true | 仅提取 body 内容 |
| `timeout` | int | 30 | 请求超时（秒） |
| `retries` | int | 3 | 重试次数 |
| `proxy` | string | null | 代理 URL |

### 浏览器相关参数（fetch / stealthy-fetch）

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `headless` | bool | true | 是否无头模式 |
| `wait` | int | 0 | 加载后等待（毫秒） |
| `wait_selector` | string | null | 等待选择器出现 |
| `network_idle` | bool | false | 等待网络空闲 |
| `disable_resources` | bool | false | 拒绝非必要资源 |
| `real_chrome` | bool | false | 使用本地 Chrome |
