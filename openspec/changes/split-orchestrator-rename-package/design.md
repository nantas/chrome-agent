# Design

## Context

Change 1（提取共享库 `lib/`）和 Change 2（统一提取引擎 `lib/extraction/`）已完成。`orchestrate.py` 已改用 `lib/` 的 `parse_strategy` 和 `resolve_rate_limit_config`，但仍是 1078 行 God Object，承担 10 种不相关职责。

当前 `orchestrate.py` 的函数分布（基于实际审计）：

| 函数 | 行号范围 | 行数 | 职责 |
|------|---------|------|------|
| Exit 常量 | L37-54 | 18 | 退出码定义 |
| `PipelineStrategies` | L71-76 | 6 | 数据容器 |
| Registry + 工厂 | L84-193 | 110 | 策略注册表 + `build_pipeline` + `derive_capabilities` |
| `validate_api_config` | L195-218 | 24 | API 校验 |
| Discovery summary | L225-474 | 250 | 发现摘要构建 + 5 辅助函数 |
| `run_phase_fetch` | L477-583 | 107 | Phase Fetch 编排 |
| `run_phase_convert` | L585-690 | 106 | Phase Convert 编排 |
| `run_pipeline` | L692-1078 | 387 | 主编排 |

包名 `mediawiki-api-extract` 含连字符，导致 `__main__.py` 需要 subprocess re-invoke workaround，且 3 处 CLI 硬编码路径需在重命名后统一更新。

## Goals / Non-Goals

**Goals:**
- 将 `orchestrate.py` 拆分为 4 个独立模块 + 1 个精简的 orchestrator
- 将 `scripts/mediawiki-api-extract/` 重命名为 `scripts/pipeline/`
- 更新所有 import 路径、CLI spawn 路径、logger 名称
- 保持端到端行为完全不变

**Non-Goals:**
- Phase 文件重命名（`phase_0` → `discovery_homepage`）— 属于 Change 4
- CLI `runCrawl()` 大函数拆分 — 属于 Change 5
- 任何功能变更或行为优化
- `converters/`、`strategies/`、`standalone.py` 的内部重构

## Decisions

### D1: 拆分顺序 — 先拆模块，后重命名包

**决策**：先在现有包结构内完成模块拆分（Step 3.1-3.4），验证通过后再执行包重命名（Step 3.5）。

**理由**：拆分涉及函数移动和 import 更新，包重命名涉及目录级操作和全局字符串替换。分两步执行可以将两类错误隔离，避免混在一起难以定位。

### D2: `phases/` 作为子目录 — 为 Change 4 预留

**决策**：创建 `pipeline/phases/` 目录存放 `fetch.py` 和 `convert.py`，而非平铺在 `pipeline/` 下。

**理由**：Change 4 将把 `phase_0.py`、`phase_a.py`、`phase_b.py`、`phase_c.py` 也移入 `phases/` 并重命名。预先创建目录结构可以减少 Change 4 的文件移动量。

### D3: `__main__.py` 简化 — 删除 re-invoke

**决策**：`pipeline` 无连字符，直接使用标准 `python3 -m scripts.pipeline` 调用。`__main__.py` 简化为仅 `from .cli import main` + 入口调用。

**理由**：当前 workaround 仅因 `mediawiki-api-extract` 含连字符而存在。重命名后不再需要。

### D4: Logger 名称统一为 `pipeline`

**决策**：全局替换 `getLogger("mediawiki-api-extract")` 为 `getLogger("pipeline")`，子模块使用点分格式如 `getLogger("pipeline.converters")`。

**理由**：logger 名称应与包名一致。已有的 `getLogger("mediawiki-api-extract.converters")` 改为 `getLogger("pipeline.converters")` 保持层级关系。

### D5: `strategies.py` 代理文件保留但更新 docstring

**决策**：`scripts/pipeline/strategies.py` 保留为代理文件，更新顶部 docstring 中的旧包名引用。

**理由**：该文件仅为 `from scripts.mediawiki_api_extract.strategies import X` 提供兼容路径。包重命名后更新 docstring 即可。

### D6: 拆分后 `pipeline/__init__.py` 导出策略

**决策**：`pipeline/pipeline/__init__.py` 从 `orchestrator.py`、`registry.py` 重新导出所有公共 API，保持 `cli.py` 不需要修改符号名。

**理由**：`cli.py` 通过 `from .pipeline import run_pipeline` 调用。拆分后需要确保 `pipeline/__init__.py` 仍然导出 `run_pipeline`。registry 的公共 API（`STRATEGY_REGISTRY` 等）也通过 `__init__.py` re-export 供外部使用。

## Risks / Migration

### R1: Import 循环风险

`phases/convert.py` 需要 `registry.build_pipeline()` → `registry` 依赖 `..strategies` → `strategies` 不依赖 `phases`。依赖链单向，无循环风险。但实现时需确认 `phases/convert.py` 不意外引入对 `orchestrator.py` 的 import。

**缓解**：每个新模块创建后立即验证 `python3 -c "from scripts.pipeline.pipeline.phases.fetch import run_phase_fetch"` 无循环 import 错误。

### R2: 相对路径层级

包重命名后，`pipeline/pipeline/phases/` 中的文件使用 `...lib` 上溯 3 层。重命名前后层级不变（`mediawiki-api-extract/pipeline/phases/` → `pipeline/pipeline/phases/`），但仍需逐文件验证。

**缓解**：重命名后执行 `python3 -m scripts.pipeline --help` 确认 import 正常。

### R3: 全局替换误伤

`mediawiki-api-extract` 和 `mediawiki_api_extract` 两形式的全局替换需要精确匹配，避免误改注释中不应变更的历史引用。

**缓解**：使用 `sed` 精确匹配并逐文件检查 `git diff`。

### R4: `lib/config_resolver.py` 的 logger 名称

`lib/config_resolver.py` 当前使用 `getLogger("mediawiki-api-extract")`，属于 `lib/` 模块但 logger 名称跟随管线包。重命名时应同步更新为 `getLogger("pipeline")` 或 `getLogger("pipeline.config")`。

**缓解**：作为全局 logger 更新的一部分处理。
