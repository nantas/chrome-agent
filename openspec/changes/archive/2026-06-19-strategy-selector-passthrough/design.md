# Design

## Context

本 change 为 `specs/fetch-strategy-selector/spec.md` 中的 4 个 ADDED Requirements 提供实现决策。触发场景是 PostHog 文档站点的 KI-1：`chrome-agent fetch` 在 `scripts/chrome-agent-cli.mjs:1914` 硬编码 `["--ai-targeted"]`，忽略策略 `extraction.selectors.content`，导致站点改版后提取失效。

经用户确认，范围覆盖 `fetch`（`runFetch()`）与 `crawl`（提取循环 `:1353`/`:1367`）两条路径，两者共享同一缺陷模式。本设计通过引入共享 helper 一次性消除该模式。

**实现前已核实的现有架构事实**（不可臆造，作为设计约束）：

1. `runScraplingFetch(repoRoot, fetcher, targetUrl, outputPath, extraArgs)` 用 `spawnSync(cliPath, args, ...)` 调用，其中 `args = ["extract", fetcher, targetUrl, outputPath, ...extraArgs]` 是**数组**。→ 选择器作为独立 argv 元素传递，**天然满足 `selector-injection-safety` requirement**，无需任何转义或 shell 处理。
2. `findStrategy()` 返回 `{ registry, strategy: { ...meta, path, document } }`，`document` 是已解析的 frontmatter。→ content 选择器访问路径为 `strategy?.document?.extraction?.selectors?.content`。
3. `selectFetcher(strategy, page)` 已封装 fetcher 决策（返回 `"get"` / `"fetch"` / `"stealthy-fetch"` / `"cloakbrowser"` / `"mediawiki-api"`），fetch/crawl 调用方已持有其返回值。
4. `mediawiki-api` fetcher 走独立路径 `runMediawikiApiFetch`，已通过 `extraArgs=[strategy.path]` 传参，不在本次 selector 逻辑内。

## Goals / Non-Goals

**Goals:**

- 让 `fetch` 与 `crawl` 在 scrapling-family fetcher（`get`/`fetch`/`stealthy-fetch`）下消费策略 `extraction.selectors.content`，经 `-s` 传递。
- 提供**单一** helper 统一构造 extraArgs，消除 fetch 与 crawl 的重复缺陷。
- 保持无选择器场景的 `--ai-targeted` 回退（向后兼容）。
- 满足 `selector-injection-safety`（利用现有 spawnSync argv 数组机制，零额外转义代码）。

**Non-Goals:**

- 不修复 `scrape`/`explore` 路径（`:2669`/`:3450`）——留作后续 change。helper 的引入使其可低成本启用，但本 change 不改这两处。
- 不消费 `extraction.selectors.title` 与 `cleanup` 字段。
- 不引入提取质量驱动的动态回退（字节数阈值等）。回退是"无选择器"的确定性触发。
- 不在运行时校验选择器语法/命中率（由 explore + 样本质量检测负责）。
- 不为 `cloakbrowser` fetcher 单独适配 `-s`（见 D6）。

## Decisions

### D1: 共享 helper `buildScraplingExtractionArgs(strategy, fetcher)`

**实现位置与签名（refine 自初稿，见 tasks.md 2.2）**：提取为可 import 模块 `scripts/lib/scrapling-extraction-args.mjs`（而非内联于单体内 `chrome-agent-cli.mjs`）。理由：TDD vertical slice 要求纯函数运行时单测，而 monolithic CLI 无 `export` 不支持直接 import 纯函数（现有 `.test.mjs` 只能做源码文本断言）。提取为小模块既满足 TDD 又改善模块化。

**签名决策（与初稿的偏差，已采纳）**：初稿拟 `buildScraplingExtractionArgs(strategy, matchingPage)` 并在 helper 内部调用 `selectFetcher(strategy, matchingPage)`。实际实现改为 `buildScraplingExtractionArgs(strategy, fetcher)`——调用方传入已解析的 `fetcher`。理由：`runFetch()` / crawl 调用方本就持有 `fetcher`（由 `selectFetcher` 先解析），让 helper 接收 fetcher 既避免重复调用 `selectFetcher`，又避免 helper 对 `selectFetcher` 的依赖（`selectFetcher` 内联于 CLI，无法被独立模块 import 而不引入循环依赖）。`fetcher` 作为纯字符串入参使 helper 保持可测且无外部耦合。

