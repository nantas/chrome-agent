# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `openspec/specs/pipeline/pipeline-discovery.md`（homepage-driven-discovery phase — P0/P2 根因）
  - `openspec/specs/pipeline/pipeline-core.md`（orchestration + assembly — P1/P2 根因）
  - `openspec/specs/pipeline/pipeline-conversion.md`（converter + link_fixer — P3/P4/P5 根因）
- `project_page_ref`:
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`（BOI 策略配置）
  - `scripts/pipeline/pipeline/orchestrator.py`（排除逻辑 + assembly dispatch）
  - `scripts/pipeline/pipeline/phases/assemble.py`（list_page index 生成、category index 生成）
  - `scripts/pipeline/pipeline/phases/discovery_homepage.py`（list page 目录分配）
  - `scripts/pipeline/converters/link_fixer.py`（括号文件名修复）
  - `scripts/lib/extraction/converter.py`（YouTube 残留清理、首图选择）
  - `outputs/test-100-extraction/`（100 页测试输出——验证基准）
  - `tests/fixtures/boi-crawl-100-manifest.json`（测试基线 manifest）
  - `tests/e2e/boi-100-baseline.sh`（基线测试运行器）
- `additional_context_refs`:
  - `openspec/changes/fix-pipeline-quality-gaps/`（前置 change，已修复 discovery dispatch 但未覆盖本 change 的问题）

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`（Known Issues 表更新）
  - `outputs/handoffs/20260518-crawl-bindingofisaacrebirth-wiki-gg/handoff.md`（Issue 状态更新）
- `writeback_owner`: chrome-agent
- `writeback_timing`: change 验证完成后

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 本 change 不创建新 spec，而是对现有 `pipeline-discovery`、`pipeline-core`、`pipeline-conversion` spec 追加 delta（通过 spec/changes 文件）

## 待确认项

- [x] 已确认标准页引用：三个现有 pipeline spec
- [x] 已确认项目页引用：策略文件、管线代码、测试基线
- [x] 已确认回写目标与权限：策略文件 + handoff 文档
- [x] 已确认异常处理与冲突策略：以 specs/ 为准
