# AGENTS.md — chrome-agent 治理文档

## 0. Critical Rule

优先使用 `lsp` 工具（symbols / definition / references）而非 `grep` + `read`。
** 使用方法详见 `lsp-code-intelligence` skill**（自动注入）。

## 0.5 Development Hard Constraints

> 修改 `scripts/`、`configs/`、`sites/` 前必须遵守。详细说明见 [08-tech-stack](docs/architecture/08-tech-stack.md)。

| # | 约束 | 违反后果 |
|---|------|----------|
| C1 | **Python 3.9+ 兼容**：禁止裸 `X \| Y` 类型语法，用 `Optional[X]` 或加 `from __future__ import annotations` | macOS 系统 Python 3.9.6 上 TypeError |
| C2 | **Node.js 纯 ESM**：`.mjs` 文件，无 TypeScript，无编译步骤，无 CommonJS | — |
| C3 | **Pipeline 调用方式**：`python3 -m scripts.pipeline <subcommand>`，禁止直接执行 `cli.py` | `__main__.py` 入口不触发，相对导入失败 |
| C4 | **引擎版本同步**：升级引擎后必须同步 `configs/engine-versions.json` 的 `expected_version` + `expected_md5` + `expected_size` | preflight 反复重下载 / hash_mismatch |
| C5 | **测试框架**：Node.js 用 `node:test`，Python 用 `unittest`，禁止引入第三方测试依赖。通用代码测试放 `tests/` 顶层目录，运行 `python3 -m unittest discover -s tests -v` | — |
| C6 | **Shell 脚本**：`set -euo pipefail` + stderr 日志（`printf '%s\n' "$*" >&2`） | — |
| C7 | **策略注册**：新增策略必须更新 `registry.json`；frontmatter 与 registry 冲突时以 frontmatter 为准 | 策略不生效 / bootstrap 与手动创建行为不一致 |
| C8 | **函数声明风格**：Node.js 顶层用 `function xxx()` 声明，不用箭头函数 | — |
| C9 | **测试义务**：修改 `scripts/lib/`、`scripts/pipeline/pipeline/phases/`、`scripts/lib/extraction/` 时必须在 `tests/` 新增或更新对应测试；修改站点策略时必须运行 `python3 scripts/test_runner.py site-samples --domain <domain>` 确认回归通过 | 新代码无测试覆盖 / 回归未捕获 |

## 1. Service Identity

**chrome-agent** 是跨仓库网页抓取服务。核心原则：Scrapling-first、workflow-driven、read-only by default、证据驱动。

范围：网页内容获取、前端调试、经验积累。范围外（v1）：凭据管理、自动化框架。
→ 全景详见 [系统总览](docs/architecture/01-overview.md)

## 2. Capability Framework

| 对外 | 说明 | 对内 | 状态 |
|------|------|------|------|
| explore | 分析页面结构与反爬 | site-strategy | 未结构化 |
| fetch | 获取页面内容 | anti-crawl-strategy | 未结构化 |
| crawl | 策略引导遍历 | engine-registry | 已规范 |
| scrape | 策略无关爬取 | output-lifecycle | 未实现 |

→ 全景详见 [总体规划](docs/governance-and-capability-plan.md)

## 3. Governance Rules

**路由：** Content Retrieval（默认）vs Platform Analysis（深度路径）。

→ Deep Discovery 详见 `docs/architecture/07-explore-workflow.md`
→ 引擎选择 & fallback 详见 `docs/architecture/06-engine-selection.md`
→ API 管线流程详见 `docs/architecture/02-pipeline-flow.md`

**Crawl Gate:** Discovery-only → ask_user 确认 → Extraction（`--from-manifest`）。
**Explore→Crawl Gate:** partial_success 需确认；failure 不准伪造策略。
**爬取诊断：** P-line/S-line/W-line 三线归因。
**Handoff：** 内部失败 → `outputs/handoffs/<tag>/handoff.md` → Gate 停止工作流。
**认证：** 需批准、只读、Scrapling-first、会话失败切 chrome-cdp。
**报告：** 默认不产出；深度路径完整产出。

## 4. Directory Governance

