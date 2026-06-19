# Proposal

## 问题定义

`chrome-agent` 的全局 skill 与 runtime 同步机制目前分散在三处且各不完整：

1. `docs/playbooks/chrome-agent-global-install.md` 的 Version Freshness 段只覆盖 source repo **behind** `origin/main` 的自动同步，遗漏 **ahead**（本地有未 push 的 commit）这一常见开发场景。
2. 没有「手动同步全局副本」的操作路径——当 HEAD 领先 `origin/main`、或希望改动立即生效而无需等待下一次 `doctor` 时，agent 只能逆向 `runAutoUpdateGlobalFiles` 手写 `cp` + 刷新 hash。
3. `~/.agents/scripts/.chrome-agent-installed-hash` 的语义（记录的是 `git rev-parse HEAD` 而非文件内容 hash，是 doctor 增量判断的种子，手动同步后也必须刷新）未在文档中说明，导致「内容 sha1 已一致但 hash 文件仍指旧 commit」产生同步迷惑。

`AGENTS.md` 作为治理入口，§9 把 playbooks 标为 P2，且无任何条目把「改 runtime/cli/SKILL.md 后要同步全局」导向对应 playbook，agent 无法从治理入口定位到同步流程。

实证：在一次 ahead-of-origin 场景中，doctor 判 `repo_freshness=ok`（不触发 auto-update），但全局副本确已过时，agent 不得不从 `chrome-agent-cli.mjs` 逆向推导出 `cp` + 刷新 HEAD hash 的等价操作才能完成同步。

## 范围边界

In-scope（纯文档）：

- 在 `docs/playbooks/chrome-agent-global-install.md` 新增「Case 6: 手动同步全局副本」，覆盖 ahead / 立即生效场景。
- 在该 playbook 的 Version Freshness 段补充「ahead of `origin/main`」情形的行为说明。
- 在该 playbook 新增 installed-hash 语义小节。
- 在 `AGENTS.md` §3 新增「Skill/Runtime 全局同步」治理条目，并指向上述 playbook。
- 在 `AGENTS.md` §11 Prerequisite Reading 必读表新增「改 runtime/cli/SKILL.md」任务行。

Out-of-scope：

- 不新增 `chrome-agent sync` 子命令（涉及 cli 改动 + C9 测试义务，留作未来独立 change）。
- 不修改 `scripts/chrome-agent-cli.mjs` 的 `runAutoUpdateGlobalFiles` / `runGitFetchCheck` / `runTrackedFilesCheck` 任何代码行为——本 change 是文档型 change，代码为既成事实的输入。
- 不修改 `skills/chrome-agent/SKILL.md` 的 `global_skill_updated` 标志与 reload 提示（已存在且正确，仅作上下文输入）。
- 不改动 `install-chrome-agent-cli.sh`（一次性安装工具，非同步工具）。

## Capabilities

### New Capabilities

- `global-skill-runtime-sync`: 定义全局 skill/runtime 副本与仓库源之间的同步契约——tracked files 清单、auto-update（behind）触发条件、手动同步（ahead / 立即生效）路径、installed-hash 语义与刷新义务，以及 AGENTS.md 治理入口对该契约的锚点引用；将生成 `specs/global-skill-runtime-sync/spec.md`

### Modified Capabilities

- _无_。`chrome-agent-cli.mjs` 中 doctor / auto-update 的代码行为不变，仅将其固化为文档契约；`cli` capability 现有 `cli-interface.md` / `cli-workflows.md` 不涉及同步文档内容，无需修改。

## Capabilities 待确认项

- [x] 能力清单已与用户确认（用户指示「按建议方案创建 change」；New capability `global-skill-runtime-sync`，无 Modified）

## Impact

- 维护者：修改 `scripts/chrome-agent-runtime.mjs` / `scripts/chrome-agent-cli.mjs` / `skills/chrome-agent/SKILL.md` 后，可从 `AGENTS.md` §3 一跳到达同步 playbook，并按 Case 6 手动同步，无需逆向代码。
- Agent：ahead-of-origin 场景不再需要从 cli.mjs 逆向推导同步操作；installed-hash 语义明确，避免误判「已同步」。
- 其它机器 / session：行为不变（仍依赖 push 后的 behind auto-update 路径）。
- 风险：极低——纯文档改动，不触发 C4（引擎版本同步）、C9（测试义务）等硬约束。

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：`repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
  - 项目页（上下文输入）：`docs/playbooks/chrome-agent-global-install.md`、`AGENTS.md`、`skills/chrome-agent/SKILL.md`
  - 回写目标：`docs/playbooks/chrome-agent-global-install.md`（Case 6 + ahead 行 + hash 小节）、`AGENTS.md`（§3 治理条目 + §11 必读行）
