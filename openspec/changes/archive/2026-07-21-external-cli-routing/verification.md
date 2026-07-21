# Verification

## 验证结论

**✅ PASS** — `external-cli-routing` spec 的 4 个 ADDED Requirements 全部落地，5 处文档改动完成，C10 全局同步与 installed-hash 刷新均通过，边界自检（5 条）全部满足。无 spec 缺口、无未完成任务、无遗留阻塞项。本 change 为纯文档治理，无新增 `.py`/`.mjs` 代码模块，J3 测试完备检查不适用。

## Spec-to-Implementation Coverage

| Spec Requirement | 落地位置 | 覆盖状态 |
|------------------|----------|----------|
| `platform-precheck-gate` | `skills/chrome-agent/SKILL.md` → `### Platform Pre-check (before intent routing)` | ✅ 3 scenario 全覆盖（in-list / not-in-list / ambiguous） |
| `external-cli-priority-on-match` | `AGENTS.md` §3 路由表（9 平台 × CLI × 需浏览器 × 说明）+ skill Pre-check 指示语 | ✅ 2 scenario 覆盖（prefer-over-cdp / requires-browser-session 区分） |
| `engine-chain-fallback` | `skills/chrome-agent/SKILL.md` Pre-check fallback 子句 + `docs/playbooks/fallback-escalation.md` 前置说明 | ✅ 2 scenario 覆盖（cli-unavailable / task-requires-browser） |
| `external-cli-routing-boundaries` | 5 条边界由下方"边界自检"独立验证 | ✅ 5 scenario 全覆盖 |

### Scenario 验证位置明细

- `target-platform-in-external-cli-list` / `target-platform-not-in-list` / `ambiguous-target` → skill Pre-check 段三个 bullet（if-yes / needs-browser / not-in-list-or-ambiguous）
- `prefer-external-cli-over-chrome-cdp` → skill Pre-check "non-intrusive" 说明 + AGENTS.md §3 根因说明
- `external-cli-requires-browser-session` → AGENTS.md §3 表"需浏览器?"列 + authenticated-sessions.md 指针（区分"借用凭证代发 API"与"侵入式接管"）
- `external-cli-unavailable` → skill Pre-check "fallback when unavailable" + fallback-escalation.md 前置说明
- `task-requires-browser-capability` → skill Pre-check 第二 bullet（needs browser-only capabilities）
- `external-cli-not-in-engine-registry` → 边界自检 1（grep clean）
- `routing-table-not-duplicated` → 边界自检 5（skill/strategy/playbook 表格计数为 0）
- `strategy-frontmatter-unaffected` → 边界自检 3（preferred 仍为 scrapling-fetch / chrome-cdp）
- `capability-not-in-section-2` → 边界自检 2（§2 无 external-cli-routing）

## Task-to-Evidence Coverage

| Task | 证据 | 状态 |
|------|------|------|
| 1.1 requirement→文档映射 | 见上方 Spec-to-Implementation 表 | ✅ |
| 1.2 baseline 同步确认 | `diff` EXIT 0（propose 阶段记录） | ✅ |
| 2.1.1 AGENTS.md §3 小节 | git: `M AGENTS.md`；9 平台行 + 根因 + 维护说明 | ✅ |
| 2.2.1 skill Pre-check 段 | `grep -c "^### Platform Pre-check" = 1` | ✅ |
| 2.3.1 全局副本同步 | `diff -q` = identical | ✅ |
| 2.3.2 installed-hash 刷新 | hash == `git rev-parse HEAD` = MATCH | ✅ |
| 2.4.1 x.com Overview 指针 | git: `M sites/strategies/x.com/strategy.md`；frontmatter 未变 | ✅ |
| 2.5.1 fallback-escalation 前置说明 | git: `M docs/playbooks/fallback-escalation.md` | ✅ |
| 2.6.1 authenticated-sessions 指针 | git: `M docs/playbooks/authenticated-sessions.md` | ✅ |
| 3.1 覆盖矩阵 | 本文件 Spec-to-Implementation 节 | ✅ |
| 3.2 边界自检检查点 | 下方"关键证据"节 5 条 grep | ✅ |

## 关键证据入口

| 证据类型 | 证据路径/链接 | 对应 requirement/task |
|----------|---------------|----------------------|
| git 改动集 | `git status --short` → 5 个 `M` 文件 + `?? openspec/changes/external-cli-routing/` | tasks 2.1.1–2.6.1 |
| §3 路由表 | `AGENTS.md` §3 "外部能力路由" 小节 | external-cli-priority-on-match / routing-boundaries(SSOT) |
| skill Pre-check | `skills/chrome-agent/SKILL.md` L61 `### Platform Pre-check` | platform-precheck-gate / engine-chain-fallback |
| C10 同步 diff | `diff skills/chrome-agent/SKILL.md ~/.agents/skills/chrome-agent/SKILL.md` → identical | task 2.3.1 |
| installed-hash | `~/.agents/scripts/.chrome-agent-installed-hash` == `git rev-parse HEAD` (4b9376b...) | task 2.3.2 |
| 边界自检 1 | `grep -iE "twitter-cli\|opencli\|agent-reach\|external-cli-routing\|yt-dlp" configs/{engine-registry.json,capability-registry.yaml} scripts/pipeline/pipeline/registry.py` → clean | routing-boundaries 边界 1 |
| 边界自检 2 | `awk '/## 2. Capability/,/## 3./' AGENTS.md \| grep external-cli-routing` → empty | routing-boundaries 边界 2 |
| 边界自检 3 | x.com strategy frontmatter `preferred: scrapling-fetch` / `preferred: chrome-cdp`（无 external:） | routing-boundaries 边界 3 |
| 边界自检 4 | `grep -iE "twitter\|opencli\|external.cli\|agent.reach" scripts/lib/strategy_loader.py` → clean | routing-boundaries 边界 4 |
| 边界自检 5 | skill/strategy/playbook 中 `\| Twitter/X` 等表格行计数 = 0（仅指针） | routing-boundaries 边界 5 |

## 缺口与阻塞项

**无缺口、无阻塞项。**

- Spec 覆盖：4/4 requirement、12/12 scenario 全部有对应落地位置
- 任务完成：11/11 实现+收敛任务完成（task 4.2 writeback 生成、4.3 回写执行为后续步骤）
- 边界自检：5/5 通过
- J3 测试完备：不适用（纯 `.md` 改动，无新增代码模块）
- 遗留：task 4.2（writeback.md 生成）、task 4.3（spec 回填顶层）待执行，见 writeback 阶段
