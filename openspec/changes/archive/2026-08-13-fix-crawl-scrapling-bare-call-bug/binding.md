# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `docs/GOVERNANCE.md` §3（change 生命周期 + SSOT 仲裁）、`docs/adr/0013-four-dimensional-domain-model.md` §4.4 Mirror Anti-Patterns（seam 模块的 deps 注入 SHALL 与调用点一致）、`openspec/specs/crawl-scrapling-pages-scope/spec.md`（scrapling crawl 产出契约，markdown artifact 分支属其行为面）
- `project_page_ref`: 架构再审查报告 Critical callout（crawl seam 抽取引入的活跃 ReferenceError）来源 `/var/folders/.../architecture-review-20260813-154550.html`；`scripts/lib/crawl_scrapling.mjs:328`（缺陷行）；`tests/crawl_scrapling.test.mjs:95,108`（现有测试均 `markdown:false`，未覆盖崩溃分支）
- `additional_context_refs`: `scripts/chrome-agent-cli.mjs:1324`（`collectMarkdownArtifacts` 定义）、`:2136`（`crawlApi` bundle 注入点，缺陷函数已存在于 bundle）；commit `04a35fb`（extract-crawl-scrapling-orchestrator，引入本缺陷的提取）；commit `9cd9a3a`（紧随其后的两处 CRITICAL 回归修复，未覆盖本分支）

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`: `openspec/specs/crawl-scrapling-pages-scope/spec.md`（若 markdown artifact 收集行为需补契约条款，在此 spec delta 内体现）；架构再审查报告（外部临时文件，不回写）
- `writeback_owner`: 实施 agent
- `writeback_timing`: 验证通过后、归档前
- C10 全局同步：**不触发**。本 change 仅修改 `scripts/lib/crawl_scrapling.mjs` + 新增测试，不触碰 C10 tracked files（`chrome-agent-runtime.mjs` / `chrome-agent-cli.mjs` / `skills/chrome-agent/SKILL.md`）。`collectMarkdownArtifacts` 已存在于 `crawlApi` 注入 bundle，缺陷纯粹是调用点缺 `api.` 前缀。

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 外部行为不变性：本 change 是缺陷修复，修复后 crawl `markdown:true`（默认）路径 SHALL 不再抛 `ReferenceError` 并产出与设计一致的 markdown artifacts；`markdown:false` 路径行为字节级不变
- 缺陷函数已正确注入 bundle（`crawlApi.collectMarkdownArtifacts`），修复 = 调用点补 `api.` 前缀，禁止改动 bundle 定义或 helper 实现

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限（C10 不触发，已核实 tracked files 清单）
- [x] 已确认异常处理与冲突策略（纯调用点修复，无 bundle / helper 改动）
