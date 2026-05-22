# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: 无外部 spec 标准（纯代码优化 change）
- `project_page_ref`:
  - `docs/architecture/02-pipeline-flow.md` — 管线数据流文档（Fetch 阶段描述）
  - `scripts/pipeline/pipeline/phases/fetch.py` — Fetch 阶段实现（变更主目标）
  - `scripts/pipeline/pipeline/cache.py` — 缓存模块（依赖）
- `additional_context_refs`:
  - `docs/architecture/01-overview.md` — 系统全景
  - `docs/architecture/08-tech-stack.md` — 技术栈约束（Python 3.9+ 兼容）

## Source of Truth

- 行为规范真源：本次 change 无外部 spec，变更真源为 `scripts/pipeline/pipeline/phases/fetch.py`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `docs/architecture/02-pipeline-flow.md` — 更新 Fetch 阶段描述，补充快速路径行为
- `writeback_owner`: 实施者
- `writeback_timing`: 实施完成后、验证通过前

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 本 change 不涉及跨仓库同步

## 待确认项

- [x] 已确认标准页引用（无外部 spec）
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
