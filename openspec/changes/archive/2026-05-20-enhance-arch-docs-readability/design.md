# Design

## Context

`finish-refactor-cleanup` change 完成后，`docs/architecture/` 中的 3 篇文档存在可读性缺口（缺少 ASCII 图/流程图），2 篇文档存在路径/命名过时问题。审计发现：

- 已有良好图示的文档：`01-overview.md`、`06-engine-selection.md`、`07-explore-workflow.md`
- 缺图示的文档：`03-strategy-schema.md`、`04-cli-reference.md`、`08-tech-stack.md`
- 路径过时：`02-pipeline-flow.md`、`05-converter-architecture.md`

## Goals / Non-Goals

**Goals:**
- 为 3 篇文档增加 ASCII 图/流程图（共 7 个视觉元素）
- 为 2 篇文档更新过时的 Phase 命名和文件路径
- 所有图表使用 ASCII art 格式（兼容纯文本阅读和 agent 处理）
- 图表准确反映当前代码状态

**Non-Goals:**
- 不修改已有良好图示的 3 篇文档
- 不新增文档文件
- 不修改代码
- 不修改 AGENTS.md

## Decisions

### D1: ASCII Art 格式

**Decision**: 所有图表使用 ASCII box-drawing 字符（`┌─┐│└┘├┤┬┴┼`），不使用 Unicode 宽字符。

**Rationale**: 纯文本兼容性最好，agent 可直接解析，`grep` 和 `head` 操作正常。

### D2: 图表插入位置

**Decision**: 图表插入在对应章节的开头（"概述"节之后、详细列表之前），作为导航入口。

| 文档 | 图表 | 插入位置 |
|------|------|---------|
| `03-strategy-schema.md` | 系统上下文图 | "概述"节末尾 |
| `03-strategy-schema.md` | 字段层级树 | "字段详细说明"节开头 |
| `03-strategy-schema.md` | content_profile 路由图 | "content_profile 合法值"节开头 |
| `04-cli-reference.md` | 命令路由决策树 | "概述"节末尾 |
| `04-cli-reference.md` | 管线阶段流程图 | Pipeline 子命令节开头 |
| `08-tech-stack.md` | 组件依赖关系图 | "Runtime Dependencies"节前（新增节） |
| `08-tech-stack.md` | 安装脚本链流程图 | "External Engine Dependencies"节后 |

### D3: Phase 命名更新策略

**Decision**: 在 `02-pipeline-flow.md` 中使用 `sed` 精确替换 Phase 命名。

替换映射：
```
Phase 0 → homepage discovery (作为描述性文本)
Phase A → allpages discovery
Phase B → fetch / convert (拆分为两个阶段名)
Phase C → assembly
run_phase_0() → run_homepage_discovery()
run_phase_a() → run_allpages_discovery()
run_phase_c() → run_assemble()
```

标题中已有英文名（如 "### Phase A: Allpages Discovery"），更新策略：
- 标题改为 `### Allpages Discovery (allpages discovery)`
- 不再使用 Phase 编号作为主标识

### D4: Converter 路径更新策略

**Decision**: 在 `05-converter-architecture.md` 中：
- "Pipeline Converters" 表拆分为"Shared Extraction Library"和"Pipeline Converters"两个表
- `html_to_markdown.py` 从 pipeline 表移至 lib 表
- §2.3 "Design Decision" 章节更新理由为当前实际状态

### D5: 图表溯源

**Decision**: 每个 ASCII 图下方添加注释行标明数据来源：
```
<!-- Source: scripts/pipeline/pipeline/orchestrator.py:76 run_pipeline() -->
```
这使未来代码变更时能快速找到需要同步更新的图表。

## Risks / Migration

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| ASCII 图与代码实际状态不一致 | Low | Medium | 图表标注源文件路径 + 行号，变更时可追溯 |
| Phase 命名更新不完整 | Low | Low | `grep -n "Phase [0ABC]" docs/architecture/02-pipeline-flow.md` 验证零残留 |
| Converter 路径更新不完整 | Low | Low | `grep "pipeline/converters/html_to_markdown" docs/architecture/05-converter-architecture.md` 验证零残留 |
| 文档格式破坏 | Low | Low | 纯文本格式，`git diff` 审查变更 |
