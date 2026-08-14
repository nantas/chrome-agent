# Design

## Context

`crawlApi` bundle（`cli.mjs:2129-2141`）是 28-entry 扁平 grab-bag：26 命名函数 + `fs` + `log`。C4 修复（commit `c51e771`）补上了 `api.` 前缀纪律 + 静态纪律测试，但 bundle **形状**仍是问题——6-7 个关注点（engine fetch / scrapling cache / obscura pool / traversal / convert / report / handoff）被压成无结构对象，reader 持有不了心智模型，且扁平结构是 C4 bare-call bug 的结构性温床。

再审查报告建议「缩到 ~4 真协作方」，但**该目标天真**：bundle 里大多数 helper 跨 cli.mjs 共享（见 §"不可移动 shared helper" 盘点），移入 seam 模块会循环 import 或复制。本 change 的真实目标 = **重塑 bundle 形状为 named concern objects**，不改 deps 注入机制、不移动 shared helper。

规范真源：`specs/fetch/spec.md` 的 MODIFIED `crawl-scrapling-orchestrator-is-a-seam-module`——保留 C4 调用纪律 + 新增 seam surface 形状契约 + 新 scenario `seam-surface-uses-named-concern-groups`。

## Goals / Non-Goals

**Goals:**
- 把 `crawlApi` 从 flat 29-key 重塑为 9 个 named concern objects（fs / log / report / handoff / engine / cache / pool / traversal / convert）
- `crawl_scrapling.mjs` 全部 ~40 调用点从 `api.<helper>` → `api.<group>.<helper>`
- 静态纪律测试升级：既测 bare call（C4 保留）又测 flat `api.<helper>` 残留（新增）
- spec delta 声明 seam surface 形状契约

**Non-Goals:**
- 不移动任何 shared helper（会循环 import）——`pagePatternMatches`/`selectFetcher`/`buildScraplingExtractionArgs`/`convertTraversalToMarkdown`/`collectMarkdownArtifacts`/`collectLinksFromHtml`/`urlToStructuredPath`/`scraplingSlugFromUrl` 留在 cli.mjs
- 不改 deps 注入机制（仍手传 `api` 对象，不引入 DI 框架）
- 不抽 cli.mjs 其余大 handler（另立 change）
- 不改 crawl 控制流/产出

## Decisions

**D1 — 分组方案（9 个 concern objects）**。按下表把 26 函数分入 7 组 + `fs` + `log` 保留顶层：

| 组 | helper | 数 |
|---|---|---|
| `api.report` | makeResult, absoluteArtifact, writeTextFile, buildCrawlReport | 4 |
| `api.handoff` | generateHandoff | 1 |
| `api.engine` | runEngineFetch, selectFetcher | 2 |
| `api.cache` | scraplingCacheDir, ensureDir, isScraplingCached, saveScraplingCache, scraplingSlugFromUrl, loadScraplingCache, buildScraplingExtractionArgs, runScraplingPreflight | 8 |
| `api.pool` | findAvailablePort, startObscuraServe, concurrentFetch, stopObscuraServe, runObscuraPreflight | 5 |
| `api.traversal` | pagePatternMatches, collectLinksFromHtml, nextPaginationUrl | 3 |
| `api.convert` | convertTraversalToMarkdown, collectMarkdownArtifacts, urlToStructuredPath | 3 |
| `api.fs` / `api.log` | （顶层，不分组——单成员且语义独立） | 2 |

总计 26 函数 + fs + log。分组依据 = 关注点内聚（cache 8 个围绕 scrapling 缓存生命周期；pool 5 个围绕 obscura serve-pool；report 4 个围绕产出构建）。

**D2 — `nextPaginationUrl` 不移入 seam 模块**。再审查暗示「纯 helper 可入住」，但 `nextPaginationUrl` 虽 cli 内零调用者，移入需 (a) 把它的逻辑搬进 crawl_scrapling.mjs，(b) 从 bundle 删——但它是 `api.traversal` 组的一员，组内另两个（pagePatternMatches/collectLinksFromHtml）是 shared 不能移。移一个留两个 = 组内分裂，破坏 D1 的分组一致性。**决定**：保留 `nextPaginationUrl` 在 cli.mjs，留 `api.traversal` 组完整。收益（少一个 bundle entry）< 成本（组内不一致 + 移动逻辑的回归面）。`ponytail:` 一致性 > 微缩减。

**D3 — 调用点机械重写**。`crawl_scrapling.mjs` 内 ~40 处 `api.<helper>` → `api.<group>.<helper>`，纯查找替换，按 D1 分组表映射。无逻辑改动。每处改动后跑静态纪律测试 + 5 个行为测试确认绿。

**D4 — 静态纪律测试升级**。现有 `readCrawlApiKeys` + 「扫 bare call」逻辑（C4）保留。新增「扫 flat `api.<helper>` 残留」：从 cli.mjs 的 grouped bundle 解析出 `{group → [keys]}` 映射，扫 crawl_scrapling.mjs 内任何 `api.<key>` 其中 `<key>` ∈ 某组的 flat 调用，发现即失败。这把 spec 的 `seam-surface-uses-named-concern-groups` scenario 变成可执行断言。

**D5 — bundle 构造同步**。`cli.mjs:2129-2141` 的 `crawlApi = { flat... }` 改为 `crawlApi = { fs, log, report: {...}, handoff: {...}, ... }`。3 个 dispatch 点（2217/2380/2384）不变（仍传 `crawlApi` 整体）。

**D6 — C10 同步**。`chrome-agent-cli.mjs` 是 tracked file，本 change 改其内容 → C10 触发。归档前 SHALL：`cp scripts/chrome-agent-runtime.mjs ~/.agents/scripts/chrome-agent.mjs` + 刷新 `~/.agents/scripts/.chrome-agent-installed-hash` 至 HEAD。见 binding 同步约束。runtime.mjs 不变（只 cp），cli.mjs 是改动源。

## Risks / Migration

**风险**：
- *低-中。* 纯机械重构（flat→grouped），无逻辑改动。回归面：~40 调用点 + bundle + 测试 stub。缓解：静态纪律测试（C4 + D4 升级）+ 5 个行为测试 + 全量 crawl suite（19 测试）逐切片跑。
- C10 同步是新步骤（前两个 change 不触发）。漏做 = 全局副本漂移、doctor 误判。tasks.md 显式列为归档前置。
- stub api 重构：`tests/crawl_scrapling.test.mjs` 的 `stubApi` 从 flat 改 grouped，5 个行为测试的 stub 构造要同步。漏改 = 测试红。

**迁移**：无外部调用方感知。3 个 dispatch 点传的还是 `crawlApi` 对象（形状变了，但 runCrawlScrapling 是唯一消费者）。

**C10 全局同步**：**触发**（见 D6）。

**验证锚点**：`node --test tests/crawl_scrapling.test.mjs tests/crawl-scrapling-pages-scope.test.mjs tests/fetch-strategy-selector.test.mjs`（19 测试全绿）；静态纪律测试（C4 bare-call + D4 flat-call 双检）；可选 `chrome-agent doctor` 烟测默认 crawl 路径产出不变；`git diff` 确认 crawl 命令代码路径无逻辑改动（仅 `api.X` → `api.group.X`）。
