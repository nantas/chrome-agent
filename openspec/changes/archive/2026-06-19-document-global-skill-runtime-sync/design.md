# Design

## Context

本 change 是纯文档型 change，规范真源为 `specs/global-skill-runtime-sync/spec.md`。被固化的契约已作为既成事实存在于 `scripts/chrome-agent-cli.mjs`（`runAutoUpdateGlobalFiles` / `runGitFetchCheck` / `runTrackedFilesCheck`，约 3500-3651 行），本设计不改变其行为，只决定**如何在 `docs/playbooks/chrome-agent-global-install.md` 与 `AGENTS.md` 中表述该契约**。

被填补的三处文档缺口（对应 spec 的 ADDED Requirements）：

| Spec Requirement | 文档落点 |
|---|---|
| `tracked-files-registry-documented` | playbook「Tracked files for auto-update」小节 + Case 6 内联 |
| `auto-update-behind-origin-documented` | playbook「Version Freshness Check」behind 两条（已部分存在，规范措辞） |
| `ahead-of-origin-sync-gap-documented` | playbook「Version Freshness Check」新增 ahead 行 |
| `manual-sync-procedure-documented` | playbook 新增「Case 6: Manually sync global copies」 |
| `installed-hash-semantics-documented` | playbook 新增小节「Installed Hash Semantics」 |
| `agents-md-governance-anchor` | `AGENTS.md` §3 新增治理条目 + §11 必读表新增一行 |

## Goals / Non-Goals

**Goals:**

- 让维护者修改 tracked file 后，能从 `AGENTS.md` §3 一跳到达 playbook 的 Case 6 手动同步流程，无需逆向 `chrome-agent-cli.mjs`。
- 把 ahead-of-origin 的同步盲区显式文档化，消除「doctor=ok 但全局副本已过时」的误导。
- 说清 installed-hash 记录的是 commit SHA（非文件内容 hash），以及手动同步后必须刷新的义务。

**Non-Goals:**

- 不新增 `chrome-agent sync` 子命令（留作未来独立 change；引入它将触发 cli 改动 + C9 测试义务）。
- 不改动 `chrome-agent-cli.mjs` 的 doctor / auto-update 代码。
- 不修改 `skills/chrome-agent/SKILL.md` 的 `global_skill_updated` 标志与 reload 提示。
- 不覆盖其它机器的同步路径——它们仍依赖 `git push` 后的 behind auto-update。

## Decisions

**D1：playbook 采用 Case 6 而非独立小节承载手动同步。**
现有 playbook 已是「Case 1–5」的决策树结构（fresh install / 已存在 / env 缺失 / env 已对 / env 冲突）。新增「Case 6: Manually sync global copies」与现有 Case 编号体系一致，operator 可在同一个决策点序列里找到它。手动同步命令固定为 spec `manual-sync-procedure-documented` 的四步（cp runtime + chmod、cp skill、写 HEAD 到 hash、doctor 验证 + reload skill）。

**D2：ahead-of-origin 在 Version Freshness 段补一行，而非另立小节。**
behind / network-failure / detached-HEAD 三条已并列于该段，ahead 是同一维度（git fetch 比较结果）的第四种，补一行即可保持清单完整，无需结构变动。

**D3：installed-hash 单列「Installed Hash Semantics」小节。**
它横跨 Case 6 与 Version Freshness 两处引用，单列小节避免重复，且直接对应 spec 的 `installed-hash-semantics-documented`。

**D4：AGENTS.md §3 治理条目紧贴 C4（引擎版本同步）。**
两者同属「修改 X 后必须同步 Y」类硬约束，并列放置认知成本最低。措辞为「修改 tracked files 后须同步全局副本并刷新 installed-hash」，并附 playbook 链接。§11 必读表新增一行：任务类型「改 runtime/cli/SKILL.md」→ 必读 `docs/playbooks/chrome-agent-global-install.md`。

**D5：spec 采用文档型 requirement 范式（SHALL 表述文档内容）。**
参照既有 `docs-tech-stack-dependency-graph` capability 范式：requirement 描述「文档 SHALL 包含什么」，scenario 以 operator/agent 视角验证。避免把 spec 写成「代码 SHALL 改成 X」（本 change 不改代码）。

## Risks / Migration

- **风险：playbook 与代码漂移。** 若未来 `runAutoUpdateGlobalFiles` 的 tracked files 清单或 hash 语义改变，文档可能过时。缓解：本 spec 的 `tracked-files-registry-documented` 与 `installed-hash-semantics-documented` 把清单与语义固化为契约，未来代码改动应回写文档。
- **风险：AGENTS.md §3 条目增多导致冗长。** 缓解：D4 使其紧贴同类 C4 条目，单条、带链接，不展开细节。
- **迁移：无。** 纯新增文档段落，不删除/重写既有内容（Version Freshness 的 behind 两条仅规范措辞，不改变语义）。无破坏性，无需迁移既有 operator 习惯。
- **风险：极低。** 不触发 C4（引擎版本同步）、C9（测试义务）、C1-C8 任何硬约束（不改 scripts/configs/sites，不改 Python/Node 行为）。
