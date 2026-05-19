# Proposal

## 问题定义

`fix-pipeline-quality-gaps` change 暴露了多文件间职责重叠的系统性结构问题。当前存在以下重复/碎片化模式：

1. **YAML frontmatter 解析 6 处独立实现**：`orchestrate.py`（`---` split 方式）、`sample_converter.py`/`iterate.py`/`freeze.py`/`main.py`/`standalone.py`（各自 regex 方式），格式相同但实现不共享
2. **速率限制配置重复**：`orchestrate.py` 和 `rate_limit.py` 包含完全相同的 `RateLimitConfig` dataclass、`_load_anti_crawl_strategy()`、`resolve_rate_limit_config()`，且 `run_pipeline()` 使用自己的版本而非 `rate_limit.py` 的
3. **排除分类解析内联**：`_resolve_exclude_categories()` 内联在 `orchestrate.py` 中，无法被 explore 路径复用

这些模式已被规划文档标记为"双实现分裂 (Dual Implementation)"和"God Object (单文件过载)"。本次 Change 1 提取共享库 `scripts/lib/`，消除直接代码重复，为后续的转换器统一（Change 2）和 orchestrator 拆分（Change 3）提供基础。

## 范围边界

**范围内：**
- 新建 `scripts/lib/` Python 包，包含 `strategy_loader.py` 和 `config_resolver.py`
- 将 `orchestrate.py` 的 `parse_strategy()` → `lib/strategy_loader.py`
- 将 `orchestrate.py` + `rate_limit.py` 的 `RateLimitConfig`/`resolve_rate_limit_config()`/`load_anti_crawl_strategy()` → `lib/config_resolver.py`
- 将 `orchestrate.py` 的 `_resolve_exclude_categories()` → `lib/config_resolver.py`
- 清理 `orchestrate.py` 中的重复函数定义
- 删除 `rate_limit.py`（内容已迁移至 `lib/config_resolver.py`）
- 更新 `__init__.py` 和 `pipeline.py`（backcompat shim）的导出路径

**范围外：**
- 不统一其余 5 处独立的 YAML frontmatter 解析（`sample_converter.py`、`iterate.py`、`freeze.py`、`main.py`、`standalone.py`、`strategy_scaffold_generator.py`）
- 不改动 `architecture_gate.py` 的策略读取逻辑
- 不改动 Node.js 侧的 `chrome-agent-cli.mjs`
- 不涉及转换器合并（Change 2）
- 不涉及包重命名（Change 3）
- `parse_frontmatter_from_content()` 作为预留占位写入但不被调用

## Capabilities

### New Capabilities

- `shared-strategy-loader`: 提供统一的策略 YAML frontmatter 解析入口（`parse_strategy()` 和占位的 `parse_frontmatter_from_content()`），使管线侧和 explore 侧可共享同一套解析逻辑
- `shared-config-resolver`: 提供统一的速率限制配置解析（`resolve_rate_limit_config()`）和排除分类解析（`resolve_exclude_categories()`），消除 `orchestrate.py` 与 `rate_limit.py` 之间的代码重复

### Modified Capabilities

- `mediawiki-api-extraction-pipeline`: 管线编排模块中的 `parse_strategy()`、`resolve_rate_limit_config()`、`_resolve_exclude_categories()` 函数被提取至共享库，`orchestrate.py` 通过导入方式使用；行为完全不变，仅代码组织变化

## Capabilities 待确认项

- [x] 能力清单已与用户确认（基于规划文档 + 源码审计结果，已通过 ask_user 确认设计决策）

## Impact

| 维度 | 影响 |
|------|------|
| 代码文件 | 新建 3 个（`lib/__init__.py`、`lib/strategy_loader.py`、`lib/config_resolver.py`）；修改 2 个（`orchestrate.py`、`__init__.py`、`pipeline.py`）；删除 1 个（`rate_limit.py`） |
| 测试 | 无新增/修改测试；现有测试应全部通过 |
| 外部接口 | 无变化 — 所有导出的公共符号保持相同名称和签名 |
| 运行时 | 无变化 — 纯代码移动，行为完全不变 |
| 风险 | 低 — 先创建新包，逐个移动函数并验证，最后删除旧代码 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `openspec/specs/pipeline/pipeline-core.md`
  - `openspec/specs/agents-governance/spec.md`
  - `docs/plans/2026-05-19-structure-refactor-and-docs.md`
