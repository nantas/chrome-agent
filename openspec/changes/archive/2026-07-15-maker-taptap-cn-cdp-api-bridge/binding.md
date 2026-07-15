# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `openspec/specs/fetch-kernel/spec.md`
  - `openspec/specs/strategy-schema/spec.md`
  - `openspec/specs/pipeline-orchestration/spec.md`
  - `openspec/specs/pipeline-fetch/spec.md`
- `project_page_ref`:
  - `docs/architecture/00-target-architecture.md` — 能力注册表更新（fetch 新增 cdp-api-bridge 路径）
  - `docs/architecture/02-pipeline-flow.md` — 管线数据流图新增 rest 平台路径
  - `docs/architecture/03-strategy-schema.md` — 策略 schema 新增 `api.platform: rest`、`requires_authentication`、`api.auth` 字段
  - `docs/playbooks/api-backed-spa-cdp-bridge.md` — 实战记录（已存在，需补充 verify 结果）
  - `docs/playbooks/authenticated-sessions.md` — 已登录会话规则（已部分修改，需同步）
  - `docs/playbooks/README.md` — playbook 索引（已部分修改，需同步）
- `additional_context_refs`:
  - `sites/strategies/maker.taptap.cn/strategy.md` — 新站点策略（本次产出）
  - `sites/strategies/registry.json` — 策略注册表（本次更新）
  - `configs/capability-registry.yaml` — 能力注册表（本次更新）

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`（delta spec），归档后回填到 `openspec/specs/`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据；冲突时以 `specs/` 为准

## 回写目标

- `writeback_targets`:
  - `openspec/specs/fetch-kernel/spec.md` — 追加 `cdp-api-bridge` 执行路径的 requirement
  - `openspec/specs/strategy-schema/spec.md` — 追加 `api.platform: rest`、`requires_authentication`、`api.auth` 字段定义
  - `openspec/specs/pipeline-orchestration/spec.md` — 追加 rest 平台路由分支
  - `docs/architecture/00-target-architecture.md` — fetch 目标模块追加 `fetch_cdp_api.py`
  - `docs/architecture/03-strategy-schema.md` — 标注新字段为正式（移除 proposed）
  - `docs/playbooks/api-backed-spa-cdp-bridge.md` — 补充验证结果与 CLI 命令示例
- `writeback_owner`: chrome-agent maintainers
- `writeback_timing`: 归档时执行（verify 通过后）

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- C11 约束：`fetch_cdp_api.py` 实现后必须同步 `configs/capability-registry.yaml` 的 `fetch.engines`
- C7 约束：`strategy.md` frontmatter 修改后必须同步 `registry.json`

## 待确认项

- [x] 已确认标准页引用（fetch-kernel、strategy-schema、pipeline-orchestration、pipeline-fetch）
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
