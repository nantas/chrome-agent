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
| C9 | **测试义务**：修改 `scripts/lib/`、`scripts/pipeline/pipeline/phases/`、`scripts/lib/extraction/` 时必须在 `tests/` 新增或更新对应测试；修改站点策略时必须运行 `python3 scripts/test_runner.py site-samples --domain <domain>` 确认回归通过。代码任务遵循 vertical slice TDD（详见 `08-tech-stack.md` §4 TDD 约定） | 新代码无测试覆盖 / 回归未捕获 |
| C10 | **全局 skill/runtime 同步**（同 C4 的「改 X 后必须同步 Y」模式）：修改 tracked files——`scripts/chrome-agent-runtime.mjs`、`scripts/chrome-agent-cli.mjs`、`skills/chrome-agent/SKILL.md`——后，必须将改动同步到全局副本（`~/.agents/scripts/chrome-agent.mjs`、`~/.agents/skills/chrome-agent/SKILL.md`）并刷新 `~/.agents/scripts/.chrome-agent-installed-hash` 至当前 `git rev-parse HEAD`。详见 [chrome-agent-global-install](docs/playbooks/chrome-agent-global-install.md) 的 Case 6 与 Installed Hash Semantics | 全局副本与仓库源漂移 / doctor 误判 freshness / 其它机器拿不到改动 |

## 1. Service Identity

**chrome-agent** 是跨仓库网页抓取服务。核心原则：Scrapling-first、workflow-driven、read-only by default、证据驱动。

范围：网页内容获取、前端调试、经验积累。范围外（v1）：凭据管理、自动化框架。
→ 全景详见 [系统总览](docs/architecture/01-overview.md)

## 2. Capability Framework (4-Dimensional Model)

chrome-agent 的业务能力按 4 维模型（ADR 0013）组织。
完整目标架构及每项能力的决策树流程图见 [00-target-architecture](docs/architecture/00-target-architecture.md)。

| 能力 (A) | 子能力 | 内核 | 镜像 | 变体机制 | 说明 |
|----------|--------|------|------|---------|------|
| **fetch** | — | `pipeline/phases/fetch.py` (MediaWiki API) / `pipeline/phases/fetch_cdp.py` (CDP cache) | `explore/probe_chain.py` (引擎探测) | — | .mjs 路由到 pipeline fetch 内核（`ApiClient`），不再实现自有 API client |
| **convert** | — | `lib/extraction/converter.py` (selectolax, 可选 wiki_domain) + `convert_page_full()` 共享编排入口 | explore/pipeline/cdp 三路径薄壳编排器 | 策略配置驱动 | D 轴分叉：wikitext→MD 为独立 format_converter |
| **extract** | infobox / preprocess / card_stats / link_fix | `lib/extraction/` (共享内核) | — | 策略配置驱动 | preprocessor 统一 always-full-cleanup（无 context 分支） |
| **discover** | site_analysis | `scripts/explore/` (8 步管线) | — | — | pipeline 不再自行发现页面，清单来自 explore 冻结的 strategy |
| **assemble** | — | `pipeline/phases/assemble.py` | — | — | .mjs mergeMarkdownFiles 为基础设施工具 |

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

`docs/adr/` 内。命名 `NNNN-slug.md`（四位数编号，kebab-case 标题）。每份含标题、状态、背景、决策、后果。与 `grill-with-docs` / `improve-codebase-architecture` skill 对齐。

历史决策（2026-03 至 2026-05）已从旧 `docs/decisions/`（日期格式）迁移至 `docs/adr/0004-0012`。

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
| P0 | `docs/architecture/00-target-architecture.md` | 4 维目标架构：能力注册表、声明 Schema、等价契约 |
| P1 | `docs/adr/` | 架构决策记录（ADR），编号格式，grill-with-docs skill 自动使用 |
| P2 | `docs/playbooks/` | 操作手册（抓取/fallback/认证） |
| P2 | `docs/setup/` | 环境配置 |
| P0 | `CONTEXT.md` / `CONTEXT-MAP.md` | 领域语言词汇表、模块关系图 |
| P0 | `docs/GOVERNANCE.md` | 治理工作流：文档体系、change 链路、SSOT 仲裁、维护检查清单 |
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

| 应用层依赖清单 | `requirements.txt`（仓库根） | Python 依赖 SSOT（bs4 / selectolax / pyyaml / markdownify / requests）|
| Python 解析策略 | `scripts/lib/python-resolver.mjs` → `resolveAppPython()` | `.venv/bin/python` 优先，`CHROME_AGENT_PYTHON` 覆盖，system `python3` fallback |
### 架构 & 规范 SSOT

