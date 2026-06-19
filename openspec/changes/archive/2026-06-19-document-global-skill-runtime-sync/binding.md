# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
- `project_page_ref`:
  - `docs/playbooks/chrome-agent-global-install.md` — 全局安装/同步操作手册（主回写目标）
  - `AGENTS.md` — 项目治理入口（§3 Governance Rules、§11 Prerequisite Reading）
  - `skills/chrome-agent/SKILL.md` — 已有 `global_skill_updated` 标志与 reload 提示（上下文输入，本 change 不修改其行为）
- `additional_context_refs`:
  - `scripts/chrome-agent-cli.mjs` — `runAutoUpdateGlobalFiles` / `runGitFetchCheck` / `runTrackedFilesCheck`（被文档化的行为真源，仅作输入，不修改）
  - `scripts/install-chrome-agent-cli.sh` — 一次性安装脚本（上下文输入）
  - `scripts/chrome-agent-runtime.mjs` — runtime 源文件（被同步对象，仅作输入）

## Source of Truth

- 行为规范真源：`specs/global-skill-runtime-sync/spec.md`（本 change 新建 capability）
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据。本 change 是文档型 change：`scripts/chrome-agent-cli.mjs` 中的同步代码行为是既成事实的输入，spec 据此固化文档契约，不修改代码行为。

## 回写目标

- `writeback_targets`:
  - `docs/playbooks/chrome-agent-global-install.md` — 新增「Case 6: 手动同步全局副本」；Version Freshness 段补充「ahead of origin」情形；新增 installed-hash 语义小节
  - `AGENTS.md` — §3 新增「Skill/Runtime 全局同步」治理条目；§11 必读表新增「改 runtime/cli/SKILL.md」任务行并指向上述 playbook
- `writeback_owner`: chrome-agent maintainer
- `writeback_timing`: 实现完成并通过 doctor 验证后立即回写

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 本 change 仅写文档（playbook + AGENTS.md），不触碰 `scripts/`、`configs/`、`sites/`，因此不触发 C9 测试义务与引擎版本同步约束（C4）
- 不引入新的 `chrome-agent sync` 子命令；该命令本 change 显式排除，留作未来独立 change

## 待确认项

- [x] 已确认标准页引用（OrbitOS Spec Standard v0.3）
- [x] 已确认项目页引用（playbook + AGENTS.md + SKILL.md 上下文）
- [x] 已确认回写目标与权限（repo-local，无外部依赖）
- [x] 已确认异常处理与冲突策略（spec 优先；同步后 hash 必须刷新至当前 HEAD）
