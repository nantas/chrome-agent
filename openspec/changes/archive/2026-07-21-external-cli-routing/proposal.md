# Proposal

## 问题定义

chrome-agent 当前对社交平台（Twitter/X、Reddit、小红书、Facebook、Instagram 等）以及 GitHub / YouTube 的内容获取，**唯一集成的浏览器路径是 chrome-cdp**。实证暴露三个问题：

1. **侵入式体验断层**：chrome-cdp 经 remote debugging 接口接管用户的活动 Chrome tab，每次首次访问新 target 触发 Chrome "Allow debugging" 权限弹窗，打断用户正常使用浏览器。而同类的 login-wall 内容，外部 CLI（agent-reach 路由的 `twitter-cli` / `opencli`，以及 `gh` / `yt-dlp`）采用**非侵入式**范式——借用凭证（cookie/token）、用自有网络栈发请求，完全不接管浏览器、零弹窗打扰。twitter-cli 甚至无需浏览器运行（纯 cookie HTTP）。两者不在同一体验档次。

2. **路由判断缺失**：chrome-agent skill 的 Intent Routing 只有意图分支（fetch / explore / crawl），**没有平台维度的前置判断**。外部 agent 调用 chrome-agent 工作流时，即便目标平台（如 reddit）有更优的外部 CLI 路径，也会被直接路由进 chrome-cdp，承受不必要的侵入式体验与 SPA DOM 脆弱性。

3. **外部 CLI 零文档散落**：`gh` / `yt-dlp` 已是本仓库事实上的标准外部工具（分别服务 GitHub / YouTube），但**未在任何治理文档中登记**；agent-reach 路由的社交平台 CLI 更是完全在仓库视野之外。无 SSOT 声明"哪些平台该优先走外部 CLI"，也无 fallback 边界。

本 change 将"平台→外部 CLI 优先路由"确立为一项**可验证的路由层决策能力**，并落地配套文档，使外部 agent 能在进入 chrome-agent 引擎链之前正确分流。

## 范围边界

**In scope**:

- 新增路由层 spec `external-cli-routing`，锁定决策行为契约（命中清单→外部 CLI 优先；失败→fallback 引擎链；未命中→直接引擎链）
- `AGENTS.md` §3 新增"外部能力路由"小节，作为平台→外部 CLI 路由表的**文档层 SSOT**（含平台 / CLI / 是否需浏览器 / 说明 四列）
- `skills/chrome-agent/SKILL.md` Intent Routing 顶部新增 Platform Pre-check gate（C10 同步全局副本）
- `sites/strategies/x.com/strategy.md` Overview 段补指针（**frontmatter 不变**——外部路由发生在引擎选择之前，不应污染 `engine_preference` 字段，否则被 `chrome-agent-cli.mjs:637` 当未知引擎误读）
- `docs/playbooks/fallback-escalation.md`、`docs/playbooks/authenticated-sessions.md` 各补一行指针（不重复路由表，仅引用 AGENTS.md §3）

**Out of scope**（明确排除，避免形状污染）:

- ❌ 不把外部 CLI 注册进 `configs/engine-registry.json` / `configs/capability-registry.yaml` / `scripts/pipeline/pipeline/registry.py`——外部 CLI 是 shell-out 工具（与 `gh`/`yt-dlp` 同类），非抓取引擎，返回结构化记录而非页面，不满足 convert 的输入契约（D 轴：rendered HTML / wikitext / API JSON）
- ❌ 不把 `external-cli-routing` 加入 `AGENTS.md` §2 Capability Framework（4 维模型 A 轴）——它是路由/治理层 spec，与 `governance/` 域同层，不进 `capability-registry.yaml`，故不触发 `capability-registry` spec 的 "§2 必须有行" doctor 检查
- ❌ 不内化 agent-reach 源码到本仓库——agent-reach 是外部维护的能力路由器，本仓库只引用其平台清单，不复制实现
- ❌ 不修改 `strategy_loader.py`——外部路由不在策略解析层发生
- ❌ 不增加任何 Python/Node 代码——纯路由声明 + spec + 文档

## Capabilities

### New Capabilities

- `external-cli-routing`: 路由层决策能力——目标平台命中外部 CLI 清单（Twitter/Reddit/小红书/B站/Facebook/Instagram/V2EX/YouTube/GitHub）时，chrome-agent skill 优先路由到外部 CLI（agent-reach / `gh` / `yt-dlp`），不进入 fetch/explore/crawl intent routing；外部 CLI 不可用或失败时 fallback 到 chrome-agent 内部引擎链；将生成 `specs/external-cli-routing/spec.md`

### Modified Capabilities

_无。本 change 不修改任何 A 轴业务能力（fetch / convert / extract / discover / assemble）的既有 requirement。_

## Capabilities 待确认项

- [x] 能力清单已与用户确认（grill 会话达成共识：agent-reach 能力形状与 chrome-agent 4 维模型不匹配，正确纳入形式为外部 CLI shell-out + 路由层 spec，不内化为引擎/能力）
- [x] capability 归属已确认（`external-cli-routing` 定位为治理/路由层 spec，参照 `governance/` 域先例，不进 4 维模型 A 轴）

## Impact

**受影响文档（5 处）**:

| 文档 | 改动类型 | C10 同步 |
|------|----------|----------|
| `AGENTS.md` §3 | 新增小节（路由表 SSOT） | — |
| `skills/chrome-agent/SKILL.md` | Intent Routing 顶部加 Platform Pre-check | ✅ 需同步 `~/.agents/skills/chrome-agent/SKILL.md` |
| `sites/strategies/x.com/strategy.md` | Overview 段补指针（frontmatter 不动） | — |
| `docs/playbooks/fallback-escalation.md` | 开头补前置说明 | — |
| `docs/playbooks/authenticated-sessions.md` | 补指针 | — |

**受影响规范（1 处新增）**:

- `openspec/specs/external-cli-routing/spec.md` — 新增路由层行为契约（归档时回填顶层 specs/）

**不受影响**:

- 代码：`scripts/` 下零改动（不碰 cli.mjs / strategy_loader / engine 逻辑）
- 注册表：`configs/engine-registry.json` / `configs/capability-registry.yaml` / `registry.py` 零改动
- 其它冻结 spec：零改动（仅参照 `engine-registry`、`governance/governance.md`，不修改其 requirement）
- strategy frontmatter：零改动（x.com 只改正文）

**外部依赖**:

- agent-reach skill（`~/.agents/skills/agent-reach/SKILL.md`）维护平台清单与后端选择逻辑；本仓库不复制其内容，路由表的平台范围以 agent-reach 当前支持为准（15 平台，详见其 SKILL）。agent-reach 平台清单变更时，`AGENTS.md` §3 路由表需同步（人工维护，非自动）

**约束满足**:

- C7（策略注册）：不触发——未新增策略
- C9（测试义务）：不触发——未改 `scripts/lib/` / `pipeline/phases/` / `extraction/`
- C10（全局 skill 同步）：触发——`skills/chrome-agent/SKILL.md` 改动需同步全局副本 + 刷新 installed-hash
- C11（能力注册同步）：不触发——`external-cli-routing` 不进 `capability-registry.yaml`

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页（参照，不修改）：`openspec/specs/engine-registry/spec.md`、`openspec/specs/governance/governance.md`
- 已确认项目页（本次产出/修改）：见上方 Impact 表 5 处
- 已确认回写目标：`openspec/specs/external-cli-routing/spec.md`（新增）+ 5 处项目文档；C10 全局同步路径见 `docs/playbooks/chrome-agent-global-install.md` Case 6
