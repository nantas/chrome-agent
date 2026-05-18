# AGENTS.md — chrome-agent 治理文档

## 1. Service Identity（服务身份）

**chrome-agent** 是**跨仓库网页抓取服务（cross-repo web scraping service）**，提供标准化、可复用的网页内容获取流程。推荐的 agent-facing 正式入口是全局 `chrome-agent` workflow skill，repo-backed 的全局 `chrome-agent` CLI 是低层显式执行面与 shell/backend 入口；具体执行仍由当前仓库内部的 `AGENTS.md`、specs、策略库与引擎规则负责。区别于通用的浏览器调试工具仓库，其核心职责是获取和分析网页内容，将浏览器访问与诊断能力作为下层服务的能力层使用。

### 核心设计原则

- **Scrapling-first**: 默认使用 Scrapling 作为抓取引擎，在需要结构化诊断证据时 fallback 到浏览器工具
- **Workflow-driven**: 通过 `AGENTS.md` + skills 定义标准化工作流程，而非依赖临时脚本
- **Read-only by default**: 对已登录页面只做读操作，不写回，除非用户明确扩大范围
- **证据驱动**: 每次任务产出可追溯的报告，为后续流程改进和策略库积累提供依据

### 范围

**范围内：**
- 网页内容获取（静态页面、SPA、动态列表、受保护页面、文章提取）
- 前端调试、页面结构化分析和证据收集
- 站点特定经验的积累与策略库更新

**范围外（v1）：**
- 凭据管理
- 大型自动化框架
- 在真实用例验证之前预先抽象 skill 和配置结构

## 2. Capability Framework（能力框架）

### 对外能力（面向用户）

| 能力 | 说明 | 状态 |
|------|------|------|
| **explore** | 分析目标页面结构、交互模式、反爬机制 | 规划中 |
| **fetch** | 获取页面内容（静态/动态/受保护） | 已验证 |
| **crawl** | 策略引导有界遍历，默认输出 Markdown | 已验证 |
| **scrape** | 策略无关递归爬取，默认输出 Markdown | 已验证 |

### 对内能力（维护与扩展）

| 能力 | 说明 | 状态 |
|------|------|------|
| **site-strategy** | 站点结构描述（DOM 特征、分页模式、反爬等级） | 未结构化 |
| **anti-crawl-strategy** | 反爬策略配置（代理、延迟、指纹、挑战处理） | 未结构化 |
| **engine-registry** | 引擎注册与发现 | 已规范 |
| **output-lifecycle** | 输出物管理（格式、暂存、清理） | 未实现 |