```
function buildScraplingExtractionArgs(strategy, fetcher) {
  // mediawiki-api 路径：保持既有 strategy.path 传递
  if (fetcher === "mediawiki-api") {
    return strategy ? [strategy.path] : [];
  }
  // cloakbrowser 路径：cloakbrowser_fetcher.py 不接受任何 extraction flag
  // (返回 [] 修复 pre-existing bug，见 D6)
  if (fetcher === "cloakbrowser") {
    return [];
  }
  // scrapling-family 路径：优先策略 content 选择器，否则回退 ai-targeted
  const selector = strategy?.document?.extraction?.selectors?.content;
  if (typeof selector === "string" && selector.trim() !== "") {
    return ["-s", selector];
  }
  return ["--ai-targeted"];
}
```

满足 `shared-arg-builder-helper` requirement。`fetch` 与 `crawl` 调用方均调用此函数，禁止各自重新实现选择器判断。调用方负责先用 `selectFetcher(strategy, page)` 解析 fetcher，再传入 helper。

### D2: 选择器真源 = `extraction.selectors.content`

满足 `strategy-content-selector-passthrough`。读取路径 `strategy.document.extraction.selectors.content`，判空规则：仅当为非空字符串时启用 `-s`。缺失、null、空串、纯空白均触发 `--ai-targeted` 回退。

**不做**字段别名兼容（如历史可能的 `selectors.body`）——经检索当前策略库无此别名，YAGNI。

### D3: argv 安全性 = 复用现有 spawnSync 机制（零额外代码）

满足 `selector-injection-safety`。选择器字符串作为 `extraArgs` 数组的元素（`["-s", selector]`），经 `runScraplingFetch` 的 `...extraArgs` 展开后成为 `args` 数组的两个独立元素，最终传入 `spawnSync(cliPath, args)`。整个过程不经 shell 字符串拼接。

**决策**：不为 argv 安全新增任何转义/校验代码——现有架构已满足。在 helper 上方加注释说明此安全性依赖（"selector MUST stay an array element, never shell-joined"），防止未来重构退化为字符串拼接。

### D4: 调用点改造

| 调用点 | 当前代码 | 改造后 |
|--------|---------|--------|
| `runFetch()` `:1914` | `const fetchExtraArgs = fetcher === "mediawiki-api" ? [strategy.path] : ["--ai-targeted"];` | `const fetchExtraArgs = buildScraplingExtractionArgs(strategy, fetcher);` |
| crawl 每页提取 `:1367` | `runEngineFetch(repoRoot, fetcher, url, mdPath, ["--ai-targeted"]);` | 提取 `const args = buildScraplingExtractionArgs(strategy, fetcher);` 后传入（fetcher 由 per-URL `fetcherFn` 解析） |
| crawl 预取 HTML `file://` `:1353` | `runEngineFetch(repoRoot, "get", \`file://${tmpHtmlPath}\`, mdPath, ["--ai-targeted"]);` | 同上，用 `buildScraplingExtractionArgs(...)` |

crawl 路径需注意：循环内每页可能匹配不同策略/页面，helper 应在循环内对每个 URL 解析其 `strategy` + `matchingPage` 后调用（crawl 主流程已持有 per-URL 的 strategy/page 解析能力，复用之）。若 crawl 某些代码路径当前未做 per-URL 策略解析，则该 URL 回退 `--ai-targeted`（保持现有行为），不强制引入新解析。

### D5: 确定性回退，无质量驱动切换

满足 `ai-targeted-fallback-when-no-selector`。回退**仅**由"无 content 选择器"触发。即使 `-s` 提取结果为空或字节数低，也不自动二次尝试 `--ai-targeted`。

