# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `docs-architecture` spec 的 8 篇文档清单与 AGENTS.md 内容注入映射一致（spec docs-architecture § Requirement: docs-agents-md-content-injection）
- [x] 1.2 确认 `agents-governance` spec 的 6 项 LSP 审计修复清单完整（spec agents-governance § Requirement: AGENTS.md LSP Audit and Repair）
- [x] 1.3 确认 `spec-consolidation` 的 22 域合并映射覆盖所有 74 个源 spec（spec spec-consolidation § Requirement: spec-merge-by-domain）
- [x] 1.4 确认 expired-path 替换表覆盖所有 Phase 1~3 重构涉及的路径变更（spec spec-consolidation § Requirement: stale-path-references-fix）

## 2. 核心实现任务

### Step 0: AGENTS.md 过时修复

- [x] 2.0.1 引擎表格补全：增加 `mediawiki-api` (rank 0) 和 `obscura-serve-pool` (rank 3)，修正 `scrapling-fetch` rank 3→4
  - **验证**: `grep "mediawiki-api" AGENTS.md` 匹配；`grep "obscura-serve-pool" AGENTS.md` 匹配
- [x] 2.0.2 Python 3.9 兼容声明更新：`sample_converter.py` "当前有此问题" → "已在 Change 2 修复（改用 Optional）"
  - **验证**: LSP hover `sample_converter.py:8` 确认 `from typing import Optional`
- [x] 2.0.3 测试路径修正：`orchestrate.py` → `discovery_summary.py`
  - **验证**: `grep "orchestrate.py 中的纯函数" AGENTS.md` 返回 0
- [x] 2.0.4 目录结构补全：`scripts/` 下增加 `lib/` 条目
  - **验证**: `grep "scripts/lib/" AGENTS.md` 匹配
- [x] 2.0.5 Phase 命名更新：`Phase A → Phase Fetch → Phase Convert → Phase C` → `homepage/allpages discovery → fetch → convert → assembly`
  - **验证**: `grep "Phase A" AGENTS.md` 仅匹配参考索引中的链接文本（非流程描述）

### Step 1: 冻结 Change Specs

- [x] 2.1.1 复制 `extract-shared-lib/specs/shared-strategy-loader/` → `openspec/specs/shared-strategy-loader/`
- [x] 2.1.2 复制 `extract-shared-lib/specs/shared-config-resolver/` → `openspec/specs/shared-config-resolver/`
- [x] 2.1.3 合并 `extract-shared-lib/specs/mediawiki-api-extraction-pipeline/` delta 到 `openspec/specs/mediawiki-api-extraction-pipeline/spec.md`
  - **验证**: 源 delta 的所有 `## ADDED/MODIFIED Requirements` 出现在目标文件中
- [x] 2.1.4 复制 `split-orchestrator-rename-package/specs/pipeline-registry/` → `openspec/specs/pipeline-registry/`
- [x] 2.1.5 复制 `split-orchestrator-rename-package/specs/pipeline-orchestration/` → `openspec/specs/pipeline-orchestration/`
- [x] 2.1.6 复制 `split-orchestrator-rename-package/specs/pipeline-package-identity/` → `openspec/specs/pipeline-package-identity/`
- [x] 2.1.7 复制 `split-orchestrator-rename-package/specs/pipeline-phases-fetch/` → `openspec/specs/pipeline-phases-fetch/`
- [x] 2.1.8 复制 `split-orchestrator-rename-package/specs/pipeline-phases-convert/` → `openspec/specs/pipeline-phases-convert/`
- [x] 2.1.9 复制 `split-orchestrator-rename-package/specs/pipeline-discovery-summary/` → `openspec/specs/pipeline-discovery-summary/`
  - **验证**: 9 个 spec 目录全部存在于 `openspec/specs/` 中
- [x] 2.1.10 归档 `extract-shared-lib/` → `openspec/changes/archive/`
- [x] 2.1.11 归档 `split-orchestrator-rename-package/` → `openspec/changes/archive/`
  - **验证**: `openspec/changes/extract-shared-lib/` 和 `openspec/changes/split-orchestrator-rename-package/` 不再存在

### Step 2: Spec 合并 (D2)

- [x] 2.2.1 创建 `pipeline/` 域 7 个 spec（pipeline-core, pipeline-orchestration, pipeline-discovery, pipeline-registry, pipeline-conversion, pipeline-infobox, html-preprocessing）
  - 每个 spec 逐 Requirement 从源 spec 迁移，保留所有 `### Requirement:` 块
  - 合并时执行过期路径替换（spec spec-consolidation § Requirement: stale-path-references-fix）
- [x] 2.2.2 创建 `explore/` 域 4 个 spec（explore-deep-discovery, explore-scaffold, explore-validation, explore-ki）
- [x] 2.2.3 创建 `engines/` 域 spec（engine-registry）
- [x] 2.2.4 创建 `strategy/` 域 2 个 spec（strategy-schema, strategy-lifecycle）
- [x] 2.2.5 创建 `cli/` 域 2 个 spec（cli-interface, cli-workflows）
- [x] 2.2.6 创建 `governance/` 域 3 个 spec（governance, handoff, output）
- [x] 2.2.7 创建 `shared/`, `mediawiki/`, `infra/` 域 4 个 spec（shared-lib, api, install, doctor）
- [x] 2.2.8 删除已合并的源 spec 目录（~50 个）
  - **验证**: `grep -r "specs/<old-name>" openspec/changes/` 无活跃引用
