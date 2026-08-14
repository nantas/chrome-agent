# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `docs/architecture/00-target-architecture.md` §4.4 Mirror Anti-Patterns + 不变量 I2（mirror 编排不含变换逻辑）；`docs/GOVERNANCE.md` §3（change 生命周期 + SSOT 仲裁）；`openspec/specs/pipeline/pipeline-infobox.md`（C 候选要废弃的 2 个 frozen requirement：`render-infobox-table-uses-shared-lib`、`infobox-handler-callbacks`）；`openspec/specs/convert/spec.md::convert-kernel-three-layer-interface`（C 删除后 convert 产出不变性的 spec 依据）；C10 规范见 `docs/playbooks/chrome-agent-global-install.md` Case 6 + Installed Hash Semantics
- `project_page_ref`: 架构再审查报告 New #3（handoff envelope 半生抽取，10 处 `generateHandoff` + `crawlInternalError` 只覆盖 2 处）、New #4（obscura-serve-pool 生命周期 ×3）、New #5（infobox 渲染 dead code ~130 行，audit 确认不可达）来源 `/var/folders/.../architecture-review-20260813-154550.html`；调研报告（本会话，A+B+C 范围 + 精确边界）
- `additional_context_refs`: `scripts/chrome-agent-cli.mjs:2230`（`crawlInternalError` 半生实现）、:2667（runScrape pool 块）、:3061（runBatch pool 块）、:3839（runCrawlSitemapDiscovery 5 处内联 handoff 块）；`scripts/lib/extraction/converter.py:273-293,343-350,391-519,54-68`（C 候选 dead code 精确边界，subagent reachability audit 给出）；`scripts/lib/crawl_scrapling.mjs`（pool 第 3 处，已 grouped 为 `api.pool`）；`scripts/lib/extraction/infobox.py`（SSOT，不动）；`scripts/lib/extraction/preprocessor.py:41-44`（infobox 容器剥离点）

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `openspec/specs/fetch/spec.md`（A+B 候选若涉 fetch 能力，归档时 spec delta 提升；或若无 spec 级 requirement 变化则纯代码清理无 spec 回写）
  - `openspec/specs/pipeline/pipeline-infobox.md`（C 候选：REMOVED 2 个 requirement，归档时从 frozen spec 删除）
  - `openspec/specs/convert/spec.md`（C 候选若触发 convert-kernel-three-layer-interface 的澄清，delta 提升）
  - C10 全局同步：`chrome-agent-cli.mjs` tracked file 被 A+B 改 → cp runtime + 刷 hash（与 New #2 同模式）
- `writeback_owner`: 实施 agent
- `writeback_timing`: 验证通过后、归档前
- C10 全局同步：**触发**（A+B 改 `chrome-agent-cli.mjs` tracked file）。归档前 SHALL `cp scripts/chrome-agent-runtime.mjs ~/.agents/scripts/chrome-agent.mjs` + 刷新 `~/.agents/scripts/.chrome-agent-installed-hash` 至 HEAD。C 改 `converter.py`（非 tracked）不触发。整体 change 触发 C10。

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- **外部行为不变性（三候选共同承诺）**：
  - A：handoff envelope 抽取后，各 handler 的 handoff 文档产出 + failure result 字节级不变
  - B：obscura pool 合并后，parallel fetch 产出 + fallback 行为不变
  - C：infobox dead code 删除后，convert 产出 Markdown 字节级不变（dead code 本就不可达，删除 = 纯净）——由 `test_convert_equivalence.py`（CV3/CV4/CV5 等价）+ `test_convert_cleanup_consistency.py`（已断言 infobox 被**去除**而非渲染）双重保证
- **C 的 spec 治理在同一 change 闭环**：REMOVED `pipeline-infobox.md` 的 2 个 requirement + 代码删除同 commit；REMOVED requirement 的 reason = 架构演变为 preprocess-去除 + Step-1 BS4 提取（`infobox.py` SSOT），convert 期渲染路径废弃
- **不碰 SSOT**：`scripts/lib/extraction/infobox.py`（真正的 infobox kernel，BS4 路径）、`preprocessor.py` 剥离逻辑、`extract_card_stats`（用原始 html，已解耦）——均不动
- **D 候选明确排除**：cli.mjs 6 个大 handler 抽取（runExplore/runBootstrapStrategy/runBatch/runCrawlSitemapDiscovery/runCrawlSitemapExtraction/runCrawlMediawikiApi）不在本 change，独立后续

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限（C10 触发——A+B 改 cli.mjs tracked file；C 改 converter.py 非 tracked；pipeline-infobox.md 归档时 REMOVED）
- [x] 已确认异常处理与冲突策略（三候选行为不变；C 的 spec 治理同 change 闭环；D 排除）
