# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `openspec/specs/page-assignment/` — 页面分配行为真源（优先级链、MW category 匹配、source_categories 分配、Step 3.5 回退）
- `project_page_ref`:
  - `scripts/pipeline/pipeline/page_assigner.py` — 当前实现（含 Step 2 exact-1-match 逻辑，需追加 Step 3.5）
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — BOI 站点策略（验证目标）
  - `openspec/changes/fix-boi-config-issues/` — 前置 change（已修改 assignment_priority + exact-1-match spec，本 change 在此基础上追加 fallback）
- `additional_context_refs`:
  - `openspec/changes/archive/2026-05-20-fix-pipeline-assignment-and-output/specs/page-assignment/spec.md` — 前次 page-assignment 修复（S-1/S-2 根因与修复）
  - `/tmp/boi-test-crawl/page_manifest.json` — 复现数据：71 页 Items∈source_cats 但入 misc
  - `/tmp/boi-test-crawl/discovery_summary.json` — 复现 summary

## Source of Truth

- 行为规范真源：`specs/page-assignment/spec.md`（本次 change 的 spec delta）
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `openspec/specs/page-assignment/spec.md` — 合并 spec delta（Step 3.5 fallback requirement）
- `writeback_owner`: chrome-agent 仓库维护者
- `writeback_timing`: verification 完成后，writeback 阶段执行

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 与 `fix-boi-config-issues` 当前的 exact-1-match spec 无冲突——本 change 在 Step 3 之后、Step 4 之前插入新步骤

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
