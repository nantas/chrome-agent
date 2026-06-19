# Proposal

## 问题定义

`chrome-agent fetch` 的内容提取阶段**忽略策略的 `extraction.selectors.content` 字段**，硬编码使用 scrapling 的 `--ai-targeted` 启发式模式。

- **缺陷位置**：`scripts/chrome-agent-cli.mjs:1914`
  ```js
  const fetchExtraArgs = fetcher === "mediawiki-api" ? [strategy.path] : ["--ai-targeted"];
  ```
- **现象**：当目标站点改版导致 `--ai-targeted` 启发式失效（误提取导航栏而非正文）时，即使策略已正确声明 `extraction.selectors.content`，fetch 仍产出空/垃圾内容。
- **证据**：PostHog 文档站点（`sites/strategies/posthog.com/strategy.md` KI-1）。PostHog 改版移除 `<article>` 包装后，`--ai-targeted` 仅抓到 397B 导航栏；而策略声明的选择器 `div[class*='@container/reader-content']` 经验证能完整提取 h1 + 正文（5 个样本 S1-S12 质量检测 98.3% 通过）。
- **治理影响**：`extraction.selectors` 与 `extraction.mode` 成为 **dead config**——策略与 pipeline 之间形成 Architecture Gate 违规（Strategy→Pipeline 无消费者，Pipeline→Strategy 无 sourcing）。

## 范围边界

**In Scope（v1）**

- `fetch` 内容获取命令（`runFetch()`，`chrome-agent-cli.mjs:1914`）的 scrapling 调用：当匹配策略声明 `extraction.selectors.content` 时，优先通过 scrapling `-s <selector>` 传递；未声明时回退 `--ai-targeted`。
- `crawl` 提取路径（`chrome-agent-cli.mjs:1353` 预取 HTML 转换 + `:1367` 每页 scrapling 调用）同步应用相同的选择器透传与回退逻辑。
- 修复触发站点 PostHog 的 KI-1 状态（`open` → `resolved`）并回写 architecture 文档。
- 回归测试覆盖：策略有选择器 / 策略无选择器 / 选择器失效三种情形，并区分 fetch 与 crawl 两条路径。

**Out of Scope（v1，列为后续 follow-up）**

- `scrape`、`explore` 路径的同类硬编码 `--ai-targeted` 调用点（`chrome-agent-cli.mjs:2669/3450`）。它们共享相同缺陷模式，但本 change 不一并修复——通过引入共享 helper（见 design）为后续逐路径启用奠定基础，避免一次性大范围行为变更带来回归风险。
- `extraction.selectors.title` 与 `cleanup` 字段的消费（本 change 仅消费 `content` 选择器，保持最小改动面）。
- `mediawiki-api` fetcher 路径（已独立走 strategy.path 传递，不在本次 selector 透传逻辑内）。

## Capabilities

### New Capabilities

- `fetch-strategy-selector`: 内容获取后端（`fetch` 命令的 `runFetch()` 与 `crawl` 命令的提取循环）在调用 scrapling-get 提取时，SHALL 优先使用匹配策略的 `extraction.selectors.content` 选择器（经 scrapling `-s` 传递），并在策略未声明选择器或选择器提取失败时回退至 `--ai-targeted` 启发式。

### Modified Capabilities

- _无。本 change 新增独立 capability；`extraction.selectors` 字段语义由 `docs/architecture/03-strategy-schema.md` 定义，本 change 不修改字段定义，仅新增 pipeline 对该字段的消费行为。_

## Capabilities 待确认项

- [x] 能力清单已确认：单一新增 capability `fetch-strategy-selector`，范围覆盖 `fetch` 命令（`runFetch()`）与 `crawl` 命令提取循环（用户确认扩展至 crawl）。
- [x] 共享 helper 复用边界已定夺：本次同时修复 fetch 与 crawl，通过共享 helper（见 design）统一构造 selector→extraArgs，避免重复缺陷。`scrape`/`explore` 路径留作后续 follow-up。

## Impact

- **代码**：`scripts/chrome-agent-cli.mjs` `runFetch()`（:1914）、crawl 提取循环（:1353/:1367）及新增 selector→extraArgs 共享构造 helper；预计 < 80 行净增。
- **行为**：所有声明 `extraction.selectors.content` 的站点策略在 `fetch` 时改用精确选择器提取；未声明选择器的站点行为不变（仍 `--ai-targeted`）。向后兼容。
- **策略库**：现有策略若已声明选择器（如 PostHog）将立即受益；其余策略行为无变化。
- **文档**：`docs/architecture/04-cli-reference.md`（fetch 行为说明）、`docs/architecture/06-engine-selection.md`（scrapling-get 提取阶段）需补充选择器透传与回退说明。
- **测试**：新增 `tests/` 单元测试（selector→extraArgs 构造逻辑）+ 站点样本回归（PostHog 5 样本）。

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：`repo://orbitos` → `99_系统/Harness/OpenSpec_Schema_Source`（`orbitos-change-v1`）
  - 项目页：`docs/architecture/04-cli-reference.md`、`docs/architecture/06-engine-selection.md`、`docs/architecture/03-strategy-schema.md`
  - 回写目标：`sites/strategies/posthog.com/strategy.md`（KI-1 状态）、`docs/architecture/04-cli-reference.md`、`docs/architecture/06-engine-selection.md`
