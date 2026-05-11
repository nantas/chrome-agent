# Design

## Context

调研（2026-05-11）确认 CloakBrowser（CloakHQ/CloakBrowser, v0.3.27）的 57 个 C++ 源码级 Chromium patch 在以下场景显著优于现有管线：

| 场景 | 现有引擎结果 | CloakBrowser 结果 |
|------|-------------|-------------------|
| TLS 指纹检测（scrapingbee.com/blog） | obscura-fetch: 空 body | ✅ 140 links, 4660 chars |
| Cloudflare Turnstile + JS（wiki.supercombo.gg） | scrapling-stealthy-fetch: 未测试 | ✅ 6-8s 自动解析, 23,000+ chars |
| reCAPTCHA v3 评分 | 未测量 | ✅ 0.9（服务器端验证）|
| 基础 stealth 信号 | scrapling-fetch: webdriver=true, chrome=undefined | ✅ webdriver=false, chrome=object, plugins=5 |

当前管线中 `scrapling-stealthy-fetch`（Playwright + JS 注入 stealth）依赖 JS 注入的 patch 方式，检测站点可绕过且维护成本高。CloakBrowser 的源码级 patch 提供了本质更好的 stealth 能力。

Obscura-fetch 的轻量优势（8-50 MB, 1-2s 启动）与其非 stealth 定位使其保留在 rank 2。

## Goals / Non-Goals

**Goals:**
- 将 CloakBrowser 注册为 `playwright_stealth` 类型引擎，`default_rank: 4`
- 创建 `cloakbrowser-fetch-contract` spec 定义其行为契约
- 更新 `engine-registry` 和 `engine-contracts` specs
- 将 `scrapling-stealthy-fetch` 标记为 `superseded`
- 更新 `fallback-escalation` playbook 和 `AGENTS.md`
- 实现 `cloakbrowser-fetch` 引擎的可用性：用户 `pip install cloakbrowser` 后即可使用

**Non-Goals:**
- 不集成 `humanize` 模式（后续优化）
- 不集成 `cloakserve` CDP 多路复用器模式（后续优化）
- 不处理二进制自动更新（由 cloakbrowser wrapper 自身处理）
- 不处理 Linux Chromium 146 与 macOS Chromium 145 差异验证（tasks 阶段标记为注意事项）

## Decisions

### Decision 1: 引擎定位 — 替代 scrapling-stealthy-fetch 而非 obscura-fetch

CloakBrowser 定位为 `playwright_stealth` 类型引擎，替代 `scrapling-stealthy-fetch`。Obscura-fetch（`cdp_lightweight`）保留在 rank 2。

**原因**：Obsura 和 CloakBrowser 服务不同的场景：
- **Obscura**: 轻度动态页，快速轻量（8-50 MB, 1-2s），不要求 stealth
- **CloakBrowser**: 高保护页，需要 TLS 指纹绕过、Turnstile/reCAPTCHA 绕过等 stealth 能力

两者不是竞争关系而是互补。

### Decision 2: 集成方式 — pip install + Python wrapper

用户通过 `pip install cloakbrowser` 安装，chrome-agent 的 crawl/scrape 脚本中通过 `from cloakbrowser import launch` 调用。

**原因**：
- Binary 使用专有许可证，不可重新分发
- CloakBrowser wrapper 层极薄（~500 行 Python），直接调用是最低成本的集成方式
- Playwright API 兼容，现有脚本改动最小

### Decision 3: 初始状态 — draft

CloakBrowser 引擎初始注册状态为 `draft`。

**原因**：
- 仅在 macOS Chromium 145 验证，未在 Linux Chromium 146 验证
- nowsecure.nl（Turnstile + GSAP）在 headless macOS 下未通过
- 升级为 `frozen` 的前提：Linux Chromium 146 验证通过 + nowsecure.nl 或等价场景验证

### Decision 4: 调用模式 — wait_until=domcontentloaded + 等待 Turnstile 解析

对于 Turnstile 保护的页面，需使用 `wait_until='domcontentloaded'`（而非 `networkidle`）并在导航事件后重新获取页面内容。

### Decision 5: EScalation chain 位置

```
scrapling-get (rank 1)
    → obscura-fetch (rank 2)
    → scrapling-fetch (rank 3)
    → cloakbrowser-fetch (rank 4)    ← 新增
    → chrome-devtools-mcp (rank 5)
    → chrome-cdp (rank 6)
```

从 `scrapling-fetch` 升级到 `cloakbrowser-fetch` 的触发条件：
- scrapling-fetch 返回空 body 但页面非空白（TLS 检测嫌疑）
- 已知目标使用 Cloudflare Turnstile
- 已知目标需要 reCAPTCHA v3 评分
- 已知目标被 `protection_level: high` 标记

## Risks / Migration

### 风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| Binary 许可证限制 | 用户必须自行 pip install，CI/CD 需要额外步骤 | 在 tasks 中添加安装说明；Dockerfile 中增加 pip install 步骤 |
| macOS Chromium 145 | macOS 用户使用落后版本，可能在某些检测站点表现不同 | 在 contract spec 中注明平台版本差异；建议 Linux 用于生产部署 |
| 二进制大小 (~200MB) | 首次下载时间较长，CI/CD 构建时间增加 | 利用 Docker layer caching；pre-download 在构建步骤 |
| nowsecure.nl 未验证 | Turnstile + GSAP 组合在当前 macOS headless 下未通过 | 在 contract spec 中标记为已知限制；在 Linux Chromium 146 或 headed 模式下验证 |
| 上游维护风险 | CloakHQ 可能停止维护 | Binary 专有许可证意味着不能自行 fork；建议监控上游 release 并备选 scrapling-stealthy-fetch 作为 fallback |

### 迁移路径

1. **scrapling-stealthy-fetch** → `status: superseded`，保留在 registry 中供历史引用
2. 现有 site strategies 引用 `scrapling-stealthy-fetch` 的：仅在下次策略审核时更新，不做自动迁移
3. 新 site strategies：直接使用 `cloakbrowser-fetch`

### 安装前提

所有使用 CloakBrowser 的环境必须：
```bash
pip install cloakbrowser
# 首次调用自动下载 ~200MB patched Chromium binary
# 下载到 ~/.cloakbrowser/chromium-{version}/
```
