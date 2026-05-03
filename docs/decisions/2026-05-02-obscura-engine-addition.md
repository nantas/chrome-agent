# 2026-05-02 Obscura Engine Addition

## Context

chrome-agent 当前引擎管线在 `scrapling-get`（纯 HTTP）和 `scrapling-fetch`（Playwright）之间存在明显的效率断层：

- `scrapling-get` 极快（~1s）但无法处理 JS 渲染页面
- `scrapling-fetch` 功能完整但需要启动完整 Chromium（~200MB 内存，4-8s 启动+加载）
- 大量「需要 JS 渲染但不需要完整浏览器功能」的中间场景（动态列表、搜索页、轻度 SPA）缺乏适合的引擎

端到端对比测试（2026-05-02）表明，Obscura（`h4ckf0r0day/obscura`，Rust+V8 轻量级 headless 浏览器）在动态页面场景的表现显著优于现有选项：

- 加载速度比 Scrapling fetch 快 2-3.5x（HN: 1.38s vs 4.79s）
- 空闲 RSS ~8MB，峰值 ~50MB，远低于 Playwright 的 200MB+
- 内置 TLS 指纹伪装、3,520+ tracker 拦截、robots.txt 合规
- CDP 协议兼容 Puppeteer/Playwright 基本连接

## Decision

将 Obscura 作为 `cdp_lightweight` 类型引擎正式接入 chrome-agent，具体决策如下：

1. **引擎类型命名**: `cdp_lightweight` — 与现有 `cdp_managed`、`cdp_live` 形成一致命名体系，描述「通过 CDP 通信、比完整 Chrome 显著更轻」的属性，不绑定具体实现语言。
2. **注册位置**: 在 `configs/engine-registry.json` 中新增 `obscura-fetch` 条目，`default_rank: 2`，位于 `scrapling-get`（1）之后、`scrapling-fetch`（3）之前。
3. **初始状态**: `draft` — 完成 smoke-check 和策略集成验证后才可转为 `frozen`。
4. **二进制获取策略**: 优先使用 GitHub Releases 预编译二进制（macOS ARM64 / Linux x86_64），fallback 到源码编译（`cargo build --release --features stealth`）。
5. **Stealth 模式边界**: `--stealth` 不在默认 escalation chain 中自动启用；需要 stealth 的页面仍由 `scrapling-stealthy-fetch`（完整 Playwright stealth）处理。
6. **CDP 长连接模式**: 本 change 仅集成 CLI `fetch` 单次执行模式，`obscura serve` 长连接 CDP server 模式保留为后续 change。

## Consequences

### 正面影响

- 动态页面抓取效率提升 2-3.5x，内存占用降低 10x+
- 新增内置能力：robots.txt 合规、CDP native 的 DOM→Markdown 转换
- 扩展引擎类型体系，为后续类似轻量引擎接入提供 precedent

### 风险

- **Obscura v0.1.0 稳定性**：上游仍在早期版本。缓解：状态设为 `draft`，进程隔离降低影响面。
- **CDP 实现子集**：特定 Playwright/Puppeteer API 可能不兼容。缓解：不暴露 CDP server 模式。
- **预编译二进制平台覆盖**：当前仅 macOS ARM64 和 Linux x86_64。缓解：明确列出自定义构建步骤。
- **上游仓库可靠性**：GitHub release URL 可能变更。缓解：fallback 到源码编译；后续考虑 vendor binary。

### 迁移

- `configs/engine-registry.json` 中现有引擎 `default_rank` 后移：
  - `scrapling-fetch`: 2 → 3
  - `scrapling-bulk-fetch`: 3 → 4
  - `scrapling-stealthy-fetch`: 3 → 4
  - `chrome-devtools-mcp`: 4 → 5
  - `chrome-cdp`: 5 → 6
- `engine-contracts/spec.md` 中 escalation chain 和错误矩阵追加 `obscura-fetch`
- 无破坏性变更，所有现有功能保持不变