> 完整目录树见 [01-overview](docs/architecture/01-overview.md)，此处为入口文件速查。

```
scripts/
├── chrome-agent-cli.mjs          ← CLI 主入口（所有命令）
├── chrome-agent-runtime.mjs      ← 全局 launcher（repo 解析）
├── lib/                          ← 共享 Python 库
│   ├── strategy_loader.py        ← 策略 frontmatter 解析
│   ├── config_resolver.py        ← 配置优先级解析
│   └── extraction/               ← 提取引擎（infobox/preprocessor/converter）
├── pipeline/                     ← MediaWiki API 管线
│   ├── __main__.py               ← python3 -m scripts.pipeline 入口
│   ├── pipeline/orchestrator.py  ← 管线编排（run_pipeline）
│   └── pipeline/registry.py      ← _STRATEGY_REGISTRY
├── explore/                      ← Deep discovery 管线
│   └── main.py                   ← explore CLI 入口
configs/
├── engine-versions.json          ← 引擎版本 SSOT
├── engine-registry.json          ← 引擎能力定义
└── backend-signatures.json       ← 平台检测签名
sites/strategies/                 ← 站点策略（frontmatter = 权威）
openspec/specs/                   ← 冻结能力规范
```

## 5. Decision Record Governance

`docs/decisions/` 内。命名 `YYYY-MM-DD-topic.md`。每份含 Context / Decision / Consequences。

## 6. Spec & Change Governance

Orbitos Spec Standard v0.3。真源：`openspec/specs/`。变更：`openspec/changes/`。

## 7. Strategy Library Governance

`strategy.md` frontmatter 为权威来源。新增策略需更新 `registry.json`。

→ Pipeline Strategy ID 清单 & `platform_variant` 详见 `docs/architecture/03-strategy-schema.md`

`_STRATEGY_REGISTRY`（`registry.py`）为 ID 唯一权威来源。扩展：实现→注册→引用。

## 8. Engine Extension Governance

新引擎通过 openspec change 接入。`configs/engine-versions.json` 为版本真源。升级须同步哈希/大小字段。

→ 引擎概览详见 `docs/architecture/06-engine-selection.md`

## 9. Reference Index

> **P0** = 所有任务必读 · **P1** = 按任务类型必读 · **P2** = 需要时查阅

### 架构文档（docs/architecture/）

| 优先级 | 文件 | 用途 |
|--------|------|------|
| P0 | `01-overview.md` | 系统全景、多后端架构、目录结构 |
| P1 | `02-pipeline-flow.md` | MediaWiki 五阶段管线详解 |
| P1 | `03-strategy-schema.md` | 策略 frontmatter 字段 + 策略类型体系 |
| P1 | `04-cli-reference.md` | CLI 命令路由 + 参数签名 |
| P1 | `05-converter-architecture.md` | 两阶段转换 + 共享提取引擎 |
| P1 | `06-engine-selection.md` | 引擎选择决策树 + fallback 机制 |
| P1 | `07-explore-workflow.md` | Deep discovery 管线 |
| P0 | `08-tech-stack.md` | 依赖、语言约定、常见坑、测试基础设施 |

### 其他文档

| 优先级 | 位置 | 用途 |
|--------|------|------|
| P2 | `docs/governance-and-capability-plan.md` | 路线图 |
| P2 | `docs/decisions/` | 架构决策记录（ADR） |
| P2 | `docs/playbooks/` | 操作手册（抓取/fallback/认证） |
| P2 | `docs/setup/` | 环境配置 |
| P2 | `openspec/specs/` | 冻结能力规范 |
| P2 | `openspec/changes/` | 进行中变更 |
| P2 | `scripts/explore/ki_lifecycle.py` | Issue 分类与修复 |
| P1 | `tests/` | 通用代码单元测试（按源码模块分组） |
| P1 | `scripts/test_runner.py` | 统一测试入口（`all` / `site-samples` / `unit`） |
| P2 | `scripts/lib/test_assertions.py` | 结构断言规则集（HTML 标签 / 链接解析 / 表格校验） |

## 10. Single Source of Truth (SSOT) Map

