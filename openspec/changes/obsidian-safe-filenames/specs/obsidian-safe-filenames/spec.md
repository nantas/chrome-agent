# Specification Delta

## Capability 对齐（已确认）

- Capability: `output-lifecycle` / `pipeline-convert-phase`
- 来源: 需求报告 — 从下游 Obsidian vault 使用场景反推的治理约束
- 变更类型: `enhancement`
- 用户确认摘要: chrome-agent 输出作为 Obsidian vault 使用时，文件名与目录名中的空格会导致 wikilink 引用失效或需要全路径显式指定

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## 背景与问题

### 下游场景

chrome-agent 爬取 wiki 数据后输出的 Markdown 文件经常被直接作为 **Obsidian vault** 的 `30-raw/` 层使用。下游的 synthesis digest 文档使用 Obsidian wikilink（`[[Bare Name]]`）引用这些 raw 页面。

### 实际故障案例

BoI wiki 消化任务中，synthesis 文档 `synergy-design-methodology.md` 包含 44 个物品 wikilink（如 `[[Mom's Knife]]`、`[[Car Battery]]`）。

- chrome-agent 输出文件名：`Mom's_Knife.md`（空格→下划线）
- Obsidian wikilink：`[[Mom's Knife]]`
- **结果**：Obsidian 的模糊匹配无法将 `Mom's Knife` 解析为 `Mom's_Knife.md`，wikilink 显示为未创建页面
- **修复成本**：需人工补全 34 个链接为完整 vault 路径 `[[30-raw/.../Mom's_Knife|Mom's Knife]]`

### 根因分析

虽然 `title_to_filepath()` 已实现空格→下划线替换，但：
1. 这是**隐式实现**，未在任何规范中明确声明为 Obsidian 兼容性约束
2. 目录分配（`target_directory`）依赖策略中的 `dir` 字段，目前策略作者可能无意中使用带空格的目录名
3. 缺乏**验证机制**：管线未在输出前检查文件名/路径是否包含空格

## ADDED Requirements

### Requirement: obsidian-safe-filename-contract

管线输出层（`convert` phase 的 `title_to_filepath` 调用链） SHALL 保证所有生成的 `.md` 文件名和目录名**不包含空格字符**（U+0020）。

#### 范围定义

| 层级 | 当前处理 | 约束 |
|------|---------|------|
| 文件名（`target_filename`） | `title_to_filepath()` 已替换空格为下划线 | ✅ 已满足，需显式规范 |
| 目录名（`target_directory`） | 来自策略 `api.homepage.categories[].dir` | ⚠️ 需策略验证 + 运行时断言 |
| Cache 文件名 | `raw_to_cache_filename()` 已替换空格 | ✅ 已满足 |

#### 策略层验证

策略文件（`sites/strategies/*.md`）的 `api.homepage.categories` 中，所有 `dir` 值 SHALL 不包含空格。

**验证位置**：策略加载时（`lib/strategy_loader.py` 或策略 schema 校验）。

#### 运行时断言

管线在页面分配后（`page_assigner.py` 返回前）和文件写入前（`convert.py` / `assemble.py`）SHALL 执行断言：

```python
assert " " not in target_directory, f"target_directory contains space: {target_directory}"
assert " " not in target_filename, f"target_filename contains space: {target_filename}"
```

断言失败 SHALL 视为 **pipeline error**，触发 handoff 而非静默写入。

#### 向后兼容

现有已处理下划线的文件名（如 `Mom's_Knife.md`）无需变更，仅对新增/变更的管线代码施加约束。

### Requirement: filename-sanitization-spec-explicit

`title_to_filepath()` 和 `raw_to_cache_filename()` 的 docstring 及所在模块的文档 SHALL 明确声明：

> "空格字符（U+0020）被替换为下划线（U+005F），以确保 Obsidian vault 兼容性。"

#### 代码位置

- `scripts/pipeline/strategies/__init__.py` — `title_to_filepath()` docstring
- `scripts/pipeline/pipeline/cache.py` — `raw_to_cache_filename()` docstring

### Requirement: strategy-schema-dir-validation

策略 schema（`sites/strategies/` frontmatter 或 `configs/` 中的 strategy schema 定义）SHALL 对 `api.homepage.categories[].dir` 添加约束：`pattern: '^[^ ]+$'`（不含空格）。

## MODIFIED Requirements

_None_

## REMOVED Requirements

_None_

## RENAMED Requirements

_None_

## Verification Plan

1. 读取 BoI strategy 文件，确认 `categories[].dir` 值无空格
2. 对现有策略文件运行 schema 校验，确认无 `dir` 含空格
3. 在管线中注入带空格的 `target_directory` 模拟数据，确认断言抛出
4. 运行 `convert` phase 端到端测试，确认输出文件名无空格
