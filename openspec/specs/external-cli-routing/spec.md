# Specification Delta

## Capability 对齐（已确认）

- Capability: `external-cli-routing`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: 用户确认新增 `external-cli-routing` 作为路由层决策能力，定位为治理层 spec（与 `governance/` 域同层），不进入 4 维模型 A 轴、不进 `capability-registry.yaml`；无 Modified Capability。确认发生在 capability 归属演化之后（最初拟为纯文档治理，调研发现 `global-workflow-skill` spec 为空目录、skill 路由行为从未被 spec 化，故演化为新增路由层 spec 锁定决策行为）。

## 规范真源声明

- 本文件是 `external-cli-routing` capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写（`AGENTS.md` §3 路由表）不得替代本文件；本文件锁定行为契约，`AGENTS.md` §3 是其文档层投影

## ADDED Requirements

### Requirement: platform-precheck-gate

chrome-agent skill（仓库 tracked 源 `skills/chrome-agent/SKILL.md`）SHALL 在 Intent Routing（分发到 fetch / explore / crawl）之前，执行一次 Platform Pre-check：判断用户目标（URL 或平台描述）是否命中"外部 CLI 清单"中的平台。

外部 CLI 清单的文档层 SSOT 为 `AGENTS.md` §3 Governance Rules 的"外部能力路由"小节。命中判定 SHALL 基于该清单的平台列；清单覆盖范围以 agent-reach skill 当前支持的平台为准（Twitter/X、Reddit、小红书、B站、Facebook、Instagram、V2EX、YouTube、GitHub）。

Platform Pre-check SHALL 是 Intent Routing 的第一个前置步骤，先于任何 `chrome-agent fetch/explore/crawl` 命令的构造与执行。

#### Scenario: target-platform-in-external-cli-list
- **WHEN** 用户目标指向外部 CLI 清单内的平台（例如 `x.com` 搜索、`reddit.com` 帖子、`xiaohongshu.com` 笔记、`github.com` 仓库、`youtube.com` 视频）
- **THEN** skill SHALL 路由到该平台对应的外部 CLI（见 `external-cli-priority-on-match`），不构造 `chrome-agent fetch/explore/crawl` 命令

#### Scenario: target-platform-not-in-list
- **WHEN** 用户目标指向清单外的平台（例如某 MediaWiki 站点、某通用网页）
- **THEN** skill SHALL 跳过外部 CLI 分流，正常进入 Intent Routing（fetch / explore / crawl）

#### Scenario: ambiguous-target
- **WHEN** 用户目标无法明确判定平台归属（例如裸关键词搜索，无 URL、无平台提示）
- **THEN** skill SHALL 跳过外部 CLI 分流，进入 Intent Routing，不强制猜测平台

### Requirement: external-cli-priority-on-match

当 Platform Pre-check 命中外部 CLI 清单时，skill SHALL 优先指示用户/调用方使用该平台的外部 CLI，而非 chrome-agent 内部引擎。命中时的路由映射 SHALL 如下：

| 平台 | 外部 CLI | 优先级理由 |
|------|----------|-----------|
| Twitter/X | `twitter-cli`（命令 `twitter`） | 纯 cookie HTTP，非侵入式，无需浏览器 |
| Reddit | `opencli reddit`（或 `rdt` 备选） | 非侵入式（复用登录态代发 API，不接管 tab） |
| 小红书 | `opencli xiaohongshu` | 同上 |
| B站 | `bili` / `opencli bilibili` | bili-cli 无需登录 |
| Facebook / Instagram | `opencli facebook` / `opencli instagram` | 同上 |
| V2EX | 公开 API（`curl`） | 零配置 |
| YouTube | `yt-dlp` | 非侵入式 |
| GitHub | `gh` | 非侵入式，已是仓库标准工具 |

多后端平台（Twitter/Reddit/小红书/B站）的具体 active_backend SHALL 由 `agent-reach doctor --json` 运行时决定；skill 指示调用方参考 agent-reach skill 的后端选择逻辑，本 spec 不锁定具体后端命令。

#### Scenario: prefer-external-cli-over-chrome-cdp
- **WHEN** 命中清单且对应外部 CLI 在当前环境可用
- **THEN** skill SHALL 指示外部 CLI 作为首选路径，并在说明中标注"非侵入式"理由（借用凭证、自有网络栈、不接管浏览器、不触发 Allow debugging 弹窗）

#### Scenario: external-cli-requires-browser-session
- **WHEN** 命中的外部 CLI 后端需要 Chrome 登录态（如 opencli 系），但属于"借用凭证代发 API"而非"接管 tab"
- **THEN** skill SHALL 在指示中区分"需浏览器登录态"与"侵入式接管"，不将两者混为一谈

