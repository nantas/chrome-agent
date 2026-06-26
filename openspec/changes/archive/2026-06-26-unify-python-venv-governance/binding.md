# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `openspec/specs/engine-registry/spec.md` — 引擎注册表与治理约束
  - `openspec/specs/scrapling-cli-environment/spec.md` — 引擎 venv 预检模式（cloakbrowser 治理方案参照基准）
  - `openspec/specs/doctor-repo-freshness/spec.md` — doctor 检测项与自动修复语义
  - `openspec/specs/global-skill-runtime-sync/spec.md` — 仓库文件同步到全局副本后须刷新 installed-hash 并 reload skill
- `project_page_ref`:
  - `docs/architecture/06-engine-selection.md` — 引擎选择决策树、preflight 机制说明
  - `docs/architecture/08-tech-stack.md` — Python 依赖声明、测试基础设施
  - `docs/adr/0002-app-engine-venv-boundary.md` — 应用层/引擎层 venv 分界决策
  - `docs/adr/0003-lazy-trigger-venv-lifecycle.md` — 懒触发 preflight 生命周期决策
  - `CONTEXT.md` / `CONTEXT-MAP.md` — 领域语言词汇表与模块关系图
- `additional_context_refs`:
  - `configs/engine-registry.json` — 引擎能力定义（cloakbrowser-fetch rank 4, draft）
  - `configs/engine-versions.json` — 引擎版本清单（cloakbrowser detection/managed_path）

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`（本次涉及的 engine-registry、scrapling-cli-environment、doctor-repo-freshness）
- 项目页面角色：上下文输入（06-engine-selection.md 描述现有 preflight 机制）/ 治理展示（08-tech-stack.md 声明依赖清单）/ 结果回写（实施后同步更新）
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据；页面条目与 spec 冲突时以 spec 为准

## 回写目标

- `writeback_targets`:
  - `docs/architecture/06-engine-selection.md` → CloakBrowser preflight 节更新为引用新 `cloakbrowser-cli.sh` managed venv
  - `docs/architecture/08-tech-stack.md` → Python Dependencies 节修正 pipeline "(none declared)" 谎言，更新 test_runner 命令示例为 `.venv/bin/python`，新增应用层 venv 约定小节
  - `docs/setup/cloakbrowser-setup.md` → 安装指令从 `pip install cloakbrowser` 更新为 `cloakbrowser-cli.sh preflight`
  - `configs/engine-versions.json` → cloakbrowser 条目 `detection.managed_path` 从 `null` 改为 `$HOME/.cache/chrome-agent-cloakbrowser/bin/python`
- `writeback_owner`: 本 change 实施者
- `writeback_timing`: 所有实施 task 完成后一次性回写

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若 `configs/engine-versions.json` 变更，必须同步 `expected_version` + `managed_path` 字段，遵守 C4 约束
- `scripts/chrome-agent-cli.mjs` 变更后必须同步全局副本并刷新 `~/.agents/scripts/.chrome-agent-installed-hash`（C10 约束）

## 待确认项

- [x] 已确认标准页引用（engine-registry / scrapling-cli-environment / doctor-repo-freshness）
- [x] 已确认项目页引用（06-engine-selection / 08-tech-stack / ADRs / CONTEXT）
- [x] 已确认回写目标与权限（4 个写回目标，均在 repo 内）
- [x] 已确认异常处理与冲突策略（spec 优先于项目页面；engine-versions.json 遵守 C4）
