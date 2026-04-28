# Governance & Capability Rebuild — 总体规划

> 日期: 2026-04-28
> 状态: 已发布（v1）
> 关联: [binding](../openspec/changes/governance-and-capability-rebuild/binding.md)

---

## 1. 项目目标与服务身份

**chrome-agent** 是跨仓库网页抓取服务（cross-repo web scraping service），提供可复用的网页内容获取流程，覆盖静态页面、SPA、动态列表、受保护页面、文章提取等场景。

核心设计原则：

- **Scrapling-first**: 默认使用 Scrapling 作为抓取引擎，在需要结构化诊断证据时 fallback 到浏览器工具
- **Workflow-driven**: 通过 `AGENTS.md` + skills 定义标准化工作流程，而非依赖临时脚本
- **Read-only by default**: 对已验证的已登录页面只做读操作，不写回
- **证据驱动**: 每次任务产出可追溯的抓取报告，为后续流程改进提供依据

---

## 2. 当前状态

### 已验证的能力

| 能力 | 状态 | 证据 |
|------|------|------|
| Scrapling `get` — 静态页面 | ✅ 已验证 | 公共对比报告 |
| Scrapling `fetch` — SPA / 动态列表 | ✅ 已验证 | 公共对比报告 |
| Scrapling `stealthy-fetch` — 受保护页面 | ✅ 已验证 | 公共对比报告 |
| `chrome-devtools-mcp` — 诊断证据 | ✅ 已验证 | 浏览器工具对比报告 |
| `chrome-cdp` — 实时会话延续 | ✅ 已验证 | 实时会话对比报告 |
| 工作流路由（Content Retrieval / Platform Analysis） | ✅ 已验证 | AGENTS.md 路由定义 |
| 文章式正文提取（DOM 顺序 + 内联图片） | ✅ 已验证 | 微信文章测试 |
| 全局 skill 分发 | ✅ 已验证 | 安装与调度验证 |

### 现有结构

```
.
├── AGENTS.md                 # 操作指南（245 行）
├── README.md                 # 仓库说明（待重写）
├── openspec/
│   ├── changes/              # OpenSpec 变更
│   └── specs/                # 已冻结规范
├── docs/
│   ├── decisions/            # 决策记录
│   ├── playbooks/            # 操作手册
│   ├── plans/                # 实现规划
│   └── setup/                # 环境配置
├── reports/                  # 执行报告
├── skills/                   # 全局 skill 源码
├── sites/                    # 站点经验
└── configs/                  # 工具与运行配置
```

### 已知差距

- AGENTS.md 仍在"浏览器工作台"操作手册模式，未对齐"网页抓取服务"身份
- 能力契约未冻结（各引擎的输入/输出/错误没有统一规范）
- 策略库未标准化（站点策略、反爬策略以经验和报告存在，未结构化）
- 没有引擎注册/发现机制
- 没有输出物生命周期管理

---

## 3. 能力全景图

### 对外能力（面向用户）

```
用户请求
    │
    ├─ explore ──→ 分析目标页面结构、交互模式、反爬机制
    │
    ├─ fetch ────→ 获取页面内容
    │    ├── get           静态页面 / 低保护
    │    ├── fetch         SPA / 动态页面 / 需 JS 渲染
    │    └── stealthy-fetch  受保护页面 / Cloudflare / WAF
    │
    └─ crawl ────→ 多页面遍历与批量抓取（未来）
         ├── pagination    分页 / 列表
         ├── bulk          批量 URL
         └── deep-crawl    递归遍历（未来）
```

### 对内能力（维护与扩展）

| 能力 | 说明 | 状态 |
|------|------|------|
| **site-strategy** | 站点结构描述（DOM 特征、分页模式、反爬等级） | ❌ 未结构化 |
| **anti-crawl-strategy** | 反爬策略配置（代理、延迟、指纹、挑战处理） | ❌ 未结构化 |
| **engine-registry** | 引擎注册与发现（get/fetch/stealthy-fetch + 扩展） | ✅ 已规范 |
| **output-lifecycle** | 输出物管理（格式、存储、清理） | ❌ 未实现 |

