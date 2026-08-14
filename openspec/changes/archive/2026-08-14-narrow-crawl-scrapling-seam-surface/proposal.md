# Proposal

## 问题定义

`extract-crawl-scrapling-orchestrator` change（commit `04a35fb`）把 `runCrawlScrapling` 抽成 seam 模块 `scripts/lib/crawl_scrapling.mjs`，用注入式 `api` bundle 承接 cli.mjs 的 helper。C4 修复（commit `c51e771`）补上了 `api.` 前缀纪律并钉死成静态测试。但 **bundle 的形状本身仍是问题**：它是一个 **28-entry 的扁平 grab-bag**（26 命名函数 + `fs` + `log`），把 6-7 个不同关注点（engine fetch / scrapling cache / obscura pool / traversal / convert / report / handoff）压成一个无结构的对象。

三个并发症状（架构再审查 New #2）：

1. **不降低耦合，只重命名**：模块 docstring 称 `api` 为「deps-injected seam」，但接口面 = cli.mjs 的全部 crawl helper。deletion test：把 `runCrawlScrapling` 内联回 cli.mjs，会删掉 29-key bundle、`api.` 前缀风险、以及 C4 的 bug——seam shape 本身是 shallow，只是给耦合换了个名字。
2. **无契约边界**：reader 面对 `api.collectMarkdownArtifacts` / `api.runObscuraPreflight` / `api.scraplingSlugFromUrl` 无法一眼看出哪些是 engine fetch、哪些是 cache、哪些是 report——关注点被扁平化抹平。
3. **C4 bug 的结构性温床**：扁平 bag 里 bare-vs-`api.` 拼写错误类正是 C4 的 bug 根因。grouped 结构让「这个 helper 属哪个关注点」显式化，降低下次抽取时同类错误概率。

**根因**：seam 设计时只考虑「避免循环 import」（用注入解决），没考虑「注入什么形状」。一个 reader 持有不了 29 个无分组 key 的心智模型。

**范围澄清（诚实修正再审查报告）**：再审查报告建议「缩到 ~4 真协作方」，但**这个目标过于天真**——bundle 里大多数 helper 跨 cli.mjs 共享（`pagePatternMatches` 9 refs、`selectFetcher` 8 refs、`buildScraplingExtractionArgs`/`convertTraversalToMarkdown`/`collectMarkdownArtifacts`/`collectLinksFromHtml`/`urlToStructuredPath`/`scraplingSlugFromUrl` 都有 cli 内调用者），移入 seam 模块会循环 import 或复制。真正 crawl-专属且纯的 helper 极少（`nextPaginationUrl` 是 cli 内零调用者的候选）。故本 change 的真实目标是**重塑 bundle 形状为 named concern objects**（让 seam 读起来像契约），而非物理移动 helper。

## 范围边界

**In scope**：
- 把 `crawlApi` 从 flat 29-key 重塑为 grouped：`api.fs`、`api.log`、`api.report{makeResult,absoluteArtifact,writeTextFile,buildCrawlReport}`、`api.handoff{generateHandoff}`、`api.engine{runEngineFetch,selectFetcher}`、`api.cache{scraplingCacheDir,ensureDir,isScraplingCached,saveScraplingCache,scraplingSlugFromUrl,loadScraplingCache,buildScraplingExtractionArgs,runScraplingPreflight}`、`api.pool{findAvailablePort,startObscuraServe,concurrentFetch,stopObscuraServe,runObscuraPreflight}`、`api.traversal{pagePatternMatches,collectLinksFromHtml,nextPaginationUrl}`、`api.convert{convertTraversalToMarkdown,collectMarkdownArtifacts,urlToStructuredPath}`
- `crawl_scrapling.mjs` 全部调用点从 `api.<helper>` 改为 `api.<group>.<helper>`
- `cli.mjs` bundle 构造处同步改为 grouped 对象
- 静态纪律测试适配 grouped 结构（扫 `api.<group>.<key>` 模式 + flat key 残留检测）
- spec delta：`crawl-scrapling-orchestrator-is-a-seam-module` 声明 seam surface 形状契约（named concern objects + 分组调用约定）
- （可选，design.md 定夺）移入 `nextPaginationUrl` 到 seam 模块作为「纯 helper 入住」示范——若评估有循环风险或收益小则不做

**Out of scope**：
- 移动任何 shared helper（`pagePatternMatches`/`selectFetcher` 等）——会循环 import
- 抽取 cli.mjs 其余 6 个大 handler（runExplore/runBootstrapStrategy/runBatch/runCrawlSitemapDiscovery/runCrawlSitemapExtraction/runCrawlMediawikiApi）——原 C4 候选剩余部分，另立 change
- 改 seam 的 deps 注入「机制」（仍是手传 `api` 对象）——只改「形状」
- crawl 控制流/产出逻辑任何改动

**不变性**：crawl 命令产出（manifest/report/merged output/artifacts）字节级不变——纯 seam surface 重塑。

## Capabilities

### New Capabilities

_(无)_

### Modified Capabilities

- `fetch`: 既有 `crawl-scrapling-orchestrator-is-a-seam-module` requirement MODIFIED——声明 `api` bundle SHALL 按 named concern objects 组织（report/handoff/engine/cache/pool/traversal/convert/fs/log），调用点 SHALL 用 `api.<group>.<helper>`；保留 C4 的调用纪律（无 bare call）+ 静态纪律测试

## Capabilities 待确认项

- [x] 能力清单已与用户确认（仅 Modified `fetch`；用户指令「继续 new#2」，New #2 = crawl seam 表面过宽，归属 fetch 能力的既有 seam 契约）

## Impact

- **代码**：`scripts/lib/crawl_scrapling.mjs`（~40 处 `api.X` → `api.<group>.X`）、`scripts/chrome-agent-cli.mjs:2129-2141`（bundle 构造 flat → grouped）、`tests/crawl_scrapling.test.mjs`（stub api 适配 grouped + 静态纪律测试适配）
- **测试**：现有 5 个 crawl_scrapling 测试 SHALL 全绿（stub api 重构为 grouped）；静态纪律测试逻辑升级
- **行为**：零变更（纯结构重塑）
- **规范**：`openspec/specs/fetch/spec.md` delta（MODIFIED `crawl-scrapling-orchestrator-is-a-seam-module`）
- **C10 全局同步**：**触发**（`chrome-agent-cli.mjs` 是 tracked file 且被改）。归档前 SHALL cp runtime + 刷 installed-hash。这是本 change 与前两个的关键差异
- **风险**：低-中。纯机械重构（flat→grouped），但触碰面广（~40 调用点 + bundle + 测试 stub）；C10 同步是额外步骤。静态纪律测试是回归守卫

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：target-arch §4.4 + 不变量 I2、`crawl-scrapling-orchestrator-is-a-seam-module` requirement、C4 修复 archive（纪律测试先例）
  - 项目页：架构再审查报告 New #2、`crawl_scrapling.mjs`、`cli.mjs:2129-2141`、`tests/crawl_scrapling.test.mjs`
  - 回写目标：`fetch/spec.md` delta + C10 全局同步（runtime + installed-hash）
