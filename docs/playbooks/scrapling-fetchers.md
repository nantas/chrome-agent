# 引擎 Fetcher 指南

## 概览

本仓库支持多个抓取引擎，按 `default_rank` 顺序选择。所有引擎及其特性评分定义在 `configs/engine-registry.json`。

### 引擎分类

| 引擎 | 类型 | rank | 场景 | Preflight |
|------|------|------|------|-----------|
| `scrapling-get` | `http` | 1 | 静态页面 | Scrapling CLI preflight |
| `obscura-fetch` | `cdp_lightweight` | 2 | 轻度动态页/SPA | Obscura CLI preflight |
| `scrapling-fetch` | `playwright` | 3 | 完整浏览器 | Scrapling CLI preflight |
| `scrapling-stealthy-fetch` | `playwright_stealth` | 4 | 高保护页面 | Scrapling CLI preflight |

### Preflight 要求

在选择任何引擎之前，先执行对应引擎的 CLI preflight：

```bash
# Scrapling 引擎
./scripts/scrapling-cli.sh preflight
# 或
$HOME/.cache/chrome-agent-scrapling/bin/scrapling --version

# Obscura 引擎
# 检查 OBSURA_CLI_PATH 环境变量，或检查受管安装
# 详见 docs/playbooks/obscura-cli-preflight.md
```

只有当对应 CLI 可用后，才进入引擎选型。

## Scrapling Fetcher 选型

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

## Obscura Fetcher

### `obscura-fetch` — 轻度动态页面（cdp_lightweight）
**适用场景**: 需要 JS 渲染但不需要完整 Chromium 的页面（动态列表、搜索页、轻度 SPA）。
- 使用 Rust+V8 轻量级 headless 浏览器，内存 ~8MB 空闲 / ~50MB 峰值
- 加载速度比 Scrapling Playwright 快 2-3.5x
- 内置 V8 引擎，支持 ES 模块和 async/await
- 支持 CSS 选择器等待和 networkidle 等待策略
- 内置 robots.txt 合规（`--obey-robots`）
- 支持 DOM→Markdown 转换（CDP `LP.getMarkdown`）

### 已知限制

- **重 JS 动画库**（如 GSAP）可能引发 V8 超时/死锁 → 建议升到 `scrapling-fetch`
- **专业反爬服务**（如 scrapingbee.com）即使使用 `--stealth` 模式也可检测 → 建议升到 `scrapling-stealthy-fetch`
- **Cloudflare 挑战**无法绕过 → 建议升到 `scrapling-stealthy-fetch`
- **WebSocket / Service Worker** 不支持

### 命令格式

```bash
# 基本用法
obscura fetch <URL> --dump html

# 指定等待策略
obscura fetch <URL> --wait-until networkidle0

# 提取文本
obscura fetch <URL> --dump text

# 评估 JS 表达式
obscura fetch <URL> --eval "document.title"

# 启用 TLS 伪装和 tracker 拦截
obscura fetch <URL> --stealth

# 启用 robots.txt 合规
obscura fetch <URL> --obey-robots
```

### Preflight 要求

使用 `obscura-fetch` 前，必须先执行 Obscura CLI preflight：

```bash
# 检查 OBSURA_CLI_PATH 环境变量
if [ -n "$OBSCURA_CLI_PATH" ] && [ -x "$OBSCURA_CLI_PATH" ]; then
  echo "OK: $OBSCURA_CLI_PATH"
elif [ -x "$HOME/.cache/chrome-agent-obscura/bin/obscura" ]; then
  echo "OK: managed install"
else
  echo "Obscura CLI not found. Run Obscura CLI preflight."
  # 详见 docs/playbooks/obscura-cli-preflight.md
fi
```

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