### Requirement: engine-chain-fallback

当且仅当以下情形之一发生时，skill SHALL 回退（fallback）到 chrome-agent 内部引擎链（scrapling-first → chrome-cdp，见 `docs/playbooks/fallback-escalation.md`）：

1. 命中的外部 CLI 在当前环境不可用（未安装、未登录、doctor 报失败）
2. 外部 CLI 执行失败且重试链（见 agent-reach skill references）已耗尽
3. 外部 CLI 无法满足任务需求（例如需要截图、页面布局分析、浏览器交互等外部 CLI 不提供的能力）

Fallback SHALL 保持 scrapling-first 原则（chrome-cdp 仍是引擎链的最后手段，而非首选）。

#### Scenario: external-cli-unavailable
- **WHEN** 命中平台的外部 CLI 未安装或 doctor 报告该后端不可用
- **THEN** skill SHALL 回退到 chrome-agent fetch/explore/crawl，并在说明中记录"外部 CLI 不可用"作为降级原因

#### Scenario: task-requires-browser-capability
- **WHEN** 任务明确需要浏览器独有能力（截图 / DOM 交互 / 页面级快照 / 写操作）
- **THEN** skill SHALL 跳过外部 CLI 分流（即使平台在清单内），直接进入 chrome-agent 引擎链，因外部 CLI 是只读字段抽取器，不提供这些能力

### Requirement: external-cli-routing-boundaries

本路由能力 SHALL 遵守以下边界，避免污染 chrome-agent 的 4 维业务模型与引擎治理：

1. **不进引擎注册表**：外部 CLI（agent-reach / `gh` / `yt-dlp`）SHALL NOT 出现在 `configs/engine-registry.json`、`configs/capability-registry.yaml`、`scripts/pipeline/pipeline/registry.py` 中。它们是 shell-out 工具，非抓取引擎，返回结构化记录而非页面，不满足 convert 的 D 轴输入契约（rendered HTML / wikitext / API JSON）。
2. **不进 4 维模型 A 轴**：`external-cli-routing` capability SHALL NOT 在 `AGENTS.md` §2 Capability Framework 中登记行项。它定位为治理/路由层 spec（与 `governance/` 域同层），仅落在 `AGENTS.md` §3 Governance Rules。
3. **不修改 strategy frontmatter**：站点策略（如 `sites/strategies/x.com/strategy.md`）的 `engine_preference.preferred` 字段 SHALL NOT 使用 `external:` 前缀或任何外部 CLI 标识，因该字段被 `scripts/chrome-agent-cli.mjs:637` 当作引擎 ID 解析。外部路由指针 SHALL 仅出现在 strategy 正文（如 Overview 段），不进入 frontmatter。
4. **不被 strategy_loader 特殊解析**：`scripts/lib/strategy_loader.py` SHALL NOT 增加针对外部 CLI 的字段解析逻辑。
5. **SSOT 单一**：平台→外部 CLI 映射表 SHALL 只在 `AGENTS.md` §3 维护一份；skill / strategy / playbook 中对该表的引用 SHALL 是指针（链接或一句话引用），SHALL NOT 复制表格内容。

#### Scenario: external-cli-not-in-engine-registry
- **WHEN** 检查 `configs/engine-registry.json` 与 `configs/capability-registry.yaml`
- **THEN** 其中 SHALL NOT 出现 `twitter-cli` / `opencli` / `agent-reach` / `gh` / `yt-dlp` / `external-cli-routing` 等条目

#### Scenario: routing-table-not-duplicated
- **WHEN** 审查 `skills/chrome-agent/SKILL.md`、`sites/strategies/x.com/strategy.md`、`docs/playbooks/*.md` 中对外部 CLI 路由的描述
- **THEN** 这些文件 SHALL 仅包含指向 `AGENTS.md` §3 的指针引用，SHALL NOT 各自维护一份独立的平台→CLI 映射表

#### Scenario: strategy-frontmatter-unaffected
- **WHEN** 审查受影响站点策略的 frontmatter（如 `x.com/strategy.md`）
- **THEN** `engine_preference.preferred` 字段 SHALL 保持原有引擎 ID 值（如 `scrapling-fetch` / `chrome-cdp`），SHALL NOT 包含任何外部 CLI 标识

#### Scenario: capability-not-in-section-2
- **WHEN** 审查 `AGENTS.md` §2 Capability Framework（4 维模型 A 轴表）
- **THEN** 其中 SHALL NOT 出现 `external-cli-routing` 行项；该 capability 仅以 §3 Governance Rules 中的路由表形式呈现
