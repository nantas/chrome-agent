# Tasks

> 本 change 为纯文档/治理 change（无 `.py`/`.mjs` 代码改动），核心实现任务均为文档编辑，按 openspec 规则不强制 TDD vertical slice，但每个任务均配可验证的完成标准（引用 `specs/external-cli-routing/spec.md` 的 requirement / scenario）。spec/proposal/design/binding 已在 propose 阶段产出，归档时 specs/ 回填顶层。

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `specs/external-cli-routing/spec.md` 的 4 个 ADDED Requirements（platform-precheck-gate / external-cli-priority-on-match / engine-chain-fallback / external-cli-routing-boundaries）各自对应的落地文档
  - platform-precheck-gate → `skills/chrome-agent/SKILL.md`
  - external-cli-priority-on-match → `AGENTS.md` §3 路由表 + skill 指示语
  - engine-chain-fallback → `skills/chrome-agent/SKILL.md` + `docs/playbooks/fallback-escalation.md`
  - external-cli-routing-boundaries → 5 处文档的边界自检（不进 registry / 不改 frontmatter / SSOT 单一）
- [x] 1.2 确认 C10 tracked 源与全局副本当前同步（baseline）
  - 验证：`diff skills/chrome-agent/SKILL.md ~/.agents/skills/chrome-agent/SKILL.md` 应无差异（已确认 EXIT 0）
  - 记录当前 `git rev-parse HEAD` 供 installed-hash 刷新对比

## 2. 核心实现任务

### 2.1 `AGENTS.md` §3 新增"外部能力路由"小节（路由表 SSOT）

- [x] 2.1.1 在 `AGENTS.md` §3 Governance Rules 现有内容末尾、`## 4. Directory Governance` 之前，插入"外部能力路由（External CLI 优先）"小节
  - 内容：路由规则一句话 + 平台清单表（平台 / 外部 CLI / 需浏览器? / 说明 四列，9 个平台）+ 根因说明（侵入式 vs 非侵入式）+ 未命中处理
  - 覆盖 spec：`external-cli-priority-on-match`（映射表）、`external-cli-routing-boundaries`（SSOT 单一）
  - 验证：表格 9 行平台与 agent-reach SKILL 当前支持范围一致；小节位于 §3 末尾、§4 之前

### 2.2 `skills/chrome-agent/SKILL.md` Intent Routing 顶部加 Platform Pre-check

- [x] 2.2.1 在 `## Intent Routing` 标题下、`After doctor succeeds...` 之前，插入 `### Platform Pre-check (before intent routing)` 段
  - 内容：命中 AGENTS.md §3 清单 → 优先外部 CLI（非侵入式理由）；未命中/需浏览器能力 → 进入下方 intent routing；外部 CLI 失败 → fallback
  - 覆盖 spec：`platform-precheck-gate`、`engine-chain-fallback`、`external-cli-priority-on-match`
  - 验证：该段是 Intent Routing 的第一个子段；引用 AGENTS.md §3 为指针，不复制表格（满足 `external-cli-routing-boundaries` 第 5 条）

### 2.3 C10 全局副本同步

- [x] 2.3.1 将 `skills/chrome-agent/SKILL.md`（tracked 源）的改动同步到 `~/.agents/skills/chrome-agent/SKILL.md`（全局副本）
  - 验证：`diff skills/chrome-agent/SKILL.md ~/.agents/skills/chrome-agent/SKILL.md` EXIT 0
- [x] 2.3.2 刷新 `~/.agents/scripts/.chrome-agent-installed-hash` 至当前 `git rev-parse HEAD`
  - 验证：`cat ~/.agents/scripts/.chrome-agent-installed-hash` 等于 `git rev-parse HEAD`
  - 参照：`docs/playbooks/chrome-agent-global-install.md` Case 6

### 2.4 `sites/strategies/x.com/strategy.md` Overview 补指针

- [x] 2.4.1 在 `## Overview` 段首句后插入路由指针（引用 twitter-cli 优先 + AGENTS.md §3）
  - 覆盖 spec：`external-cli-routing-boundaries` 第 3 条（指针仅在正文，frontmatter 不动）
  - 验证：`engine_preference.preferred` 字段值未变（仍为 `scrapling-fetch` / `chrome-cdp`）；Overview 段含指向 §3 的引用

### 2.5 `docs/playbooks/fallback-escalation.md` 开头补前置说明

- [x] 2.5.1 在"引擎 escalation chain"图之前插入一句前置说明：外部 CLI 优先于本 escalation chain（命中 AGENTS.md §3 清单的平台先走外部 CLI，本链仅作 fallback）
  - 覆盖 spec：`engine-chain-fallback`
  - 验证：前置说明在 escalation chain 图之前；为指针引用，不复制平台表

### 2.6 `docs/playbooks/authenticated-sessions.md` 补指针

- [x] 2.6.1 在"会话复用"或"已验证案例"相关段补一句：外部 CLI（非侵入式，借用凭证代发 API）优先于 Scrapling session 复用路径
  - 覆盖 spec：`external-cli-priority-on-match`（区分"需登录态"与"侵入式接管"）
  - 验证：含指针引用 AGENTS.md §3；不复制表格

## 3. 收敛与验证准备

- [x] 3.1 整理 spec-to-implementation 覆盖矩阵（4 个 requirement × 5 处文档，标记每条 scenario 的验证位置）
- [x] 3.2 标记边界自检检查点（`external-cli-routing-boundaries` 的 5 条边界各对应一个 verification 检查）
  - 检查 1：`grep` 确认外部 CLI 标识未出现在 `configs/engine-registry.json` / `configs/capability-registry.yaml` / `registry.py`
  - 检查 2：确认 `AGENTS.md` §2 无 `external-cli-routing` 行项
  - 检查 3：确认 x.com strategy frontmatter 的 `preferred` 字段未含 `external:` 或 CLI 名
  - 检查 4：确认 `strategy_loader.py` 未新增外部 CLI 解析逻辑
  - 检查 5：确认路由表只在 §3，skill/strategy/playbook 仅指针

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成 `verification.md`（覆盖 spec-to-implementation 与 task-to-evidence，含 C10 同步 diff 证据、边界自检 grep 结果）
- [x] 4.2 基于 verification.md 结论生成 `writeback.md`（目标：`openspec/specs/external-cli-routing/spec.md` 回填 + 5 处文档状态确认）
- [x] 4.3 执行 writeback.md 中定义的回写目标（归档时：`specs/external-cli-routing/spec.md` → `openspec/specs/external-cli-routing/spec.md`），并记录可审计证据
