# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 **确认 spec 实现范围** ✅ 4 个 Requirements 均有任务+测试对应：passthrough→2.1/2.3/2.6；fallback→2.1；helper→2.1/2.2；injection-safety→2.1：逐条核对 `specs/fetch-strategy-selector/spec.md` 的 4 个 ADDED Requirements（`strategy-content-selector-passthrough` / `ai-targeted-fallback-when-no-selector` / `shared-arg-builder-helper` / `selector-injection-safety`），确认本 tasks 覆盖其全部场景。完成标准：每个 Requirement 至少有一个任务 + 一个测试场景对应。
- [x] 1.2 **审计 crawl 路径 per-URL 策略解析** ✅ 结论：`convertTraversalToMarkdown`(L1325) 无 strategy 参数；per-URL page 解析在 `fetcherFn` 内（L2708/2731/4352）。决策：将 `strategy` 注入 opts，循环内按 URL 解析 args。scrape 调用点(L3012/3032)不传 strategy → 自动 ai-targeted 回退（scrape 出范围，行为不变）（对应 design D4 风险缓解）：确认 `runCrawlScrapling` 提取循环（`chrome-agent-cli.mjs:1353`/`:1367` 附近）是否已对每个 URL 解析 `strategy` + `matchingPage`。完成标准：产出审计结论（"已解析"则直接复用；"未解析"则该 URL 走 `--ai-targeted` 回退，不引入新解析逻辑）。验证：`grep -nE 'findStrategy|findMatchingPage' scripts/chrome-agent-cli.mjs` 定位 crawl 调用点。
- [x] 1.3 **确认前置约定** ✅ node v24 + `node:test`；测试落 `tests/fetch-strategy-selector.test.mjs`；site 回归 `python3 scripts/test_runner.py site-samples --domain posthog.com`：阅读 `docs/architecture/08-tech-stack.md` §2（Node.js 纯 ESM / C2 / C8 函数声明风格）与 §4（测试约定：Node.js 用 `node:test` + `node:assert/strict`，运行 `node --test tests/<file>`；Python 站点回归用 `python3 scripts/test_runner.py site-samples --domain <domain>`）。完成标准：明确测试落地位置（`tests/fetch-strategy-selector.test.mjs`）与运行命令。

## 2. 核心实现任务

### Slice A — `buildScraplingExtractionArgs` helper（对应 Requirement: shared-arg-builder-helper）

> **实现位置决策**（refine design D1）：提取为可 import 模块 `scripts/lib/scrapling-extraction-args.mjs`，而非内联于单体内 `chrome-agent-cli.mjs`。理由：TDD vertical slice 要求纯函数运行时单测，而 monolithic CLI 无 `export` 不支持直接 import 纯函数（现有 `.test.mjs` 只能做源码文本断言）。提取为小模块既满足 TDD 又改善模块化。design D1 的"函数签名与三分支逻辑"不变，仅位置从内联改为 importable module。遵循 C2（纯 ESM `.mjs`）与 C8（`function` 声明）。

- [x] 2.1 **RED — 编写 helper 单元测试** `tests/fetch-strategy-selector.test.mjs`（`node:test` + `node:assert/strict`）。覆盖三个分支：
  - 策略有非空 `extraction.selectors.content` + scrapling-family fetcher → 返回 `["-s", selector]`（对应 `strategy-content-selector-passthrough`）
  - 策略无/空 `content` 选择器 → 返回 `["--ai-targeted"]`（对应 `ai-targeted-fallback-when-no-selector`）
  - fetcher 为 `mediawiki-api` → 返回 `[strategy.path]`（对应 `shared-arg-builder-helper` 的 mediawiki-api 场景）
  - 额外：selector 含特殊字符（`div[class*='@container/reader-content']`）仍作为**单一数组元素**返回（对应 `selector-injection-safety`：断言返回数组中 selector 是独立元素，未与 `-s` 拼接）
  - 验证方式：`node --test tests/fetch-strategy-selector.test.mjs` → 此时**应失败**（模块尚未创建）。
- [x] 2.2 **GREEN — 实现 helper 模块** `scripts/lib/scrapling-extraction-args.mjs`：
  - `export function buildScraplingExtractionArgs(strategy, matchingPage)`，内含 design D1 的三分支逻辑（mediawiki-api → `[strategy.path]`；有非空 content 选择器 → `["-s", selector]`；否则 → `["--ai-targeted"]`）。
  - 内部调用既有 `selectFetcher` 逻辑判定 fetcher；为避免循环依赖，`selectFetcher` 若在 CLI 内联则将 fetcher 作为第三入参传入（任务 2.3/2.7 调用处提供）——以实现时实际位置为准，二选一：helper 接 `(strategy, matchingPage, fetcher)` 三参，或 helper import selectFetcher。**决策原则**：不重复实现 fetcher 选择逻辑。
  - 文件顶部注释标注 `selector-injection-safety` 依赖（"selector MUST remain an array element, never shell-joined; safety relies on spawnSync argv array"）。
  - 验证方式：`node --test tests/fetch-strategy-selector.test.mjs` → **全部通过**。

### Slice B — `runFetch()` 接入（对应 Requirement: strategy-content-selector-passthrough · fetch 场景）