**理由**：质量驱动回退会引入隐藏的二次网络请求、不一致的双结果语义、以及难以复现的提取行为。选择器质量由 explore + 样本质量检测（如本次 PostHog 的 S1-S12）在策略维护阶段保证，而非运行时猜测。

### D6: cloakbrowser fetcher 返回 `[]`（修复 pre-existing bug）

`selectFetcher` 在高防护场景返回 `"cloakbrowser"`（走 `runCloakbrowserFetch`）。**任务阶段验证结论（task 2.8）**：`scripts/cloakbrowser_fetcher.py` 的 argparse 既不接受 `-s` 也**不接受 `--ai-targeted`**。这意味着 pre-change 代码对 cloakbrowser 硬编码 `"--ai-targeted"` 本身是一个 **pre-existing bug**——任何 `protection_level: high` 策略（如 `boardgamegeek.com`、`wiki.supercombo.gg`）的 fetch 都会因 `unrecognized arguments: --ai-targeted` 失败。本 change 决策：

- helper 对 cloakbrowser 路径**返回 `[]`**（而非 `"--ai-targeted"`），修复 pre-existing bug——`cloakbrowser_fetcher.py` 有自己的 fetch 逻辑，不需要任何 extraction flag。
- cloakbrowser 的 `-s` 选择器透传仍未启用（fetcher 独立，且 selector 在其 fetcher 内无对应解析）；留作后续 change。这不违反 spec：cloakbrowser 非 `scrapling-get` fetcher，spec requirement 明确限定 scrapling-get family。
- 经 reviewer 独立验证（`/opsx-verify`）确认此为真实影响而非纯潜在问题，已采纳。

## Risks / Migration

### Risks

| 风险 | 等级 | 缓解 |
|------|------|------|
| crawl 路径 per-URL 策略解析缺失或与 fetch 路径不一致 | 中 | 任务阶段先审计 crawl 循环是否已解析 per-URL strategy/page；缺失则该 URL 保持 `--ai-targeted` 回退，不破坏现状 |
| 现有策略 `extraction.selectors.content` 含已失效选择器 → 修复后反而比 `--ai-targeted` 更差 | 低 | 回归测试覆盖；失效选择器属策略维护问题，由 explore/质量检测发现并修策略（如 PostHog 本次已修）。修复前 PostHog 用 `ai-targeted` 也是 397B 垃圾，不会更差 |
| cloakbrowser 站点期望选择器透传但未启用 | 低 | D6 决策明确：cloakbrowser 返回 `[]` 修复 pre-existing unrecognized-arg bug；选择器透传留作后续 change。高防护站点（boardgamegeek/supercombo）现可正确 fetch（无 unrecognized arg） |
| 选择器含特殊字符（`[`、`*`、`@`、`'`）导致 scrapling 解析失败 | 极低 | D3 argv 安全已保证无注入；scrapling CSS 解析对合法选择器字符正常。PostHog 的 `div[class*='@container/reader-content']` 已实测通过 |

### Migration

- **向后兼容**：无 `extraction.selectors.content` 的策略行为零变化（仍 `--ai-targeted`）。
- **现有受益策略**：PostHog（本次已修选择器）修复后 fetch/crawl 立即产出正确内容。
- **无需数据迁移**：纯代码 + 文档变更，无缓存/输出格式变化。
- **文档回写**（writeback 阶段）：
  - `sites/strategies/posthog.com/strategy.md` KI-1 `open` → `resolved`，附 commit 引用。
  - `docs/architecture/04-cli-reference.md` fetch 行为说明补充选择器透传与回退。
  - `docs/architecture/06-engine-selection.md` scrapling-get 提取阶段补充"优先策略选择器，缺失回退 ai-targeted"。
- **测试落地**（遵循 C9 测试义务）：新增 `tests/` 单元测试覆盖 helper 的三个分支（有选择器 / 无选择器 / mediawiki-api）；运行 `python3 scripts/test_runner.py site-samples --domain posthog.com` 确认 PostHog 样本回归通过。
