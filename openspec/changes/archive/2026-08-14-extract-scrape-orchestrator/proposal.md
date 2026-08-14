# Proposal

## 问题定义

`scripts/chrome-agent-cli.mjs` 是 ~4200 行的 god module，其中 `runScrape`（L2594-2803，210 行）是体量最大的 command handler。它内联了 5 个关注点：arg 解析、scrapling preflight、无界 BFS 遍历、phase2 Markdown 转换（含 obscura pool 并行路径）、result synthesis。该 handler 目前**只能经 subprocess end-to-end 测试**——其 BFS 遍历、partial_success 降级、parallel-fallback 分支**零单测覆盖**。

这与架构再审查报告（2026-08-13）候选 D 一致：cli.mjs 仍是 god module，大 handler 需抽到 `scripts/lib/` seam 模块以获得可测性。

已建立的先例：`runCrawlScrapling`（180 行）已抽到 `scripts/lib/crawl_scrapling.mjs`，采用 `ctx + opts + api` 三参签名、grouped concern bundle（api.fs/api.report/api.handoff/api.engine/api.cache/api.pool/api.traversal/api.convert）、配套纪律测试三件套（bare-call 检测 + flat-call 检测 + behavior 注入）。`runScrape` 与 `runCrawlScrapling` 高度同构（同为 preflight → BFS queue → phase2 markdown → result 模式），是复刻该 seam 模式的最佳第二实例。

**为什么选 runScrape 而非 handoff 推荐的 runCrawlSitemapDiscovery**：runScrape 零外部 subprocess 副作用（全走注入的 helper），与范本同构度最高，bundle 形状几乎现成；其 BFS + partial_success + parallel fallback 核心逻辑当前零覆盖，抽出带来的可测性边际收益最大。详见 `design.md` §决策。

## 范围边界

**本 change 范围内**：
- 将 `runScrape` 从 `scripts/chrome-agent-cli.mjs` 抽出到新文件 `scripts/lib/scrape.mjs`，签名改为 `runScrape(ctx, opts, api)`
- 在 cli.mjs L3667（唯一 dispatch 点）构造 `scrapeApi` grouped concern bundle 并调用
- 新增 `tests/scrape.test.mjs`：纪律测试三件套（复刻 `tests/crawl_scrapling.test.mjs`）
- 在 `openspec/specs/fetch/spec.md` 增补 `scrape-orchestrator-is-a-seam-module` requirement

**本 change 范围外**：
- 不抽其他 handler（runCrawlSitemapDiscovery / runBootstrapStrategy / runBatch 等留待后续 change，handoff 明确"D 是不同物种，拆开做"）
- 不改变 scrape 命令的外部行为（byte-identical 不变性）
- 不移动 scrape 专属 helper（`extractAllLinks` L2532、`buildScrapeReport` L2568 留在 cli.mjs，经 api 注入）
- 不引入新的 bundle group 形状（沿用 crawlApi 已建立的 9-group）

## Capabilities

### New Capabilities

_无新增能力——runScrape 抽取是对既有 fetch 能力内部结构的重构，不引入新能力域。_

### Modified Capabilities

- `fetch`: 新增 `scrape-orchestrator-is-a-seam-module` requirement，确立 runScrape 作为 seam 模块的契约（抽取位置、签名、deps 注入、纪律测试三件套），与既有 `crawl-scrapling-orchestrator-is-a-seam-module` 同型。

## Capabilities 待确认项

- [x] 能力清单已确认（scrape 属于 fetch 能力域，fetch spec L95 已将 scrape 列为 internalFailure 覆盖的 handler 之一；无新能力）

## Impact

- **代码**：`scripts/chrome-agent-cli.mjs` 净减 ~210 行（runScrape 主体移出，dispatch 点从直接调用改为构造 bundle + 调用），新增 `scripts/lib/scrape.mjs`（~220 行，含 api 参数解构）。新增 `tests/scrape.test.mjs`（~180 行，复刻范本）。
- **测试**：node 测试数从 86 增至 ~91（新增 bare-call + flat-call + behavior ~5 个 case）。
- **行为**：scrape 命令产出字节级不变（纯结构重构）。
- **C10**：归档时 cp `chrome-agent-cli.mjs` → `~/.agents/scripts/chrome-agent.mjs` + 刷新 installed-hash。
- **可测性**：runScrape 的 BFS / partial_success / parallel-fallback 分支首次获得单测覆盖。

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：`docs/playbooks/chrome-agent-global-install.md` Case 6、`docs/GOVERNANCE.md` §3、`docs/adr/0013-four-dimensional-domain-model.md` §4.4
  - 项目页：架构再审查候选 D（`outputs/handoffs/20260814-arch-review-remaining-work/handoff.md`）、seam 范本 `scripts/lib/crawl_scrapling.mjs`
  - 回写目标：`~/.agents/scripts/chrome-agent.mjs`、`~/.agents/scripts/.chrome-agent-installed-hash`
