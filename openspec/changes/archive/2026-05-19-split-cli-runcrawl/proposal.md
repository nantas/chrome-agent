# Proposal

## 问题定义

`chrome-agent-cli.mjs` 中 `runCrawl()` 函数当前 ~764 行，在一个函数体内混合了三种互不重叠的调度路径：

1. **MediaWiki API 管线路径**（~128 行）— 检测 `api.platform === "mediawiki"` 后 spawn Python 管线
2. **Scrapling discovery-only 路径**（~86 行）— 仅做首层链接发现，不执行遍历
3. **Scrapling 标准遍历路径**（~360 行）— queue 驱动的有界遍历 + Phase 2 Markdown 转换 + 产物收集

这违反了 AGENTS.md §2.5「模式 2: God Object (单文件过载)」的治理约束：单一函数承担过多不相关职责，难以独立理解、测试和维护。

该问题是结构优化重构规划（`docs/plans/2026-05-19-structure-refactor-and-docs.md`）的 **Change 5**，也是 Phase 1-4 重构的最后一环。前序 Change 1-4 已完成了 Python 层的共享库提取、统一提取引擎、orchestrator 拆分、包重命名和 Phase 文件重命名。

## 范围边界

**范围内：**
- 将 `runCrawl()` 的三路调度提取为三个独立内部函数
- `runCrawl()` 精简为 ~60 行纯路由入口
- 仅涉及 `scripts/chrome-agent-cli.mjs` 一个文件

**范围外：**
- 不改变任何外部接口（CLI 参数面、输出格式、退出码行为）
- 不改变 `runFetch()`、`runScrape()`、`runExplore()` 等其他 CLI 函数
- 不改变 Node.js ↔ Python 进程边界的 spawn 参数（已在 Change 3 中更新为 `scripts.pipeline`）
- 不改变测试文件

## Capabilities

### New Capabilities

（无新增能力 — 本次为纯内部重构，不增加外部可见功能）

### Modified Capabilities

- `global-capability-cli`: 将 `runCrawl()` 从 ~764 行单体函数拆分为 `runCrawlMediawikiApi()` + `runCrawlScraplingDiscovery()` + `runCrawlScrapling()` 三个独立函数；`runCrawl()` 精简为路由入口；外部接口（命令面、参数面、输出格式、退出码）不变

## Capabilities 待确认项

- [x] 能力清单已与用户确认（用户原始请求为「基于上述方案产出 change 工件」，方案已明确定义 Change 5 范围为拆分 runCrawl 大函数）

## Impact

- **代码可维护性**: `runCrawl()` 从 ~764 行降至 ~60 行，三个子函数各 ≤ 400 行，每个函数职责单一
- **测试可行性**: 拆分后的独立函数更容易进行单元级行为验证
- **回归风险**: 低 — 纯内部重构，不改变任何外部行为。验证标准：`node --test tests/` 通过 + 对 wiki.gg 目标站点的 crawl 产出一致
- **依赖变更**: 无

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：`openspec/specs/global-capability-cli/spec.md`
  - 项目页：`docs/plans/2026-05-19-structure-refactor-and-docs.md`
  - 回写目标：更新规划文档 Phase 3 完成状态
