# Writeback

## 回写摘要

- **change**: `external-cli-routing`
- **回写结论**: ✅ 全部回写目标已执行（spec 回填顶层 + 5 处项目文档已就地修改 + C10 全局副本已同步）
- **关键结果**: 新增路由层 spec `external-cli-routing`，将"目标平台命中外部 CLI 清单（Twitter/Reddit/小红书/B站/Facebook/Instagram/V2EX/YouTube/GitHub）时优先走非侵入式外部 CLI，否则走 chrome-agent 引擎链"确立为可验证行为契约；零代码改动、零引擎/能力注册表污染、零 strategy frontmatter 改动。

## Capability / Spec 增量摘要

| Capability | 变更类型 | 对应 spec 文件 | 增量摘要 |
| --- | --- | --- | --- |
| `external-cli-routing` | New | `openspec/specs/external-cli-routing/spec.md`（本次回填） | 路由层决策能力：4 个 ADDED Requirements — `platform-precheck-gate`（skill Intent Routing 前置平台判断）/ `external-cli-priority-on-match`（9 平台→CLI 映射 + 非侵入式优先）/ `engine-chain-fallback`（外部 CLI 不可用/失败/需浏览器能力时降级引擎链）/ `external-cli-routing-boundaries`（不进引擎注册表、不进 4 维模型 A 轴、不改 strategy frontmatter、SSOT 单一）。定位为治理层 spec（与 `governance/` 域同层），不进 `capability-registry.yaml`。 |

## 验证结论与证据入口

| 验证维度 | 结论 | 证据入口 |
| --- | --- | --- |
| Spec-to-Implementation | ✅ 4/4 requirement、12/12 scenario 全覆盖 | `verification.md` → Spec-to-Implementation Coverage 节 |
| Task-to-Evidence | ✅ 11/11 实现+收敛任务有证据 | `verification.md` → Task-to-Evidence Coverage 节 |
| 边界自检 | ✅ 5/5 通过（注册表/§2/frontmatter/loader/SSOT 均 clean） | `verification.md` → 关键证据入口（边界自检 1–5） |
| C10 全局同步 | ✅ skill 副本 identical + installed-hash == HEAD | `verification.md` → 关键证据入口（C10 同步 diff / installed-hash） |
| J3 测试完备 | N/A（纯 `.md` 改动，无新增代码模块） | `verification.md` → 验证结论 |

## 回写目标与字段映射

| 目标页 | 同步字段/区块 | 回写内容 |
| --- | --- | --- |
| `openspec/specs/external-cli-routing/spec.md` | 整文件（新增） | 从 `openspec/changes/external-cli-routing/specs/external-cli-routing/spec.md` 回填到顶层 specs/ |
| `AGENTS.md` §3 | 新增"外部能力路由（External CLI 优先）"小节 | 9 平台路由表 + 根因（侵入式 vs 非侵入式）+ 未命中处理 + 维护说明 + spec 指针 |
| `skills/chrome-agent/SKILL.md` | Intent Routing 顶部新增 `### Platform Pre-check` | 三分支判断（命中→外部 CLI / 需浏览器能力→跳过 / 未命中→intent routing）+ spec 指针 |
| `~/.agents/skills/chrome-agent/SKILL.md` | C10 全局副本同步 | 与仓库源完全一致 |
| `sites/strategies/x.com/strategy.md` | Overview 段首句后 | twitter-cli 优先指针 + §3 引用（frontmatter 不动） |
| `docs/playbooks/fallback-escalation.md` | 文件开头前置说明 | 外部 CLI 优先于引擎 escalation chain |
| `docs/playbooks/authenticated-sessions.md` | 会话复用段前 | 外部 CLI（非侵入式）优先于 Scrapling session 复用 |

## 回写执行结果

| 目标页 | 执行结果 | 执行时间 | 执行人 | 结果说明/链接 |
| --- | --- | --- | --- | --- |
| `openspec/specs/external-cli-routing/spec.md` | ⏳ 待 task 4.3 执行 | — | — | 见下方 task 4.3 |
| `AGENTS.md` §3 | ✅ 成功 | 2026-07-21 | apply session | `git status`: `M AGENTS.md`；9 平台行就位 |
| `skills/chrome-agent/SKILL.md` | ✅ 成功 | 2026-07-21 | apply session | `grep -c "^### Platform Pre-check" = 1` |
| `~/.agents/skills/chrome-agent/SKILL.md` | ✅ 成功 | 2026-07-21 | apply session | `diff -q` = identical（C10 同步） |
| `~/.agents/scripts/.chrome-agent-installed-hash` | ✅ 成功 | 2026-07-21 | apply session | hash == `git rev-parse HEAD` (4b9376b...) |
| `sites/strategies/x.com/strategy.md` | ✅ 成功 | 2026-07-21 | apply session | `git status`: `M`；frontmatter preferred 未变 |
| `docs/playbooks/fallback-escalation.md` | ✅ 成功 | 2026-07-21 | apply session | `git status`: `M`；前置说明在 escalation 图前 |
| `docs/playbooks/authenticated-sessions.md` | ✅ 成功 | 2026-07-21 | apply session | `git status`: `M`；指针在会话复用段前 |

## 回写前置条件

- [x] 已读取 `spec_standard_ref`（`engine-registry/spec.md`、`governance/governance.md` — 均有内容，参照未修改）
- [x] `verification.md` 已生成且无阻塞项（PASS，4/4 requirement 覆盖）
- [x] 回写目标页已确认存在且可编辑（5 处文档 + 全局副本均 baseline 确认）
- [x] capability/spec 增量摘要已核对 proposal 与 specs 一致（New: `external-cli-routing`，无 Modified）

## 不回写的内容

- 不复制完整 `proposal.md`、`design.md`、`specs/*/spec.md`、`tasks.md` 正文（仅 spec.md 本身回填顶层，其余 change artifacts 留在 `openspec/changes/external-cli-routing/`）
- 不写与本次 change 无关的历史信息
- 不在项目文档中复制平台路由表（SSOT 单一：表只在 `AGENTS.md` §3，skill/strategy/playbook 仅指针）
- 不回写 agent-reach skill 内容（外部维护，本仓库不复制其平台清单实现）
