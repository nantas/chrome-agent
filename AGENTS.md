# AGENTS.md — chrome-agent 治理文档

## 1. Service Identity（服务身份）

**chrome-agent** 是**跨仓库网页抓取服务（cross-repo web scraping service）**，提供标准化、可复用的网页内容获取流程。区别于通用的浏览器调试工具仓库，其核心职责是获取和分析网页内容，将浏览器访问与诊断能力作为下层服务的能力层使用。

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
| **crawl** | 多页面遍历与批量抓取 | 规划中 |

### 对内能力（维护与扩展）

| 能力 | 说明 | 状态 |
|------|------|------|
| **site-strategy** | 站点结构描述（DOM 特征、分页模式、反爬等级） | 未结构化 |
| **anti-crawl-strategy** | 反爬策略配置（代理、延迟、指纹、挑战处理） | 未结构化 |
| **engine-registry** | 引擎注册与发现 | 未实现 |
| **output-lifecycle** | 输出物管理（格式、暂存、清理） | 未实现 |

能力全景详见[总体规划文档](docs/governance-and-capability-plan.md#3-能力全景图)。

## 3. Governance Rules（治理规则）

### 工作流路由规则

本仓库定义两种工作流路径，根据用户意图选择：

**Content Retrieval（默认路径）**：用户给 URL 要求获取内容时使用。Scrapling-first，轻量验证，直接返回内容。

**Platform/Page Analysis（深度路径）**：用户要求分析、调试、收集证据时使用。可 fallback 到 Chrome DevTools，完整证据收集，产出报告。

路由信号：默认走 Content Retrieval；prompt 包含 `分析、调试、证据、总结经验、平台、结构、抓取规则、复现` 等信号时走 Platform/Page Analysis；两种信号同时出现时优先 Platform/Page Analysis。

操作流程详见[docs/playbooks/scrapling-fetchers.md](docs/playbooks/scrapling-fetchers.md)。

### 引擎选择策略

**默认路径：Scrapling**
- 静态页面 → `get`
- SPA/动态页面 → `fetch`
- 受保护页面 → `stealthy-fetch`
- 批量 URL → bulk variants
- 已登录会话 → session variants

**诊断 fallback：chrome-devtools-mcp**
当 Scrapling 输出不完整、被阻断、视觉存疑，或需要 DOM/网络/控制台/截图/交互证据时使用。

**实时会话 fallback：chrome-cdp**
当需要立即在已打开的 Chrome 标签页上继续操作，或已登录状态无法通过 Scrapling 安全保持时使用。

**fallback 选择标准**：按诊断需求 vs 会话连续性需求选择，不因两个工具都可用就随意切换。

切换逻辑详见[docs/playbooks/fallback-escalation.md](docs/playbooks/fallback-escalation.md)。

### 认证访问边界

- 已登录/认证的工作需要用户明确批准目标页面或标签页
- 认证运行默认为只读，除非用户明确扩大范围
- 仍走 Scrapling-first，但 Scrapling 会话复用失败时切换到 chrome-cdp 实时标签页
- 遇到重定向到登录、页面重置、登出或写操作风险时，停止并记录失败

认证会话规则详见[docs/playbooks/authenticated-sessions.md](docs/playbooks/authenticated-sessions.md)。

### 报告产出规范

| 工作流 | 最低要求 |
|--------|----------|
| Content Retrieval | 页面标题、最终 URL、Scrapling 路径、提取内容/失败原因 |
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
├── skills/             # 全局 skill 源码
├── sites/              # 站点经验 + 反爬策略（YAML frontmatter + 正文）
├── configs/            # 工具与运行配置
└── scripts/            # 辅助脚本
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

更多细节参见 `sites/README.md`。

## 8. Reference Index（参考索引）

| 文档 | 位置 | 用途 |
|------|------|------|
| 总体规划 | `docs/governance-and-capability-plan.md` | 项目路线图与阶段定义 |
| 决策记录 | `docs/decisions/` | 架构决策索引 |
| 操作手册 | `docs/playbooks/` | Scrapling 使用、fallback、证据收集、认证会话 |
| Scrapling fetcher 指南 | `docs/playbooks/scrapling-fetchers.md` | fetcher 选型与参数参考 |
| Fallback 切换逻辑 | `docs/playbooks/fallback-escalation.md` | 何时升到 DevTools 或 chrome-cdp |
| 证据收集方法 | `docs/playbooks/evidence-collection.md` | 截图/DOM/网络等收集步骤 |
| 认证会话规则 | `docs/playbooks/authenticated-sessions.md` | 已登录页面的只读操作安全规则 |
| 站点经验库 | `sites/` | 站点结构与反爬策略 |
| 能力规范 | `openspec/specs/` | 已冻结的行为规范 |
| 治理 Spec | `openspec/specs/agents-governance/spec.md` | 本文件的规范真源 |
| 契约元模型 | `openspec/specs/capability-contracts/spec.md` | 引擎契约通用 schema |
