# Proposal

## 问题定义

`scripts/mediawiki-api-extract/pipeline/orchestrate.py` 当前为 1078 行的 God Object，承担了 10 种不相关职责：策略注册表、管线工厂、能力推导、API 校验、发现摘要构建、Phase Fetch 编排、Phase Convert 编排、主编排逻辑、配置解析、退出码定义。这使得独立理解、测试和修改任何一个关注点都极为困难。

同时，包名 `mediawiki-api-extract` 含连字符，导致 `__main__.py` 需要特殊的 re-invoke workaround，且与目标架构 `pipeline` 命名不一致。包内 Python 绝对 import 路径 `scripts.mediawiki_api_extract` 与目录名 `scripts/mediawiki-api-extract` 的映射也增加了认知负担。

## 范围边界

**范围内：**
- 将 `orchestrate.py` 拆分为 4 个独立模块：`registry.py`、`discovery_summary.py`、`phases/fetch.py`、`phases/convert.py`；原文件精简为 ~300 行的 `orchestrator.py`
- 将 `scripts/mediawiki-api-extract/` 重命名为 `scripts/pipeline/`
- 更新所有 import 引用、CLI spawn 路径、logger 名称
- 简化 `__main__.py`（删除 re-invoke workaround）
- 更新 `AGENTS.md` 中 `_STRATEGY_REGISTRY` 权威来源路径

**范围外：**
- Phase 文件重命名（`phase_0` → `discovery_homepage` 等）— 属于 Change 4
- CLI `runCrawl()` 大函数拆分 — 属于 Change 5
- `html_to_markdown.py` 文件移动 — 已在 Change 2 中完成统一 infobox 集成
- 行为变更 — 纯结构重构，所有外部行为完全不变

## Capabilities

### New Capabilities

- `pipeline-registry`: 策略注册表、管线工厂与能力推导的独立模块，从 orchestrator 中提取
- `pipeline-discovery-summary`: 发现摘要构建的独立模块，含 5 个辅助函数
- `pipeline-phases-fetch`: Phase Fetch 编排的独立模块，从 orchestrator 中提取
- `pipeline-phases-convert`: Phase Convert 编排的独立模块，从 orchestrator 中提取

### Modified Capabilities

- `pipeline-orchestration`: 主编排逻辑精简为 ~300 行，仅保留 `run_pipeline()` 入口、exit 常量和 `validate_api_config()`；依赖新建的 4 个模块
- `pipeline-package-identity`: 包从 `mediawiki-api-extract` 重命名为 `pipeline`，消除连字符问题和 re-invoke workaround

## Capabilities 待确认项

- [x] 能力清单已与用户确认（基于 `docs/plans/2026-05-19-structure-refactor-and-docs.md` § Change 3 的设计确认）

## Impact

| 影响面 | 说明 |
|--------|------|
| `chrome-agent-cli.mjs` | 3 处硬编码路径更新（spawn 命令 + fallback 消息） |
| `pipeline/` 内所有 `.py` | import 路径批量更新（`mediawiki-api-extract` → `pipeline`） |
| `scripts/explore/` | 3 个文件引用路径更新（`architecture_gate.py`, `sample_converter.py`, `strategy_scaffold_generator.py`） |
| `tests/` | 1 处路径引用更新（`test_discovery_summary.py`） |
| `AGENTS.md` | `_STRATEGY_REGISTRY` 权威来源路径更新 |
| logger 名称 | ~20 处 `getLogger("mediawiki-api-extract")` → `getLogger("pipeline")` |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：`openspec/specs/agents-governance/spec.md`
  - 项目页：`docs/plans/2026-05-19-structure-refactor-and-docs.md` § Change 3
  - 回写目标：项目页状态更新 + `AGENTS.md` 路径更新
