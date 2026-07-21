# Design

## Context

chrome-agent skill 的 Intent Routing（`skills/chrome-agent/SKILL.md`）当前只有意图分支（fetch / explore / crawl），**没有平台维度的前置判断**。外部 agent 调用 chrome-agent 时，即便目标平台（Twitter/Reddit/小红书/GitHub/YouTube）存在更优的非侵入式外部 CLI 路径，也会被直接路由进 chrome-cdp，承受 "Allow debugging" 弹窗打扰与 SPA DOM 脆弱性。

实证（本机测试）：`twitter search` / `opencli reddit read` / `opencli xiaohongshu note` 均一次返回结构化记录（id/text/score/likes/comments + xsec_token），而 chrome-cdp 接管 tab 的范式本质是侵入式的。`global-workflow-skill` spec 目录为空，说明 skill 路由行为从未被 spec 化——本次顺势用 `external-cli-routing` spec 锁定决策行为。

本 design 以 `specs/external-cli-routing/spec.md` 的 4 个 ADDED Requirements 为输入（platform-precheck-gate / external-cli-priority-on-match / engine-chain-fallback / external-cli-routing-boundaries），说明如何落地。

## Goals / Non-Goals

**Goals:**

- 让外部 agent 在进入 chrome-agent 引擎链之前，能基于目标平台判断是否该走外部 CLI（满足 `platform-precheck-gate`）
- 提供唯一的路由表 SSOT（`AGENTS.md` §3），其余文档只加指针（满足 `external-cli-routing-boundaries` 第 5 条 SSOT 单一）
- 保持外部 CLI 在引擎/能力注册表、strategy frontmatter、4 维模型之外（满足 `external-cli-routing-boundaries` 第 1–4 条）
- 失败时正确 fallback 到既有引擎链，不破坏 scrapling-first（满足 `engine-chain-fallback`）

**Non-Goals:**

- 不内化 agent-reach 实现、不写任何 Python/Node 路由代码（纯文档 + spec）
- 不自动同步 agent-reach 平台清单变更（人工维护 `AGENTS.md` §3）
- 不为外部 CLI 增加 preflight / doctor 检查（外部 CLI 可用性由 agent-reach 自己的 doctor 负责，本仓库不重复）
- 不修改 chrome-agent CLI 命令行接口（`fetch/explore/crawl` 子命令不变）

## Decisions

### D1: 路由判断点 = skill 路由层，不是 strategy frontmatter

**决策**：外部 CLI 分流发生在 chrome-agent skill 的 Intent Routing **之前**（新增 Platform Pre-check gate），不进入 site strategy 的 `engine_preference` 字段。

**理由**：
- `engine_preference.preferred` 被 `scripts/chrome-agent-cli.mjs:637` 当作引擎 ID 解析。若写入 `external:twitter-cli` 会被当成未知引擎，行为不可预测。
- 外部路由是"是否进 chrome-agent 引擎链"的前置判断，逻辑层级高于"进引擎链后选哪个引擎"。把前置判断塞进引擎选择字段是层级错配。
- x.com strategy 的 frontmatter 保持原值（`scrapling-fetch` / `chrome-cdp`），仅在 Overview 正文补指针，满足 `external-cli-routing-boundaries` 第 3 条。

### D2: SSOT 分层 — spec 是行为契约真源，AGENTS.md §3 是文档投影

**决策**：行为契约（ SHALL/MUST 规则、scenario）真源是 `specs/external-cli-routing/spec.md`；平台→CLI 映射表的文档层 SSOT 是 `AGENTS.md` §3。两者不重复：spec 不写死具体平台清单（平台会随 agent-reach 演变），只锁定"清单位置在 AGENTS.md §3 + 命中时路由"的行为；AGENTS.md §3 维护具体表格。

**理由**：spec 应稳定（行为规则不变），表格会变（agent-reach 新增平台时 AGENTS.md §3 同步）。分离避免每次平台增减都要改冻结 spec。

### D3: external-cli-routing 定位为治理层 spec，不进 4 维模型

**决策**：`external-cli-routing` 不登记进 `configs/capability-registry.yaml`、不进 `AGENTS.md` §2 Capability Framework，仅落 §3 Governance Rules。

**理由**：
- `capability-registry` spec 的 doctor 检查（第 32 行）只验证 `registry.yaml` 中**已声明**条目需在 §2 有行。external-cli-routing 不进 registry.yaml → 不触发该检查。
- 这与 `governance/` 域（governance.md / handoff.md / output.md）的处理一致——它们也是 spec 但不在 §2 A 轴表里。
- 避免污染 4 维模型（A 轴 = fetch/convert/extract/discover/assemble 是业务能力；路由是调度层，不是业务能力）。

### D4: 5 处文档改动的角色分工

| 文档 | 角色 | 改动量 |
|------|------|--------|
| `AGENTS.md` §3 | 路由表文档层 SSOT | 新增完整小节（表格 + 规则） |
| `skills/chrome-agent/SKILL.md` | 外部入口执行点 | Intent Routing 顶部加 Platform Pre-check 段（C10 同步全局副本） |
| `sites/strategies/x.com/strategy.md` | 单平台实例 | Overview 段补一句指针 |
| `docs/playbooks/fallback-escalation.md` | 引擎链文档 | 开头补"外部 CLI 优先于本链"一句 |
| `docs/playbooks/authenticated-sessions.md` | 认证会话文档 | 补"外部 CLI 优先于 session 复用"一句 |

后三处是**指针**（引用 §3，不复制表格），满足 SSOT 单一（D2）。

### D5: 不增加任何 preflight / 代码

**决策**：不为外部 CLI 在本仓库增加 doctor 检查或 preflight 脚本。

**理由**：外部 CLI 可用性已由 agent-reach 自己的 `doctor --json` 负责。本仓库若再加一层检查 = 重复 + 漂移源。skill 的 Platform Pre-check 只做"平台是否在清单内"的静态判断，不做"CLI 是否可用"的运行时探测——后者交给调用方按 agent-reach doctor 结果处理，失败时走 `engine-chain-fallback`。

## Risks / Migration

**风险 R1: agent-reach 平台清单与本仓库 §3 表漂移**
- agent-reach 升级新增平台时，`AGENTS.md` §3 表不会自动更新。
- **缓解**：§3 表头注明"平台范围以 agent-reach 当前支持为准"；归档 verification 检查表与 agent-reach SKILL 一致。接受人工维护成本（平台清单低频变动）。

**风险 R2: 外部 CLI 失败时的降级路径不被调用方遵循**
- spec 规定了 fallback 行为，但 skill 是 markdown 指令，依赖 agent 正确执行。
- **缓解**：skill 的 Platform Pre-check 段显式写明"外部 CLI 不可用/失败 → 进入下方 Intent Routing"；fallback-escalation.md 开头也补前置说明。双重提示降低遗漏概率。这是文档治理 change 的固有局限，可接受。

**风险 R3: C10 同步遗漏导致全局 skill 副本漂移**
- 改 `skills/chrome-agent/SKILL.md` 后若忘记同步 `~/.agents/skills/chrome-agent/SKILL.md`，全局调用的 agent 读到旧版。
- **缓解**：tasks 明确列出 C10 同步步骤 + installed-hash 刷新；verification 用 `diff` 确认两份一致。

**迁移**：无破坏性迁移。本 change 纯增量（新增 spec + 新增文档小节 + 指针），不修改任何既有行为或契约。现有 fetch/explore/crawl 调用对清单外平台行为完全不变。