- [x] 2.2.9 过期路径残留验证（所有残留为历史归档引用，非活跃路径）
  - **验证**: `grep -r "mediawiki-api-extract\|mediawiki_api_extract" openspec/specs/` 返回 0
  - **验证**: `grep -r "orchestrate\.py" openspec/specs/` 返回 0
  - **验证**: `grep -r "infox_renderer\.py" openspec/specs/` 返回 0
- [x] 2.2.10 更新 `openspec/changes/` 中活跃 change 的 spec 引用（fix-pipeline-quality-gaps + phase-4 binding）

### Step 3: 核心架构文档 (D1)

- [x] 2.3.1 创建 `docs/architecture/01-overview.md`
  - 真源验证: LSP symbols `chrome-agent-cli.mjs` main(), `pipeline/orchestrator.py` run_pipeline()
  - 注入: AGENTS.md §1 (服务身份摘要), §4 (目录结构更新版含 scripts/lib/)
- [x] 2.3.2 创建 `docs/architecture/02-pipeline-flow.md`
  - 真源验证: LSP symbols `orchestrator.py`, `phases/` 5 文件
  - 注入: AGENTS.md §3 API管线 Phase 流程（去旧名化）
- [x] 2.3.3 创建 `docs/architecture/03-strategy-schema.md`
  - 真源验证: LSP hover `registry.py:_STRATEGY_REGISTRY`
  - 注入: AGENTS.md §8 Pipeline Strategy Schema ID 清单 + platform_variant
  - 声明为 YAML frontmatter 唯一权威真源
- [x] 2.3.4 创建 `docs/architecture/04-cli-reference.md`
  - 真源验证: LSP symbols `chrome-agent-cli.mjs:parseArgs()`, `main()`
- [x] 2.3.5 创建 `docs/architecture/05-converter-architecture.md`
  - 真源验证: LSP symbols `lib/extraction/infobox.py:extract_infobox()`, `preprocessor.py:preprocess_html()`
- [x] 2.3.6 创建 `docs/architecture/06-engine-selection.md`
  - 真源验证: `configs/engine-registry.json` 10 引擎
  - 注入: AGENTS.md §3 引擎选择策略(全文), §9 已注册引擎概览(更新版), 版本治理
- [x] 2.3.7 创建 `docs/architecture/07-explore-workflow.md`
  - 真源验证: LSP symbols `chrome-agent-cli.mjs:runExplore()`, `scripts/explore/main.py`
  - 注入: AGENTS.md §3 Deep Discovery 8步, 样本转换 CLI
- [x] 2.3.8 创建 `docs/architecture/08-tech-stack.md`
  - 真源验证: `configs/engine-versions.json`, `package.json`, `scripts/explore/requirements.txt`
  - 注入: AGENTS.md §6 仓库结构, Node.js/Python/Shell约定, LSP模式1-4, 运行测试, 版本检查, 常见陷阱

### Step 4: AGENTS.md 瘦身

- [x] 2.4.1 删除 AGENTS.md 中已迁移至 `docs/architecture/` 的段落，每段替换为 `→ 详见 docs/architecture/<file>.md`
  - 迁移映射见 spec agents-governance § Requirement: AGENTS.md Architecture Content Migration
- [x] 2.4.2 缩减 AGENTS.md Reference Index，增加 `docs/architecture/` 条目
  - **验证**: `wc -c AGENTS.md` ≤ 3500 字节
- [x] 2.4.3 AGENTS.md 第 8 节策略库治理中删除 Pipeline Strategy Schema ID 清单，替换为链接
  - **验证**: `grep "当前注册 ID 清单" AGENTS.md` 返回 0
- [x] 2.4.4 AGENTS.md 第 9 节引擎扩展治理中删除引擎概览表，替换为链接
  - **验证**: `grep "| \`scrapling-get\`" AGENTS.md` 返回 0

## 3. 收敛与验证准备

- [x] 3.1 整理 Architecture Gate 回归检查点：确认 `docs/architecture/` 下 8 个文件全部存在
- [x] 3.2 整理 Spec 合并验证：`find openspec/specs -name "*.md" | wc -l` ≤ 30（含新增和合并后）
- [x] 3.3 整理过期路径残留验证：执行 Step 2.2.9 中定义的 grep 检查
- [x] 3.4 整理 AGENTS.md 瘦身验证：行数和字节数对比（修复前 ~39KB，修复后 3.3KB）
- [x] 3.5 整理 LSP 真源验证报告：8 篇架构文档已全部通过代码验证（详见各 subagent 输出）

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成 verification.md（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 verification.md 结论生成 writeback.md（回写目标: AGENTS.md, docs/plans/2026-05-19-structure-refactor-and-docs.md, README.md）
- [x] 4.3 执行 writeback.md 中定义的回写：AGENTS.md 瘦身完成、规划文档 Phase 4 已标注完成、README 已补充 docs/architecture/ 引用
