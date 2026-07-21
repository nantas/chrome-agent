# Binding

## 标准与项目页面绑定

- `spec_standard_ref`（本次 change 参照的冻结规范，作为边界基准；本 change 不修改其 requirement）:
  - `openspec/specs/engine-registry/spec.md` — 声明外部 CLI（agent-reach / `gh` / `yt-dlp`）不进入引擎注册表的边界依据
  - `openspec/specs/governance/governance.md` — 治理层 spec 先例（AGENTS.md 结构、workflow routing、engine selection），本次新增的 `external-cli-routing` spec 与其同层
- `project_page_ref`（本次 change 直接产出/修改的项目文档）:
  - `AGENTS.md` §3 Governance Rules — 新增"外部能力路由（External CLI 优先）"小节，作为平台→外部 CLI 路由表的文档层 SSOT
  - `skills/chrome-agent/SKILL.md` — Intent Routing 顶部新增 Platform Pre-check（C10 tracked 源，需同步全局副本）
  - `sites/strategies/x.com/strategy.md` — Overview 段补外部 CLI 路由指针（frontmatter 不变）
  - `docs/playbooks/fallback-escalation.md` — 开头补前置说明：外部 CLI 优先于引擎 escalation chain
  - `docs/playbooks/authenticated-sessions.md` — 补指针：外部 CLI 优先于 session 复用路径
- `additional_context_refs`:
  - `~/.agents/skills/agent-reach/SKILL.md` — agent-reach 能力路由器（外部维护，本仓库不复制其内容，仅引用平台清单）
  - `CONTEXT.md` — 业务架构维度词汇表（确认外部 CLI 路由发生在 A 轴 fetch 能力被调用之前，不污染 4 维模型）

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 本 change 性质：新增**路由层** spec delta（`external-cli-routing`），锁定"目标平台命中外部 CLI 清单时优先路由到外部 CLI"的决策行为；不修改 A 轴业务能力（fetch / convert / extract / discover / assemble）的任何 requirement
- spec 定位：`external-cli-routing` 为治理/路由层 spec（与 `governance/` 域同层），**不进入** `configs/capability-registry.yaml` 与 `AGENTS.md` §2 Capability Framework（4 维模型），仅落在 `AGENTS.md` §3 Governance Rules
- 边界依据：`capability-registry` spec 的 doctor 检查仅验证 `configs/capability-registry.yaml` 中**已声明**条目需在 §2 有行；`external-cli-routing` 不进 registry.yaml，故不触发该约束（与 `governance/` 域处理一致）
- 项目页面角色：路由表文档层 SSOT 落在 `AGENTS.md` §3；skill / strategy / playbook 仅加指针引用，不复制表格内容
- 非真源说明：项目页面不得替代 spec delta；`AGENTS.md` §3 路由表是文档层 SSOT，行为契约真源为 `specs/external-cli-routing/spec.md`（本次产出）

## 回写目标

- `writeback_targets`（归档时确认一致性）:
  - `openspec/specs/external-cli-routing/spec.md` — 本次新增的行为规范真源（归档时从 change 内 specs/ 回填到顶层 specs/）
  - `AGENTS.md` §3 — 确认"外部能力路由"小节存在且平台清单与 agent-reach 当前支持范围一致
  - `skills/chrome-agent/SKILL.md` — 确认 Platform Pre-check 段存在；**C10 同步**：全局副本 `~/.agents/skills/chrome-agent/SKILL.md` 必须与仓库源一致
  - `sites/strategies/x.com/strategy.md` — 确认 Overview 指针存在且 frontmatter 未被改动
  - `docs/playbooks/fallback-escalation.md` — 确认前置说明存在
  - `docs/playbooks/authenticated-sessions.md` — 确认指针存在
- `writeback_owner`: chrome-agent maintainers
- `writeback_timing`: 归档时执行（verification 通过后）；C10 全局副本同步在实现阶段即完成

## 同步约束

- **SSOT 单一**：平台→外部 CLI 路由表只在 `AGENTS.md` §3 维护一份；skill / strategy / playbook 仅加指针引用，不复制表格内容
- **C10 全局同步**：修改 `skills/chrome-agent/SKILL.md`（tracked 源）后，必须同步到 `~/.agents/skills/chrome-agent/SKILL.md`（全局副本），并刷新 `~/.agents/scripts/.chrome-agent-installed-hash` 至当前 `git rev-parse HEAD`
- **不进引擎/能力注册表**：外部 CLI 是 shell-out 工具（与 `gh` / `yt-dlp` 同类），不进入 `configs/engine-registry.json` / `configs/capability-registry.yaml` / `scripts/pipeline/pipeline/registry.py`，也不被 `strategy_loader.py` 特殊解析
- 页面与 spec 不一致时，以 `specs/` 为准；本 change 的行为契约以 `specs/external-cli-routing/spec.md` 为真源，`AGENTS.md` §3 为文档投影
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks

## 待确认项

- [x] 已确认标准页引用（`engine-registry`、`governance/governance.md` 均有内容且相关；已排除空 spec 目录 `global-workflow-skill`、`scrapling-first-browser-workflow`）
- [x] 已确认项目页引用（5 处文档均存在，skill 源 `skills/chrome-agent/SKILL.md` 与全局副本已 diff 确认同步）
- [x] 已确认回写目标与权限（C10 同步路径已在 `docs/playbooks/chrome-agent-global-install.md` Case 6 定义）
- [x] 已确认异常处理与冲突策略（外部 CLI 失败 → fallback 到 chrome-agent 引擎链；未在清单内的平台 → 直接走 chrome-agent 后端）