| 知识领域 | 真源文件 | 说明 |
|----------|----------|------|
| 能力行为规范 | `openspec/specs/` | 已冻结规范，变更走 `openspec/changes/` |
| 系统架构全景 | `docs/architecture/01-overview.md` | 多后端架构 + 目录结构 |
| 目标能力架构 | `docs/architecture/00-target-architecture.md` | 4 维模型：能力注册表、声明 Schema、等价契约 |
| 管线数据流 | `docs/architecture/02-pipeline-flow.md` | 五阶段管线 + orchestrator 编排 |
| 策略 Schema | `docs/architecture/03-strategy-schema.md` | frontmatter 字段 + 策略类型 |
| 转换器架构 | `docs/architecture/05-converter-architecture.md` | 两阶段转换 + 共享提取引擎 |
| 引擎选择 & fallback | `docs/architecture/06-engine-selection.md` | 决策树 + 评分机制 |
| Explore 工作流 | `docs/architecture/07-explore-workflow.md` | deep discovery 管线 |
| 技术栈 & 开发约定 | `docs/architecture/08-tech-stack.md` | 依赖 + 语言规范 + 常见坑 |
| CLI 命令参考 | `docs/architecture/04-cli-reference.md` | 命令路由 + 参数签名 |

| Python 环境治理 | `openspec/specs/app-layer-venv-governance/spec.md` + `docs/adr/0002` / `docs/adr/0003` + CONTEXT.md | 应用层 vs 引擎层 venv 边界、懒触发 preflight 生命周期、依赖声明 SSOT |
| 治理工作流 | `docs/GOVERNANCE.md` | 文档体系设计、各类型生命周期、change 工作流完整链路、SSOT 冲突仲裁、维护检查清单 |
## 11. Prerequisite Reading by Task

> 执行开发任务前，按任务类型完成必读。未读必读文档就开始改代码 = 违反开发流程。

### 通用必读（所有开发任务）

| 优先级 | 文档 | 理由 |
|--------|------|------|
| **P0** | 本文件 §0.5 Hard Constraints | 技术红线 |
| **P0** | `docs/architecture/00-target-architecture.md` | 目标能力架构：知道每个模块的维度坐标、关系类型、等价契约 |
| **P0** | `docs/architecture/01-overview.md` | 系统全景 + 目录结构，不知道代码在哪就不能改 |
| **P0** | `docs/architecture/08-tech-stack.md` | 依赖、语言规范、常见坑 |
| **P0** | `docs/GOVERNANCE.md` | 治理工作流：文档类型生命周期、change 链路、SSOT 仲裁、反模式 |

### 按任务类型必读

| 任务类型 | 必读文档 | 关键关注点 |
|----------|----------|------------|
| **改 Pipeline**（`scripts/pipeline/`） | `00-target-architecture.md` + `02-pipeline-flow.md` | 4 维能力坐标 + 五阶段编排 |
| **改 Explore**（`scripts/explore/`） | `00-target-architecture.md` + `07-explore-workflow.md` | 4 维能力坐标 + Deep discovery 阶段 |
| **改/新增策略**（`sites/strategies/`） | `03-strategy-schema.md` + `07-explore-workflow.md` | frontmatter 字段、策略类型、Explore→Pipeline 桥接 |
| **改/新增引擎**（引擎相关） | `06-engine-selection.md` + `configs/engine-versions.json` | 评分机制、fallback 链、版本同步流程 |
| **改 Python 环境/依赖**（`requirements.txt`、preflight 脚本、`python-resolver.mjs`） | CONTEXT.md + `docs/adr/0002` + `docs/adr/0003` + `docs/architecture/08-tech-stack.md` §1 | 应用层/引擎层 venv 边界、懒触发生命周期、`resolveAppPython()` 解析策略 |
| **改 CLI**（`scripts/*.mjs`） | `04-cli-reference.md` | 命令路由、ESM 规范、函数声明风格 |
| **改共享库**（`scripts/lib/`） | `00-target-architecture.md` + `05-converter-architecture.md` | 4 维 convert 模型 + 两阶段转换 |
| **改 Shell 脚本**（`scripts/*.sh`） | `08-tech-stack.md` §2.3 | `set -euo pipefail`、路径计算模式 |
| **改 runtime/cli/SKILL.md**（全局同步） | `docs/playbooks/chrome-agent-global-install.md` | tracked files 清单、ahead / 手动同步（Case 6）、installed-hash 刷新、C10 约束 |
| **新增能力规范** | `00-target-architecture.md` §2 声明 Schema + `openspec/specs/` 同类文件 | 先确定维度坐标，再写行为 spec |
| **测试相关** | `08-tech-stack.md` §4 + testing-governance specs | 测试目录约定、runner 命令、站点样本机制、C9 测试义务 |

---

## Agent Skills

> 本区块记录项目中可用的 agent skill 及其注册信息。
> 由 `$setup-matt-pocock-skills` 初始化。

| Skill | 用途 | 触发条件 |
|-------|------|----------|
| _暂无已注册 skill_ | | |

### Skill 安装记录

_尚无 skill 安装记录。_
