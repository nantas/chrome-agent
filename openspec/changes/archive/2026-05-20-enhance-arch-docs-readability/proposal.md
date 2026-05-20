# Proposal

## 问题定义

对 `docs/architecture/` 的 8 篇真源文档进行可读性审计发现：3 篇文档严重缺乏面向人类和 agent 的结构化视觉元素（ASCII 图、流程图、决策树），另外 2 篇存在路径/命名过时问题：

1. **`03-strategy-schema.md`** (389 行)：纯字段参考，无策略文件与管线系统的关系图、无字段层级树状图、无 `content_profile` 到 `_STRATEGY_REGISTRY` 的路由图
2. **`04-cli-reference.md`** (227 行)：纯参数表，无命令路由决策树（crawl → MediaWiki API vs Scrapling），无 `--discovery`/`--phase` 如何影响管线阶段的流程图
3. **`08-tech-stack.md`** (221 行)：纯列表，无组件依赖关系图（Node.js CLI → Python pipeline → 引擎 → 输出），无安装脚本链流程图
4. **`02-pipeline-flow.md`**：Phase 0/A/C 命名过时（应为 homepage/allpages/assembly），与 `finish-refactor-cleanup` change 后的实际代码不一致
5. **`05-converter-architecture.md`**：`html_to_markdown.py` 仍标注在 `pipeline/converters/`（实际已在 `finish-refactor-cleanup` 中移动到 `lib/extraction/converter.py`）

## 范围边界

**范围内：**
- `03-strategy-schema.md`：增加上下文位置图（策略文件在系统中的位置） + 字段层级树状图 + `content_profile` 策略路由图
- `04-cli-reference.md`：增加命令路由决策树 + 管线阶段流程图（`--discovery` / `--phase` 如何影响管线）
- `08-tech-stack.md`：增加组件依赖关系图 + 安装脚本链流程图
- `02-pipeline-flow.md`：更新 Phase 命名（Phase 0→homepage, Phase A→allpages, Phase C→assembly）
- `05-converter-architecture.md`：更新 `html_to_markdown.py` 路径引用

**范围外：**
- 不修改 `01-overview.md`、`06-engine-selection.md`、`07-explore-workflow.md`（已具备充分的视觉元素）
- 不新增文档文件（维持 8 篇结构）
- 不修改 AGENTS.md
- 不修改代码

## Capabilities

### New Capabilities

- `docs-strategy-schema-diagrams`: 为策略 schema 参考文档增加 3 个结构化视觉元素：系统上下文图（策略文件在 chrome-agent 架构中的位置）、字段层级树状图（YAML key 嵌套关系）、content_profile 策略路由图（字段值→`_STRATEGY_REGISTRY` 维度→策略类实例化）
- `docs-cli-routing-diagrams`: 为 CLI 参考文档增加 2 个结构化视觉元素：命令路由决策树（crawl/fetch/scrape/explore 的分发逻辑）、管线阶段流程图（`--discovery`/`--phase` 参数如何影响五阶段执行）
- `docs-tech-stack-dependency-graph`: 为技术栈文档增加 2 个结构化视觉元素：组件依赖关系图（Node.js CLI→Python pipeline→引擎→输出）、安装脚本链流程图（preflight 脚本的执行顺序）

### Modified Capabilities

- `docs-pipeline-flow-phase-naming`: 更新管线数据流文档中的 Phase 命名为与 `finish-refactor-cleanup` change 一致（Phase 0→homepage discovery, Phase A→allpages discovery, Phase C→assembly），同时更新函数名引用（`run_phase_0`→`run_homepage_discovery` 等）
- `docs-converter-path-update`: 更新转换器架构文档中的 `html_to_markdown.py` 路径为 `scripts/lib/extraction/converter.py`，同步更新模块清单中的文件列表

## Capabilities 待确认项

- [x] 能力清单已与用户确认（基于 session 中完成的文档审计结果，用户要求按建议整理方案）

## Impact

| 影响维度 | 详情 |
|---------|------|
| 文档变更 | 5 个文件修改，0 个新增，0 个删除 |
| 代码变更 | 无 |
| 行为变更 | 无 |
| AGENTS.md 引用 | 不变（文档路径不变） |

**每个文档的具体变更：**

| 文档 | 新增视觉元素 | 修正内容 |
|------|------------|---------|
| `03-strategy-schema.md` | ① 系统上下文图 ② 字段层级树 ③ content_profile 路由图 | — |
| `04-cli-reference.md` | ① 命令路由决策树 ② 管线阶段流程图 | — |
| `08-tech-stack.md` | ① 组件依赖关系图 ② 安装脚本链流程图 | — |
| `02-pipeline-flow.md` | — | Phase 0/A/C 命名更新 |
| `05-converter-architecture.md` | — | converter 路径更新 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：见 binding.md 的 `project_page_ref` 和 `writeback_targets`