能力全景详见[总体规划文档](docs/governance-and-capability-plan.md#3-能力全景图)。

## 3. Governance Rules（治理规则）

### 工作流路由规则

本仓库定义两种工作流路径，根据用户意图选择：

全局 `chrome-agent` workflow skill 与 repo-backed `chrome-agent` CLI 都只是入口层。无论请求从哪个 shell 或 agent 进入，真正的路由判断仍由仓库内规则执行，本节仍是行为权威。

**Content Retrieval（默认路径）**：用户给 URL 要求获取内容时使用。Scrapling-first，轻量验证，直接返回内容。

**Platform/Page Analysis（深度路径）**：用户要求分析、调试、收集证据时使用。可 fallback 到 Chrome DevTools，完整证据收集，产出报告。

路由信号：默认走 Content Retrieval；prompt 包含 `分析、调试、证据、总结经验、平台、结构、抓取规则、复现` 等信号时走 Platform/Page Analysis；两种信号同时出现时优先 Platform/Page Analysis。

**Explore Deep Discovery（策略缺口路径）**：当 `explore <url>` 未命中已有策略时，不再仅返回"strategy gap"，而是自动执行 deep discovery 管线：
1. **引擎链探测**（ProbeChain）：依次尝试 `scrapling-get` → `obscura-fetch` → `cloakbrowser-fetch` → `chrome-devtools-mcp`
2. **API 发现**（ApiDiscovery）：探测 `/api.php`、`/wp-json`、`/graphql`、`/sitemap.xml`、`/robots.txt`
3. **结构映射**（StructureMapper）：提取 nav 栏目（≤10）、页面类型（home/list/article/gallery）、内容结构（表格/infobox/列表）
4. **保护识别**（ProtectionIdentifier）：基于引擎链错误 + HTML 特征判断保护机制
5. **策略模板选择**：从 `sites/templates/` 选择最佳匹配模板（mediawiki / mediawiki-fandom / static-site / custom）
6. **Scaffold 生成**：填充 frontmatter 并写入 `sites/strategies/<domain>/strategy.md`
7. **样本转换与自检**（S1-S7）：转换样本、运行自检、最多 2 轮 auto-remediation
8. **冻结**：用户确认后移除 scaffold 标记、追加 `sites/strategies/registry.json`

该路径由 `scripts/explore/` Python 模块实现，CLI 通过 `python3 scripts/explore/main.py` 调用。若 deep discovery 失败，CLI 仍 fallback 到原有 detectBackend + bootstrap-strategy 建议行为。

所有以 Scrapling 为起点的路径在真正执行前都必须先做 Scrapling CLI preflight：先检查 `SCRAPLING_CLI_PATH`，再检查默认受管安装 `$HOME/.cache/chrome-agent-scrapling/bin/scrapling`，仍缺失时先执行安装保障；只有 preflight 成功后，才能进入 fetcher 选择或 MCP 启动。

若 preflight 无法恢复 CLI，可报告安装/配置失败，但不得伪装成已经进入 Scrapling-first 工作流。

操作流程详见 [docs/playbooks/scrapling-cli-preflight.md](docs/playbooks/scrapling-cli-preflight.md) 与 [docs/playbooks/scrapling-fetchers.md](docs/playbooks/scrapling-fetchers.md)。

### Explore→Crawl Confirmation Gate

When `explore` returns `partial_success` with a strategy gap (no existing strategy for the target domain), the agent **MUST** follow the Explore Workflow Gates defined in the chrome-agent skill before proceeding to `crawl` or `fetch`.

1. The agent **MUST NOT** proceed directly to `crawl` or `fetch` without user confirmation.
2. The agent **MUST** present at minimum: structure analysis, sample conversions, and self-check results.
3. When `explore` returns `failure`, the agent **MUST** surface the exact failure reason and remediation from the explore result as-is. The agent **MUST NOT** fabricate a strategy or workaround, **MUST NOT** attempt to fall back to a different extraction path without user approval, and **MUST** wait for user direction before taking any further action on the target URL.
4. The agent **SHALL** follow the Agent Gate rules defined in `skills/chrome-agent/SKILL.md` — including self-check report before presentation, sample file path output, self-audit before user review, full retest on converter change, 3-iteration limit, and **Architecture Gate** (strategy↔pipeline bidirectional alignment validation), and **KI Lifecycle Gate** (Known Issue classification, prioritization, and sequential fix management via `scripts/explore/ki_lifecycle.py`).
5. The agent **MUST** ensure the Architecture Gate passes before proceeding to user confirmation. The gate validates that every strategy extraction field has a pipeline consumer (no dead config) and that every pipeline site-specific value is sourced from strategy config (no hardcoded selectors/domains).

### 引擎选择策略

**默认路径：Scrapling + cdp_lightweight**
- 静态页面 → `scrapling-get`
- SPA/动态页面 → `obscura-fetch` (cdp_lightweight)
- 完整浏览器需求 → `scrapling-fetch`
- 高保护页面（Turnstile/reCAPTCHA/TLS 指纹） → `cloakbrowser-fetch` (playwright_stealth)
- 批量 URL → bulk variants
- 已登录会话 → session variants

> `scrapling-stealthy-fetch` 已被 `cloakbrowser-fetch` 替代（superseded），保留在 registry 中供历史引用。

**API 路径：MediaWiki API 提取管线**（仅 `crawl` 命令）
- 策略含 `api.platform: mediawiki` → `scripts/mediawiki-api-extract`（Phase A: Discovery → Phase B: Extraction → Phase C: Assembly）
- API 管线失败时自动 fallback 到 Scrapling crawl
- `fetch` 和 `scrape` 命令不触发 API 路径
- 输出 Markdown 与 Scrapling 输出格式兼容，并额外包含结构化 frontmatter

**样本转换 CLI（策略驱动）**：
- `scripts/explore/sample_converter.py` — 使用策略 `extraction.*` 规则将 HTML 转换为 Markdown
- `apply` 子命令：转换已有的 HTML 文件
- `fetch-and-apply` 子命令：通过 MediaWiki `action=parse` API 获取页面后转换
- 适用场景：explore 策略命中后，agent 通过此 CLI 执行策略驱动的样本转换

fetcher 选择的前提是 preflight 已成功；不可把 CLI 安装失败误判为 fetcher 或 fallback 问题。

**诊断 fallback：chrome-devtools-mcp**
当 Scrapling 输出不完整、被阻断、视觉存疑，或需要 DOM/网络/控制台/截图/交互证据时使用。

**实时会话 fallback：chrome-cdp**
当需要立即在已打开的 Chrome 标签页上继续操作，或已登录状态无法通过 Scrapling 安全保持时使用。

**fallback 选择标准**：按诊断需求 vs 会话连续性需求选择，不因两个工具都可用就随意切换。

全局 `chrome-agent` workflow skill 与 CLI 都不得复制或覆盖上述引擎选择规则；skill 只负责 doctor preflight、意图路由与结果包装，CLI 只负责 repo 解析、dispatch、doctor、clean 和结果归一化。

切换逻辑详见 [docs/playbooks/fallback-escalation.md](docs/playbooks/fallback-escalation.md) 与 [docs/playbooks/obscura-cli-preflight.md](docs/playbooks/obscura-cli-preflight.md)。CloakBrowser preflight 详见 `scripts/cloakbrowser-preflight.sh`。

### 爬取问题系统化诊断与修复

当用户报告已有策略站点的爬取问题（如"爬取结果链接缺失"、"分类不对齐"、"后处理脚本过多"等），Agent 应遵循以下系统化流程，而非逐问题零散打补丁：

**Phase 1: 问题归因分类**

将报告中所有问题按归属分类为三线：
- **P-line（Pipeline 管线层）**：代码缺陷或缺失功能，如 URL 解码失败、断点续传缺失、重定向未处理
- **S-line（Strategy 策略层）**：策略文件配置缺口，如缺少 `category→directory` 映射、未区分 list_page vs category_page
- **W-line（Workflow 工作流层）**：工具调用方自行编写的外部脚本覆盖了管线应承担的能力

**Phase 2: 代码能力映射**

对每个问题：
1. 阅读相关源码模块（管线脚本、converter、策略文件）
2. 判断当前代码是否已具备对应能力（已有但未触发 / 已有但行为错误 / 完全缺失）
3. 标记修复类型：bugfix（小范围修改） / extension（新增模块） / schema-update（策略字段扩展）

**Phase 3: 方案设计**

- 按能力维度（New / Modified）列出需要变更的 capability
- 每项 capability 产出 spec delta（`## ADDED/MODIFIED Requirements`）作为行为规范真源
- 通过 openspec change 工件化（proposal → specs → design → tasks）
- 与用户确认 capability 清单后再进入实现

**Phase 4: 验证闭环**

- 对站点策略覆盖的目标站点执行实际爬取验证
- 检查 P-line 修复是否生效（bugfix）、S-line 缺口是否填补（strategy schema）、W-line 脚本是否被管线消化
- 测试中发现的新问题纳入 change 工件更新
- 保留样本产出供人工审核
- verification 通过后回写项目页面与策略文件的状态

**路由信号**：用户 prompt 包含 `爬取报告`、`遇到的问题`、`为什么 X 失败`、`分类不对`、`链接丢失`、`后处理` 等关键词，且讨论的是已有策略的站点时，走此流程。

**禁止行为**：
- 不得逐问题零散修复而不做系统归因
- 不得在未确认 capability 清单前直接写实现代码
- 不得跳过 openspec change 直接修改策略和管线
- 不得在未实际测试目标站点的情况下声称"已修复"

### Handoff 工作流

当 CLI 在内部失败场景（管线脚本非零退出、策略缺失、引擎 preflight 失败等）自动生成 handoff 文档时：

- **存储路径**：`outputs/handoffs/<run-tag>/handoff.md`，与 `outputs/` 同级受 `.gitignore` 排除
- **触发条件**：仅内部失败（详见 `openspec/changes/workflow-handoff-gate/specs/handoff-emission/spec.md`）
- **SKILL.md 闸门**：当 CLI 结果包含 `handoff_path` 时，Handoff Gate 强制停止工作流并路由到 chrome-agent 仓库修复
- **禁止行为**：不得绕过 Handoff Gate 直接调用引擎或编写替代脚本
- **外部失败**：目标网站 HTTP 错误、无效 URL、环境配置缺失不触发 handoff，保持原有行为

Handoff 文档包含完整的上下文（命令、URL、时间戳、策略路径）、错误详情、run artifacts 路径和下一步修复指引。chrome-agent 仓库的 agent 应基于 handoff 文档进行 P-line/S-line/W-line 分类并通过 openspec change 修复。

### 认证访问边界

- 已登录/认证的工作需要用户明确批准目标页面或标签页
- 认证运行默认为只读，除非用户明确扩大范围
- 仍走 Scrapling-first，但 Scrapling 会话复用失败时切换到 chrome-cdp 实时标签页
- 若工作流建议把 `SCRAPLING_CLI_PATH` 写入 `/Users/nantas-agent/.zshenv`，必须先征求用户确认；已有正确值不重写，冲突值不静默覆盖
- 遇到重定向到登录、页面重置、登出或写操作风险时，停止并记录失败

认证会话规则详见[docs/playbooks/authenticated-sessions.md](docs/playbooks/authenticated-sessions.md)。

### 报告产出规范

| 工作流 | 最低要求 |
|--------|----------|
| Content Retrieval | 默认不产出 `reports/`；返回页面标题、最终 URL、Scrapling 路径、提取内容/失败原因；仅在显式 `--report` 时产出 durable report |
| Platform/Page Analysis | 完整 reports/ 产出：标题、URL、内容摘要、截图、结构线索、交互结果 |
| 文章提取（两者通用） | DOM 保序、内联图片 URL 保留、Markdown 图片语法 |

证据收集方法详见[docs/playbooks/evidence-collection.md](docs/playbooks/evidence-collection.md)。

## 4. Directory Governance（目录结构治理）

```
.
├── AGENTS.md           # [本文件] 治理文档——服务身份、能力契约框架、治理规则
├── README.md           # 仓库全景——身份、能力总览、Quick Start、路线图
├── openspec/           # 规范驱动的变更管理（Orbitos Spec Standard v0.3）
│   ├── changes/        #   进行中 + 已归档的变更
│   └── specs/          #   已冻结的能力规范（行为规范真源）
├── docs/
│   ├── decisions/      # 架构决策记录（YYYY-MM-DD-topic.md）
│   ├── playbooks/      # 操作手册（从 AGENTS.md 提取的操作流程）
│   ├── plans/          # 实现规划文档
│   └── setup/          # 环境配置与安装指引
├── outputs/            # 抓取产出暂存区（.gitignore 排除）
├── reports/            # 执行报告与证据
├── skills/             # 全局 skill 源码（含官方 `skills/chrome-agent/` workflow skill）
├── sites/              # 站点经验 + 反爬策略（YAML frontmatter + 正文）
├── configs/            # 工具与运行配置
├── scripts/            # 辅助脚本（含 `mediawiki-api-extract` 提取管线）
```

## 5. Decision Record Governance（决策记录治理）

所有架构决策记录存放于 `docs/decisions/`。

### 命名规则

`YYYY-MM-DD-<topic>.md`，例如 `2026-04-23-scrapling-first-workflow.md`

### 内容结构

每个决策记录包含：
- **Context**: 决策背景和驱动力
- **Decision**: 做出的决策和理由
- **Consequences**: 决策带来的后果和后续考虑

### 索引

`docs/decisions/README.md` 维持所有决策的索引清单，包括标题、日期和一句话摘要。

## 6. Spec and Change Governance（规范与变更治理）

本仓库使用 Orbitos Spec Standard v0.3 管理规范与变更。

- 行为规范真源位于 `openspec/specs/<capability-id>/spec.md`
- 活跃变更位于 `openspec/changes/<change-name>/`
- 已归档变更位于 `openspec/changes/archive/YYYY-MM-DD-<name>/`
- 项目页面（Obsidian）不替代 spec delta 作为实现与验证依据
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks

## 7. 策略库治理（Strategy Library Governance）

### 目录结构

```
sites/
├── anti-crawl/                # 反爬策略（按保护机制命名）
│   ├── default.md             #   默认 Scrapling-first 策略
│   ├── <mechanism>.md         #   具体反爬策略
│   └── registry.json          #   索引
└── strategies/                # 站点策略（按域名文件夹组织）
    ├── <domain>/
    │   ├── strategy.md        #   站点策略（YAML frontmatter + body）
    │   └── _attachments/      #   操作附件（可选）
    └── registry.json          #   索引
```

### 治理约束

- **frontmatter 为权威来源**：`registry.json` 仅为索引摘要，不一致时以 frontmatter 为准
- **新增策略需更新 registry.json**：每次添加或修改策略文件必须同步更新对应的 `registry.json`
- **反爬策略按机制命名**：文件名匹配保护机制（如 `cloudflare-turnstile.md`），而非来源站点
- **站点策略按域名组织**：文件夹名匹配 `domain` 字段，策略文件必须为 `strategy.md`
- **操作内容分离**：脚本、配置等操作内容放入 `_attachments/`，不混入 `strategy.md`
- **受控词汇表**：`protection_level`、`page_type`、`protection_type` 的枚举值定义在各自的 spec 中，新增值需通过 openspec change

### 策略派生（Bootstrap）

- **`bootstrap-strategy` 命令自动生成并更新 registry.json**：通过 `chrome-agent bootstrap-strategy <url> --from <domain>` 派生的策略会自动写入 `sites/strategies/<domain>/strategy.md` 并追加 `registry.json` 条目，无需手动更新索引
- **手动创建策略仍需人工更新 registry.json**：当不通过 `bootstrap-strategy` 而是直接新建 `strategy.md` 时，必须手动添加对应 registry 条目
- **`backend` 字段为可选 advisory 字段**：用于标记后端家族关系（如 `weird-gloop-mediawiki-1.45`），不作为运行时策略匹配键；无效值仅触发警告，不阻断执行
- **bootstrap 生成的策略必须 review**：生成的 `strategy.md` 包含 `<!-- Bootstrapped from ...; review recommended -->` 标记，使用前必须完成验证并替换为实际操作细节

更多细节参见 `sites/README.md`。

### Pipeline Strategy Schema 治理

#### 权威来源

`scripts/mediawiki-api-extract/pipeline/orchestrate.py` 中的 `_STRATEGY_REGISTRY` 是策略 ID 的唯一权威来源。

每个 `content_profile` 维度的合法值由 `_STRATEGY_REGISTRY` 中对应维度的 key 定义。

#### 策略文件约束

- 策略文件的 `api.content_profile` 各字段只能引用 `_STRATEGY_REGISTRY` 中对应维度已注册的 ID
- Pipeline 启动时执行 hard-fail 校验：引用未注册 ID 导致 `EXIT_STRATEGY_ERROR`，不降级执行
- `bootstrap-strategy` 输出时同步校验：写入策略文件前检查所有 `content_profile` ID 的有效性
- 未指定 `content_profile` 的策略文件使用 `DEFAULT_STRATEGIES` 默认值，不触发校验

#### 扩展协议

新增策略实现必须严格遵守以下顺序：

1. **实现 Strategy 类**（继承或实现对应接口 Protocol）
2. **注册到 `_STRATEGY_REGISTRY`** 对应维度的 dict 中
3. **在策略文件中引用**已注册的 ID

严禁在 Step 2（注册）之前执行 Step 3（策略文件引用）。违反此顺序的策略文件引用会被 pipeline 的启动校验拒绝。

#### 当前注册 ID 清单

> 此清单为快速参考，不替代 `_STRATEGY_REGISTRY` 作为权威来源。以代码为准。

| 维度 | 合法 ID |
|------|--------|
| `discovery` | `allpages`, `category_members` |
| `content_acquisition` | `wikitext_only`, `hybrid_wikitext_plus_rendered`, `html_rendered` |
| `link_resolver` | `exact_title_match`, `short_name_with_cross_namespace` |
| `template_processor` | `simple_substitution`, `structured_with_lua_fallback` |
| `list_page_assembler` | `frontmatter_driven`, `hybrid_frontmatter_and_rendered` |

#### Registry 变更约束

删除或重命名 registry 中的 ID 前必须：

1. 扫描所有 `sites/strategies/*/strategy.md` 确认无策略文件引用该 ID
2. 更新任何引用该 ID 的策略文件
3. 同步更新 `sites/templates/` 中的模板文件（如模板包含该 ID）

新增 registry ID 无此约束（新增是向后兼容的）。

#### platform_variant 声明

策略文件的 `api` 对象中可选声明 `platform_variant` 字段，用于 MediaWiki 平台子类型化：

| 值 | 描述 |
|------|------|
| `fandom` | Fandom-hosted MediaWiki |
| `wiki-gg` | wiki.gg-hosted MediaWiki |
| `standard` | 标准 MediaWiki（默认值，未指定时使用） |

Pipeline 在 `run_pipeline()` 中解析此字段并传递给各阶段函数。当前阶段仅接受和记录，不实现行为分支。

## 8. 引擎扩展治理（Engine Extension Governance）

- **新引擎必须通过 openspec change 接入**：不得绕过 `openspec/changes/` 工作流直接新增或替换引擎能力。
- **注册索引必须同步更新**：新增、修改或 supersede 任一引擎时，必须同步更新 `configs/engine-registry.json`，并以对应 contract spec 为权威来源。
- **artifact checklist 以 spec 为准**：接入时必须遵循 `openspec/specs/extension-api/spec.md` 中定义的 artifact checklist、验证条件与命名规范。
- **注册格式以 spec 为准**：引擎条目的字段结构、特性评分、`composite_score`、`default_rank` 与生命周期状态由 `openspec/specs/engine-registry/spec.md` 约束。
- **聚合索引只保留跨引擎关注点**：`openspec/specs/engine-contracts/spec.md` 负责错误矩阵、选择映射、smoke-check 聚合；具体引擎清单不再内联维护。

### 已注册引擎概览

| 引擎 | 类型 | 状态 | default_rank | 适用场景 |
|------|------|------|--------------|----------|
| `scrapling-get` | `http` | frozen | 1 | 静态页面、低保护 |
| `obscura-fetch` | `cdp_lightweight` | draft | 2 | 动态内容、SPA、动态列表、静态文章 |
| `scrapling-fetch` | `playwright` | frozen | 3 | SPA、动态交互（完整浏览器） |
| `scrapling-bulk-fetch` | `playwright_bulk` | frozen | 4 | 批量操作 |
| `cloakbrowser-fetch` | `playwright_stealth` | draft | 4 | 高保护页面、Turnstile、reCAPTCHA、TLS 指纹 |
| `scrapling-stealthy-fetch` | `playwright_stealth` | superseded | 4 | ~~高保护页面~~（已被 cloakbrowser-fetch 替代） |
| `chrome-devtools-mcp` | `cdp_managed` | frozen | 5 | 诊断证据 |
| `chrome-cdp` | `cdp_live` | frozen | 6 | 实时会话、认证延续 |

新增引擎示例：`obscura-fetch` 作为 `cdp_lightweight` 类型接入，填补 `scrapling-get` 与 `scrapling-fetch` 之间的效率断层。预编译二进制通过 GitHub Releases 获取，受管安装路径为 `$HOME/.cache/chrome-agent-obscura/bin/obscura`；详见 [docs/playbooks/obscura-cli-preflight.md](docs/playbooks/obscura-cli-preflight.md)。

新增引擎示例：`cloakbrowser-fetch` 作为 `playwright_stealth` 类型接入，替代 `scrapling-stealthy-fetch` 处理高保护页面。57 个 C++ 源码级 Chromium patch 提供 TLS 指纹绕过、Cloudflare Turnstile 自动解析、reCAPTCHA v3 高分等 stealth 能力。用户通过 `pip install cloakbrowser` 安装，binary 缓存于 `~/.cloakbrowser/chromium-{version}/`；详见 `scripts/cloakbrowser-preflight.sh`。

### 引擎版本治理（Engine Version Governance）

#### 权威来源

`configs/engine-versions.json` 是所有引擎依赖版本的唯一权威来源（single source of truth）。每个引擎条目声明 `expected_version`、检测方法、文件哈希（如适用）和更新来源。

#### 升级约束

当操作者（agent 或人工）执行引擎 runtime 版本升级时，**必须同步更新** `configs/engine-versions.json` 中对应引擎的以下字段：

| 字段 | 必须更新 | 说明 |
|------|---------|------|
| `expected_version` | ✅ | 新版本号 |
| `detection.binaries[].expected_size` | ✅（Obscura） | 新二进制文件大小（字节） |
| `detection.binaries[].expected_md5` | ✅（Obscura） | 新二进制 MD5 哈希 |

仅更新 `expected_version` 而不同步哈希值，会导致 preflight 和 `engine-version-check.sh` 持续报告 `hash_mismatch`，obscura-cli-preflight.sh 会反复触发重新下载。

#### 升级工作流

引擎 runtime 升级必须遵循以下顺序：

1. **确认目标版本可用**：检查 GitHub Release / PyPI 确认目标版本已发布
2. **更新清单**：修改 `configs/engine-versions.json` 中的 `expected_version` 及相关哈希/大小字段
3. **执行安装**：运行 `./scripts/engine-version-check.sh --update --engine <name>` 或对应 preflight 脚本
4. **验证安装**：运行 `./scripts/engine-version-check.sh --json` 确认 `all_ok: true`
5. **doctor 集成验证**：运行 `chrome-agent doctor --format json` 确认 `version_<engine>` check 通过
6. **提交变更**：将 `configs/engine-versions.json` 的更新随升级提交一起 commit

**禁止**在未更新 `configs/engine-versions.json` 的情况下手动替换二进制文件或通过 pip 重装——这会绕过版本治理，导致后续 preflight 和 doctor 报告不可靠的结果。

#### 清单字段获取方法

| 引擎 | `expected_version` | `expected_md5` / `expected_size` |
|------|--------------------|-------------------------------|
| Scrapling | PyPI 版本号 | 不适用（pip 管理版本） |
| Obscura | GitHub Release tag（去 `v` 前缀） | 安装后执行 `md5 -q` + `stat -f '%z'` 获取 |
| CloakBrowser | `pip show cloakbrowser` 的 `Version` | 不适用（pip 管理版本） |

Obscura 哈希获取示例（升级后立即执行）：
```bash
BIN="$HOME/.cache/chrome-agent-obscura/bin"
md5 -q "$BIN/obscura" "$BIN/obscura-worker"
stat -f '%z' "$BIN/obscura" "$BIN/obscura-worker"
```

#### doctor 中的版本检查

`runDoctor()` 通过 `scripts/engine-version-check.sh --json` 自动收集所有引擎的版本状态，并在 checks 中输出 `version_<engine>` 条目。版本不匹配会反映为 `partial_success` 或 `failure`，具体取决于其他检查的结果。

#### 与其他治理规则的交互

- **engine-registry.json 不作为版本来源**：`configs/engine-registry.json` 中的 prose 版本引用（如 `"v0.1.2 with expanded release history"`）仅为人工参考，不参与自动化版本检测
- **preflight 脚本从清单读取版本**：`obscura-cli-preflight.sh` 从 `configs/engine-versions.json` 读取 `expected_version`，不再硬编码
- **engine-version-check.sh 是唯一检测入口**：所有版本检测逻辑集中在该脚本中，preflight 和 doctor 均通过它获取结果

## 9. Development（开发指南）

### 仓库结构

本仓库是脚本和配置驱动的工具仓库，无编译/构建步骤。

| 目录 | 语言 | 用途 |
|------|------|------|
| `scripts/chrome-agent-cli.mjs` | Node.js ESM | CLI 主入口（所有命令逻辑） |
| `scripts/chrome-agent-runtime.mjs` | Node.js ESM | 全局 launcher runtime（repo 解析 + 分发） |
| `scripts/mediawiki-api-extract/` | Python | MediaWiki API 提取管线（多子模块包） |
| `scripts/explore/` | Python | Deep discovery 管线（explore 命令后端） |
| `scripts/*.sh` | Bash | Preflight、版本检测、安装脚本 |
| `configs/` | JSON | 引擎注册、版本清单、后端签名 |
| `sites/strategies/` | YAML+MD | 站点策略（frontmatter 为权威来源） |
| `skills/` | MD | 全局 workflow skill 源码 |
| `openspec/` | MD | 规范与变更管理 |

### 运行测试

```bash
# 运行唯一的测试文件（Node.js 内置测试框架）
node --test tests/chrome-agent-runtime.test.mjs
```

- 测试使用 `node:test` + `node:assert/strict`，无第三方依赖
- 测试通过 `spawnSync` 调用 runtime/cli 脚本，需要从仓库根目录执行
- 测试创建临时 mock repo 验证 repo 解析优先级（`CHROME_AGENT_REPO` → `repo://` override → registry fallback）

**注意**：当前无 Python 测试。修改 `scripts/mediawiki-api-extract/` 或 `scripts/explore/` 时需手动验证。

### Node.js 脚本约定

- **纯 ESM**：所有 `.mjs` 文件使用 `import`/`export`，无 CommonJS
- **无 TypeScript**：无编译步骤，直接运行 `.mjs`
- **依赖**：仅 `better-sqlite3` 和 `yaml`（`package.json`）
- **CLI 输出**：JSON-first（`--format json`），text 模式仅是渲染层
- **函数风格**：顶级函数声明（`function xxx()`），非箭头函数
- **路径解析**：通过 `__dirname` + `path.resolve` 推断 `repoRoot`

### Python 脚本约定

- **Python 3.9 兼容**：避免 `X | Y` 类型注解（3.10+ 语法），用 `Optional[X]` 代替
  - `scripts/explore/sample_converter.py` 当前有此问题（`dict | None` 在 3.9 上报 TypeError）
- **调用方式**：`python3 -m scripts.mediawiki-api-extract <subcommand>`（非直接执行目录）
  - `__main__.py` 会自动 re-invoke 通过 `-m` 解决包名含连字符的问题
- **依赖**：各子模块有独立 `requirements.txt`（如 `scripts/explore/requirements.txt`），无全局 pyproject.toml
- **Explore 模块**：通过 `sys.path.insert(0, os.path.dirname(...))` 做本地导入

### Shell 脚本约定

- **shebang**：`#!/bin/sh` 或 `#!/usr/bin/env bash`
- **错误处理**：`set -eu` 或 `set -euo pipefail`
- **路径计算**：`SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)` + `REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)`
- **日志**：`printf '%s\n' "$*" >&2` 模式写入 stderr

### 版本检查与诊断

```bash
# 检查所有引擎版本是否匹配清单
./scripts/engine-version-check.sh
./scripts/engine-version-check.sh --json          # JSON 输出
./scripts/engine-version-check.sh --update        # 自动更新

# CLI doctor（需先安装全局 launcher）
export CHROME_AGENT_REPO="$PWD"
chrome-agent doctor --format json

# 安装/更新全局 CLI launcher
./scripts/install-chrome-agent-cli.sh
```

### 常见陷阱

- **`scripts/explore/` 需要 Python 3.10+**：使用了 `dict | None` 联合类型语法。macOS 自带 3.9.6 会报 TypeError。修复时改用 `Optional[dict]`
- **MediaWiki 提取管线的 `__main__.py` 陷阱**：不能直接 `python3 scripts/mediawiki-api-extract/`，必须用 `-m` 方式调用
- **引擎版本升级必须同步 `configs/engine-versions.json`**：不同步哈希值会导致 preflight 持续报告 `hash_mismatch`（详见 §8 引擎版本治理）
- **`SCRAPLING_CLI_PATH` 是唯一识别变量**：CLI 不会猜测路径，未设置时走受管安装 `$HOME/.cache/chrome-agent-scrapling/bin/scrapling`
- **修改策略文件后必须更新 `registry.json`**：手动创建策略时需手动更新索引；`bootstrap-strategy` 命令会自动更新

## 10. Reference Index（参考索引）

| 文档 | 位置 | 用途 |
|------|------|------|
| 总体规划 | `docs/governance-and-capability-plan.md` | 项目路线图与阶段定义 |
| 决策记录 | `docs/decisions/` | 架构决策索引 |
| 操作手册 | `docs/playbooks/` | Scrapling 使用、fallback、证据收集、认证会话 |
| Global Workflow Skill | `skills/chrome-agent/SKILL.md` | 推荐的 agent-first 入口契约与 CLI-backed 路由规则 |
| Global CLI 安装 | `docs/playbooks/chrome-agent-global-install.md` | 全局 `chrome-agent` launcher 安装、skill 安装与迁移说明 |
| Scrapling CLI preflight | `docs/playbooks/scrapling-cli-preflight.md` | 工作流前的安装保障与 `.zshenv` 确认边界 |
| Obscura CLI preflight | `docs/playbooks/obscura-cli-preflight.md` | Obscura 二进制检测、下载与版本固定 |
| Scrapling fetcher 指南 | `docs/playbooks/scrapling-fetchers.md` | fetcher 选型与参数参考 |
| Fallback 切换逻辑 | `docs/playbooks/fallback-escalation.md` | 何时升到 CloakBrowser、DevTools 或 chrome-cdp |
| CloakBrowser Preflight | `scripts/cloakbrowser-preflight.sh` | CloakBrowser 模块与 binary 检查 |
| 引擎版本清单 | `configs/engine-versions.json` | 所有引擎的期望版本、检测方法和更新方式真源 |
| 版本检测脚本 | `scripts/engine-version-check.sh` | 统一的版本检测、比对和自动更新 |
| 证据收集方法 | `docs/playbooks/evidence-collection.md` | 截图/DOM/网络等收集步骤 |
| 认证会话规则 | `docs/playbooks/authenticated-sessions.md` | 已登录页面的只读操作安全规则 |
| 站点经验库 | `sites/` | 站点结构与反爬策略 |
| MediaWiki API 提取管线 | `scripts/mediawiki-api-extract` | 策略驱动的 MediaWiki API 内容提取 CLI |
| 能力规范 | `openspec/specs/` | 已冻结的行为规范 |
| 治理 Spec | `openspec/specs/agents-governance/spec.md` | 本文件的规范真源 |
| 契约元模型 | `openspec/specs/capability-contracts/spec.md` | 引擎契约通用 schema |
| KI Lifecycle 模块 | `scripts/explore/ki_lifecycle.py` | Known Issue 分类、优先级、状态追踪与修复批次规划 |