### 治理能力

| 能力 | 说明 | 状态 |
|------|------|------|
| **binding** | repo:// 语义、项目页绑定、回写规则 | ✅ Spec 存在 |
| **spec-driven** | Orbitos Spec Standard v0.3 规范驱动变更 | ✅ 工作流已采纳 |
| **decision-log** | 设计决策索引与记录 | ✅ 已有 `docs/decisions/` |
| **writeback** | 结论回写到 Obsidian 项目页 | ⚠️ 流程待验证 |

---

## 4. 阶段划分

### Phase 1: 治理基础重建

| 属性 | 内容 |
|------|------|
| **范围** | 项目治理层与契约元模型建立 |
| **交付物** | AGENTS.md 纯治理重写、agents-governance spec、capability-contracts 元模型 spec、操作流程下沉到 playbooks |
| **需要的 specs** | `agents-governance`、`capability-contracts` |
| **排他边界** | 不涉及引擎扩展、不涉及策略库、不涉及安装链 |

### Phase 2: 契约冻结

| 属性 | 内容 |
|------|------|
| **范围** | 所有现有能力的接口契约定义为规范 |
| **交付物** | 5 个引擎契约 spec（input/output/error 三维 + smoke-check scenario）、`engine-contracts` 聚合索引（引擎类型映射、错误矩阵、smoke-check 清单）、契约一致性验证 |
| **需要的 specs** | `scrapling-get-contract`、`scrapling-fetch-contract`、`scrapling-stealthy-fetch-contract`、`chrome-devtools-mcp-contract`、`chrome-cdp-contract`、`engine-contracts`（聚合索引） |
| **排他边界** | 不修改引擎实现、不扩展新能力；不创建独立的 `error-handling` spec（error 维度融入各引擎契约） |

### Phase 3: 策略库标准化

| 属性 | 内容 |
|------|------|
| **范围** | site-strategy & anti-crawl-strategy 结构化存储，5 个现有站点文件迁移 |
| **交付物** | `site-strategy-schema` spec（YAML frontmatter 字段定义、structure 页面层级、page_type 词汇表、pagination 模式、registry.json 格式、_attachments 目录用途、protection_level 词汇表）、`anti-crawl-schema` spec（frontmatter 字段定义、protection_type 词汇表、detection 信号结构、engine_priority 规则、success/failure signals、registry.json 格式）、两层目录结构（`sites/anti-crawl/` + `sites/strategies/<domain>/`）、5 个反爬策略（default、cloudflare-turnstile、login-wall-redirect、cookie-auth-session、rate-limit-api）、4 个站点策略（mp.weixin.qq.com、x.com、wiki.supercombo.gg、fanbox.cc）、两个 registry.json 索引、sites/README.md 重写、AGENTS.md 追加策略库治理约束 |
| **需要的 specs** | `site-strategy-schema`、`anti-crawl-schema` |
| **排他边界** | 不涉及引擎调度、不涉及策略自动匹配 |

### Phase 4: 引擎扩展治理

| 属性 | 内容 |
|------|------|
| **范围** | 引擎注册机制、扩展 API、新引擎接入流程 |
| **交付物** | `engine-registry` spec、`configs/engine-registry.json`、`extension-api` spec、`openspec/specs/extension-api/contract-template.md`、`scrapling-bulk-fetch-contract` 示例契约、`engine-contracts`/`anti-crawl-schema`/`site-strategy-schema` 合并更新 |
| **需要的 specs** | `engine-registry`、`extension-api`、`scrapling-bulk-fetch-contract` |
| **排他边界** | 不包含策略自动选择、不包含编排层 |

### Phase 5: 安装链与清理闭环

| 属性 | 内容 |
|------|------|
| **范围** | 输出生命周期、安装验证、清理机制 |
| **交付物** | output-lifecycle spec、`clean` workflow、安装链验收 |
| **需要的 specs** | `output-lifecycle`、`install-chain` |
| **排他边界** | 不涉及运行时监控、不涉及远程调度 |