- [x] 2.3 **RED — 扩展测试**：在 `tests/fetch-strategy-selector.test.mjs` 增加"runFetch 调用 helper"的结构断言（沿用 `crawl-scrapling-pages-scope.test.mjs` 的源码文本断言模式）：断言 `chrome-agent-cli.mjs` 中 `runFetch` 不再硬编码 `["--ai-targeted"]`，而是调用 `buildScraplingExtractionArgs(strategy, matchingPage[, fetcher])`。验证：`node --test` → 应失败。
- [x] 2.4 **GREEN — 接入 runFetch**：修改 `scripts/chrome-agent-cli.mjs` `runFetch()`（`:1914`）：
  - 顶部 `import { buildScraplingExtractionArgs } from "./lib/scrapling-extraction-args.mjs";`
  - 将 `const fetchExtraArgs = fetcher === "mediawiki-api" ? [strategy.path] : ["--ai-targeted"];` 替换为 `const fetchExtraArgs = buildScraplingExtractionArgs(strategy, matchingPage, fetcher);`
  - 验证：`node --test tests/fetch-strategy-selector.test.mjs` 通过 + 手动 `chrome-agent doctor` 不报错。

### Slice C — crawl 提取循环接入（对应 Requirement: strategy-content-selector-passthrough · crawl 场景）

- [x] 2.5 **crawl per-URL 解析落地**（依据 1.2 审计结论）：若 crawl 循环已解析 per-URL strategy/page，直接复用；若未解析，在 `:1353`/`:1367` 调用前解析该 URL 的 strategy/matchingPage（缺失则传 `null,null` 触发 `--ai-targeted` 回退）。完成标准：两个调用点都能拿到 per-URL 的 strategy/page（或合法 null）。
- [x] 2.6 **RED — 扩展测试**：源码文本断言 crawl 提取循环的 `:1353` 与 `:1367` 两处均调用 `buildScraplingExtractionArgs(...)` 而非字面量 `["--ai-targeted"]`。验证：`node --test` → 应失败。
- [x] 2.7 **GREEN — 接入 crawl**：将 crawl 两处 `runEngineFetch(..., ["--ai-targeted"])` 改为先 `const crawlArgs = buildScraplingExtractionArgs(strategy, matchingPage, fetcher);` 再传入 `runEngineFetch(..., crawlArgs)`。验证：`node --test` 通过。

### Slice D — cloakbrowser `-s` 兼容性确认（对应 design D6）

- [x] 2.8 **cloakbrowser `-s` 验证与决策记录**：执行 `/Users/nantas-agent/.cache/chrome-agent-obscura/bin/obscura`（或 cloakbrowser CLI）`extract --help` 确认是否支持 `-s/--css-selector`。
  - 若支持：helper 自然覆盖 cloakbrowser（无需改 helper），更新 design D6 决策为"cloakbrowser 已启用"。
  - 若不支持：保持 helper 对 cloakbrowser 返回 `["--ai-targeted"]`（现状），在 spec 的"非目标"补充"cloakbrowser `-s` 支持为后续 change"。
  - 验证方式：记录 CLI help 输出片段作为决策证据；无需新增测试（spec 已将 cloakbrowser 列为范围外）。

## 3. 收敛与验证准备

- [x] 3.1 **PostHog 站点样本回归**（对应 C9 测试义务 + KI-1 验证）：运行 `python3 scripts/test_runner.py site-samples --domain posthog.com`，确认 5 个样本（含已修复选择器 `div[class*='@container/reader-content']`）回归通过。完成标准：所有样本 pass；fetch 现在原生消费策略选择器（无需手动 scrapling `-s`）。
- [x] 3.2 **全量测试套件**：运行 `python3 scripts/test_runner.py all`（unit + site-samples）+ `node --test tests/fetch-strategy-selector.test.mjs tests/crawl-scrapling-pages-scope.test.mjs tests/chrome-agent-runtime.test.mjs`。完成标准：全绿，无回归。
- [x] 3.3 **标记 writeback 摘要与状态变更**（供 writeback 阶段收敛，不在本阶段执行）：整理三处回写内容草稿——(a) `sites/strategies/posthog.com/strategy.md` KI-1 `open` → `resolved` + commit 引用；(b) `docs/architecture/04-cli-reference.md` fetch 行为补充选择器透传/回退；(c) `docs/architecture/06-engine-selection.md` scrapling-get 提取阶段补充选择器优先。完成标准：草稿条目就绪，待 verification 通过后在 §4 执行。

## 4. 验证与回写收敛

> 本节任务在 `verification.md` / `writeback.md` artifacts 生成阶段执行，此处作为收敛入口记录。

- [x] 4.1 **生成 verification.md**：基于真实实现结果，覆盖 spec-to-implementation（4 个 Requirement → 实现/测试证据）与 task-to-evidence（§2 各 slice → 测试输出）。引用 §3.1/§3.2 的测试证据。
- [x] 4.2 **生成 writeback.md**：基于 verification.md 结论，定义三处回写目标（KI-1 状态 + 两份 architecture 文档）的字段映射、前置条件与执行人。
- [x] 4.3 **执行 writeback**：按 writeback.md 执行三处回写，记录可审计证据（文件路径、diff 摘要、执行时间、结果）。完成后 KI-1 在 strategy.md 标记 `resolved`。
