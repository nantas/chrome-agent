# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `docs/architecture/00-target-architecture.md` §4.4 Mirror Anti-Patterns（seam 模块的 deps 注入 SHALL 与调用点一致）+ 不变量 I2（mirror 编排不包含逻辑）；`docs/adr/` 无 ADR 0013 文件（4d 模型在 target-arch 文档）；`openspec/specs/fetch/spec.md` `crawl-scrapling-orchestrator-is-a-seam-module` requirement（既有 seam 契约，本次 MODIFIED）；`openspec/changes/archive/2026-08-13-fix-crawl-scrapling-bare-call-bug/`（C4 修复建立的 `api.` 前缀纪律 + 静态纪律测试，本 change SHALL 不破坏）
- `project_page_ref`: 架构再审查报告 New #2（crawl seam 32-key bag 不降低耦合只重命名）来源 `/var/folders/.../architecture-review-20260813-154550.html`；`scripts/lib/crawl_scrapling.mjs`（seam 模块，runCrawlScrapling(ctx, opts, api)）；`scripts/chrome-agent-cli.mjs:2129-2141`（`crawlApi` bundle：26 命名函数 + fs + log = 28 entry）；`tests/crawl_scrapling.test.mjs`（静态纪律检查测试 `readCrawlApiKeys`，读取 bundle 字面量——本 change 改 bundle 结构 SHALL 同步更新该测试）
- `additional_context_refs`: 3 个 dispatch 点 `cli.mjs:2217/2380/2384`；bundle key 按关注点分类（engine fetch / scrapling cache / obscura pool / traversal / convert / report / handoff）；shared helper 盘点（`pagePatternMatches` 9 refs、`selectFetcher` 8 refs 跨 cli 共享——不可移入 seam，否则循环 import 或复制）

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`: `openspec/specs/fetch/spec.md`（MODIFIED `crawl-scrapling-orchestrator-is-a-seam-module`：声明 seam surface 形状契约——named concern objects + api.<group>.<helper> 调用约定；归档时 spec delta 提升为 frozen）
- `writeback_owner`: 实施 agent
- `writeback_timing`: 验证通过后、归档前
- C10 全局同步：**触发**。本 change 修改 `scripts/lib/crawl_scrapling.mjs` + `scripts/chrome-agent-cli.mjs`（bundle 构造处，tracked file）+ `tests/crawl_scrapling.test.mjs`。`chrome-agent-cli.mjs` 是 C10 tracked file 且被改（仅内部 bundle 构造形状，不改命令路由/签名/runtime 入口）→ 按规则触发全局同步。详见同步约束。

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- **外部行为不变性**：crawl 命令产出（manifest / report / merged output / artifacts）SHALL 字节级不变——本 change 是 seam surface 重塑（bundle 结构 + 调用前缀），不改控制流或产出逻辑
- **C10 同步判定（重要）**：`chrome-agent-cli.mjs` 在 C10 tracked files 清单内。本 change 触碰它（改 `crawlApi` bundle 构造从 flat → grouped）。按 C10 规则，tracked file 内容变更即触发全局同步（cp runtime + 刷新 installed-hash）。**归档前 SHALL 执行 C10 同步**：`cp scripts/chrome-agent-runtime.mjs ~/.agents/scripts/chrome-agent.mjs` + 刷新 `~/.agents/scripts/.chrome-agent-installed-hash` 至 HEAD。这是本 change 与前两个 change（均不触发 C10）的关键差异
- **既有契约不破坏**：C4 修复建立的 `api.` 前缀纪律 + 静态纪律测试 SHALL 继续通过（测试逻辑需适配 grouped 结构——从「扫 flat key」改为「扫 grouped `api.<group>.<key>` + 残留 flat key」）
- **不移动 shared helper**：`pagePatternMatches`/`selectFetcher`/`buildScraplingExtractionArgs`/`convertTraversalToMarkdown`/`collectMarkdownArtifacts`/`collectLinksFromHtml`/`urlToStructuredPath`/`scraplingSlugFromUrl` 跨 cli 共享，**不可移入 seam 模块**（会循环 import 或需复制）。只有真正 crawl-专属且纯的 helper（如 `nextPaginationUrl`，cli.mjs 内零调用者）可考虑移入——design.md 评估

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限（C10 触发——`chrome-agent-cli.mjs` tracked file 被改；归档前 SHALL 同步）
- [x] 已确认异常处理与冲突策略（外部行为不变；C4 纪律测试适配 grouped 结构）