---

## 5. 依赖关系

```
Phase 1: 治理基础重建
    │
    ▼
Phase 2: 契约冻结 ───────────── Phase 3: 策略库标准化
    │                                    │
    ▼                                    │
Phase 4: 引擎扩展治理 ←──────────────────┘
    │
    ▼
Phase 5: 安装链与清理闭环
```

依赖说明：

- **Phase 2 ← Phase 1**: 契约冻结需要在治理基础（capability tree、spec 命名）建立后才能进行
- **Phase 3 ← Phase 1**: 策略 schema 依赖治理层定义的目录结构
- **Phase 3 ← Phase 2**: 策略库中的字段类型和错误码依赖冻结的契约
- **Phase 4 ← Phase 2 + Phase 3**: 引擎扩展需要已冻结的契约和已标准化的策略库
- **Phase 5 ← Phase 4**: 安装链依赖引擎扩展 API 的稳定

---

## 6. 技术栈与工具链

### 当前引擎

| 引擎 | 类型 | 使用场景 |
|------|------|----------|
| Scrapling `get` | HTTP (impersonate) | 静态页面、低保护 |
| Scrapling `fetch` | Playwright | SPA、动态交互 |
| Scrapling `stealthy-fetch` | Playwright + 指纹伪装 | Cloudflare、WAF、高保护 |
| `chrome-devtools-mcp` | Chrome DevTools Protocol | 诊断证据（DOM/网络/性能） |
| `chrome-cdp` | Chrome DevTools Protocol | 实时会话延续 |

### 扩展方向

- **Playwright-based 新引擎**: 可通过 registry 接入
- **CDP-based 新工具**: 通过 WS endpoint 集成
- **自定义协议引擎**: 通过统一的 engine contract 接入

### 工具链

| 工具 | 用途 |
|------|------|
| Python >=3.10 | Scrapling 运行环境 |
| Playwright | 浏览器自动化 |
| uv | Python 包管理 |
| codex-agent | 入口 agent |
| opencode | CLI 工作流驱动 |

---

## 7. 治理约束

### repo:// 语义

- 所有对 Obsidian 项目页的引用使用 `repo://<repo_id>/<path>` 格式
- 不记录宿主机绝对路径
- `repo://orbitos` 映射到 Obsidian 仓库根目录
- `repo://chrome-agent` 映射到本仓库根目录

### Binding 引用

- 本规划的 binding 声明在 `openspec/changes/governance-and-capability-rebuild/binding.md`
- 后续各 Phase 的 change 需在各自的 binding 中声明依赖本规划

### 决策记录索引

- `docs/decisions/` 存放所有技术决策记录
- 命名格式: `YYYY-MM-DD-<topic>.md`
- 每个决策记录包含: context、decision、consequences

### Spec 标准

- 遵循 Orbitos Spec Standard v0.3
- 规范真源位于 `openspec/specs/<capability-id>/spec.md`
- 项目页面不得替代 spec delta 作为实现与验证依据

### 回写规则

- 只同步结论、状态、摘要与链接
- 不复制整份 spec/design/tasks
- 项目页面只保留治理入口、最新状态摘要与回写规则
- 阶段规划与运行细节下沉到子页

---

## 附录 A: 参考文档

| 文档 | 位置 |
|------|------|
| 治理重建 Proposal | `openspec/changes/governance-and-capability-rebuild/proposal.md` |
| 治理重建 Design | `openspec/changes/governance-and-capability-rebuild/design.md` |
| Master Planning Spec | `openspec/changes/governance-and-capability-rebuild/specs/master-plan/spec.md` |
| Scrapling-first 规范 | `openspec/specs/scrapling-first-browser-workflow/spec.md` |
| Scrapling-first 决策 | `docs/decisions/2026-04-23-scrapling-first-workflow.md` |
| 之前 Re-scope 规划 | `docs/plans/2026-03-30-chrome-agent-goal-scope-realignment-design.md` |