> 每个知识领域只有一个权威来源。其他文档为派生/摘要，冲突时以 SSOT 为准。

### 代码 & 配置 SSOT

| 知识领域 | 真源文件 | 说明 |
|----------|----------|------|
| 引擎版本清单 | `configs/engine-versions.json` | version + md5 + size，升级必同步 |
| 引擎能力定义 | `configs/engine-registry.json` | 引擎类型、评分、状态 |
| 策略 ID 注册表 | `scripts/pipeline/pipeline/registry.py` → `_STRATEGY_REGISTRY` | ID 唯一权威，代码即注册 |
| 站点策略内容 | `sites/strategies/<domain>/strategy.md` frontmatter | frontmatter > registry.json |
| 后端检测签名 | `configs/backend-signatures.json` | 平台识别规则 |
| CLI 命令定义 | `scripts/chrome-agent-cli.mjs` | 所有命令路由 + 参数解析 |

### 架构 & 规范 SSOT

| 知识领域 | 真源文件 | 说明 |
|----------|----------|------|
| 能力行为规范 | `openspec/specs/` | 已冻结规范，变更走 `openspec/changes/` |
| 系统架构全景 | `docs/architecture/01-overview.md` | 多后端架构 + 目录结构 |
| 管线数据流 | `docs/architecture/02-pipeline-flow.md` | 五阶段管线 + orchestrator 编排 |
| 策略 Schema | `docs/architecture/03-strategy-schema.md` | frontmatter 字段 + 策略类型 |
| 转换器架构 | `docs/architecture/05-converter-architecture.md` | 两阶段转换 + 共享提取引擎 |
| 引擎选择 & fallback | `docs/architecture/06-engine-selection.md` | 决策树 + 评分机制 |
| Explore 工作流 | `docs/architecture/07-explore-workflow.md` | deep discovery 管线 |
| 技术栈 & 开发约定 | `docs/architecture/08-tech-stack.md` | 依赖 + 语言规范 + 常见坑 |
| CLI 命令参考 | `docs/architecture/04-cli-reference.md` | 命令路由 + 参数签名 |

## 11. Prerequisite Reading by Task

> 执行开发任务前，按任务类型完成必读。未读必读文档就开始改代码 = 违反开发流程。

### 通用必读（所有开发任务）

| 优先级 | 文档 | 理由 |
|--------|------|------|
| **P0** | 本文件 §0.5 Hard Constraints | 技术红线 |
| **P0** | `docs/architecture/01-overview.md` | 系统全景 + 目录结构，不知道代码在哪就不能改 |
| **P0** | `docs/architecture/08-tech-stack.md` | 依赖、语言规范、常见坑 |

### 按任务类型必读

| 任务类型 | 必读文档 | 关键关注点 |
|----------|----------|------------|
| **改 Pipeline**（`scripts/pipeline/`） | `02-pipeline-flow.md` | 五阶段编排、Python 3.9 兼容、`-m` 调用方式 |
| **改 Explore**（`scripts/explore/`） | `07-explore-workflow.md` | Deep discovery 阶段、Python 3.10+ 依赖 |
| **改/新增策略**（`sites/strategies/`） | `03-strategy-schema.md` + `07-explore-workflow.md` | frontmatter 字段、策略类型、Explore→Pipeline 桥接 |
| **改/新增引擎**（引擎相关） | `06-engine-selection.md` + `configs/engine-versions.json` | 评分机制、fallback 链、版本同步流程 |
| **改 CLI**（`scripts/*.mjs`） | `04-cli-reference.md` | 命令路由、ESM 规范、函数声明风格 |
| **改共享库**（`scripts/lib/`） | `05-converter-architecture.md` | 两阶段转换模型、Python 兼容 |
| **改 Shell 脚本**（`scripts/*.sh`） | `08-tech-stack.md` §2.3 | `set -euo pipefail`、路径计算模式 |
| **新增能力规范** | `openspec/specs/` 同类文件 + `docs/decisions/` | Orbitos Spec Standard v0.3 格式 |
| **测试相关** | `08-tech-stack.md` §4 + testing-governance specs | 测试目录约定、runner 命令、站点样本机制、C9 测试义务 |
