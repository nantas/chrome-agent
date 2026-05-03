# Design

## Context

chrome-agent 当前引擎管线在 `scrapling-get`（纯 HTTP）和 `scrapling-fetch`（Playwright）之间存在效率断层。Obscura 是一个 Rust+V8 的轻量级 headless 浏览器，端到端测试证明其可将动态页面抓取速度提升 2-3.5x，内存降低 10x+。本 design 定义如何将 Obscura 作为正式引擎接入，遵循 `extension-api` spec 的 artifact checklist。

## Goals / Non-Goals

**Goals:**

- 在 `configs/engine-registry.json` 中注册 `obscura-fetch` 引擎条目（type: `cdp_lightweight`，status: `draft`）
- 在 Scrapling CLI preflight playbook 中新增 Obscura 二进制检测与安装逻辑
- 在引擎选择 escalation chain 中插入 `obscura-fetch` 作为 `scrapling-get → scrapling-fetch` 之间的中间层
- 更新 `engine-contracts` 错误矩阵和 smoke-check 清单
- 建立 `docs/playbooks/obscura-cli-preflight.md` 操作手册
- 产出决策记录 `docs/decisions/2026-05-02-obscura-engine-addition.md`

**Non-Goals:**

- 不实现 `obscura scrape` 并行模式的 CLI 集成（需额外 worker binary）
- 不在本 change 中修改任何站点策略的 `engine_preference` 或反爬策略的 `engine_priority`
- 不替换任何现有引擎
- 不实现 Obscura CDP server 的常驻 daemon 模式
- 不修改全局 `chrome-agent` workflow skill 的路由逻辑（使用默认 escalation chain 即可覆盖）

## Decisions

### Decision 1: 引擎类型命名 — `cdp_lightweight`

选择 `cdp_lightweight` 作为新引擎类型名，而非备选 `headless_rust` 或 `v8_browser`。

**理由**：`cdp_lightweight` 准确描述了三个核心属性：(1) 通过 CDP 协议通信，(2) 比完整 CDP 引擎（Chrome）显著更轻，(3) 不绑定特定实现语言（未来可能有其他语言的轻量 CDP 引擎）。

**备选排除**：`headless_rust` 过于绑定实现语言；`v8_browser` 过于绑定 JS 引擎。`cdp_lightweight` 在 registry type 枚举中与现有 `cdp_managed`、`cdp_live` 形成一致的命名体系。

### Decision 2: Obscura 二进制获取策略 — 预编译优先

优先使用 GitHub Releases 预编译二进制，fallback 到源码编译。

**安装路径**：`$HOME/.cache/chrome-agent-obscura/bin/obscura`

**安装逻辑**：
1. 检查 `OBSURA_CLI_PATH` 环境变量，若已设置且可执行则直接使用
2. 检查默认受管路径 `$HOME/.cache/chrome-agent-obscura/bin/obscura`
3. 若缺失，自动下载对应平台的预编译 release（macOS ARM64 / Linux x86_64）
4. 若下载失败（如平台不支持），提示用户从源码构建（`cargo build --release --features stealth`）

**版本固定**：首次下载后锁定版本，通过 `obscura --help` 输出校验二进制完整性。版本更新需通过独立的 openspec change。

### Decision 3: Preflight 集成 — 扩展 Scrapling CLI preflight

将 Obscura 二进制检测追加到现有 Scrapling CLI preflight playbook 的相邻位置。

**不修改 Scrapling preflight 本身**：Scrapling 和 Obscura 是两个独立工具，各自有独立的安装保障逻辑。但 preflight 检查顺序可以合并为「先检查 Scrapling，再检查 Obscura」。

**新文件**：`docs/playbooks/obscura-cli-preflight.md`

### Decision 4: Escalation chain 中的位置

`obscura-fetch` 排在 `scrapling-get` 之后、`scrapling-fetch` 之前。

**理由**：
- `scrapling-get` rank 1：纯 HTTP 最快，静态页面无异议
- `obscura-fetch` rank 2：JS 渲染能力，但轻量级（~8MB 内存，1-3s）
- `scrapling-fetch` rank 3：完整浏览器，重但全面（200MB+ 内存，4-8s）
- 后续引擎 ranks 向后顺移

这形成了合理的效率递减 · 能力递增的 escalation 梯度。

### Decision 5: Stealth 模式边界

Obscura 的 `--stealth` 不在默认 escalation chain 中自动启用。

**理由**：Obscura stealth 是 TLS 指纹层伪装（wreq Chrome 145），不是完整浏览器指纹对抗。对需要 stealth 的页面，仍由 `scrapling-stealthy-fetch`（rank 4，完整 Playwright stealth）处理。Obscura stealth 保持为可选参数，由 anti-crawl strategy 的 `engine_priority` 显式触发时才使用。

### Decision 6: 暂不集成 CDP 长连接模式

本 change 仅集成 Obscura 的 CLI `fetch` 命令（单次执行模式），不实现 `obscura serve` 的长连接 CDP server 模式。

**理由**：CDP 长连接模式需要管理进程生命周期、端口分配、连接池等，复杂度显著高于单次 CLI 调用。保留为后续 change 的范围。

## Risks / Migration

### Risks

1. **Obscura v0.1.0 稳定性**：上游仍在早期版本，可能有未发现的 bug。但我们的用法是 CLI 单次调用模式，进程隔离降低了影响面。
   - **缓解**：engine status 设为 `draft`，不自动用于关键路径；需 smoke-check 通过后才考虑 `frozen`。

2. **CDP 实现子集**：特定 Playwright/Puppeteer API 可能不兼容。但在 CLI 模式下不依赖 CDP 交互，影响限于诊断场景。
   - **缓解**：不在此 change 中暴露 CDP server 模式。

3. **预编译二进制平台覆盖**：当前仅 macOS ARM64 和 Linux x86_64 有预编译 release。其他平台需源码编译。
   - **缓解**：install playbook 明确列出自定义构建步骤。

4. **上游仓库可靠性**：GitHub release URL 可能变更或仓库被删除。
   - **缓解**：安装逻辑 fallback 到源码编译；后续考虑 vendor binary 到内部存储。

### Migration

- 无需数据迁移
- `configs/engine-registry.json` 中现有引擎的 `default_rank` 需更新：`scrapling-fetch` 2→3，`scrapling-bulk-fetch` 3→4，`scrapling-stealthy-fetch` 3→4，`chrome-devtools-mcp` 4→5，`chrome-cdp` 5→6
- `engine-contracts/spec.md` 中 escalation chain 和错误矩阵需追加 `obscura-fetch` 行/列
- 无破坏性变更，所有现有功能保持不变
