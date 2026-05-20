# Design

## Context

Change 2 和 Change 3 完成了主要的重构工作（共享库提取、包重命名、orchestrator 拆分），但留有 2 项未闭合的清理任务：

1. `html_to_markdown.py`（813 行）仍在 `pipeline/converters/` 中，未按规划移动到 `lib/extraction/converter.py`。规划文档将此移动推迟到 Change 3 以避免两次 import 更新（Change 2 移动 + Change 3 包重命名 = 8 次 import 改动），但 Change 3 执行时遗漏了此项。

2. 5 个 phase 函数名仍为 `run_phase_0`/`run_phase_a`/`run_phase_c`/`run_phase_fetch`/`run_phase_convert`，与已重命名的文件名不一致。文件重命名完成但函数重命名未完成。

两项任务均为纯代码移动/重命名，运行时行为完全不变。`infox_renderer.py` 已在 Change 2 中删除，`html_to_markdown.py` 的 `_render_infobox_table()` 已在 Change 2 中改为调用 `lib/extraction/infobox.py`。

## Goals / Non-Goals

**Goals:**
- 将 `html_to_markdown.py` 移动到 `lib/extraction/converter.py`
- 更新 4 个 import 方（`converters/__init__.py`、`strategies/__init__.py`、`standalone.py`、`sample_converter.py`）
- 重命名 5 个 phase 函数名与对应文件的 import/call site
- 精简 `orchestrator.py` 中 `run_pipeline()` 的可提取逻辑（如有低风险机会）

**Non-Goals:**
- 不修改 `lib/extraction/infobox.py` 或 `lib/extraction/preprocessor.py`
- 不修改 `chrome-agent-cli.mjs`
- 不新增功能或改变运行时行为
- 不执行 Spec 合并（Change D2）

## Decisions

### D1: 使用 `bash mv` + `sed` 移动文件

**Decision**: 使用 `mv` 移动文件，用 `sed` 批量替换 import 路径。

**Rationale**: 纯文件移动，不需要 `git mv` 的历史保留（文件内容可能有行号变化，且 import 路径需要修改）。`sed` 批量替换更高效且不易遗漏。

### D2: Import 路径更新策略

**Decision**: 对于 4 个 import 方的更新策略：

| Importer | 当前路径 | 新路径 |
|----------|---------|--------|
| `converters/__init__.py` 行 6 | `from .html_to_markdown import HtmlToMarkdownConverter` | `from scripts.lib.extraction.converter import HtmlToMarkdownConverter` |
| `strategies/__init__.py` 行 227 | `from ..converters.html_to_markdown import HtmlToMarkdownConverter` | `from scripts.lib.extraction.converter import HtmlToMarkdownConverter` |
| `standalone.py` 行 13 | `from .converters.html_to_markdown import HtmlToMarkdownConverter` | `from scripts.lib.extraction.converter import HtmlToMarkdownConverter` |
| `sample_converter.py` 行 438 | `importlib.import_module('scripts.mediawiki-api-extract.converters.html_to_markdown')` | `importlib.import_module('scripts.lib.extraction.converter')` |

**Rationale**: 所有 import 统一使用 `scripts.lib.extraction.converter` 绝对路径，避免相对路径跨包引用（如 `from ....lib.extraction.converter import ...` 需要 4-5 级 `..`）。

### D3: `html_to_markdown.py` 中自引用的处理

**Decision**: `html_to_markdown.py` 行 6 有一个自引用（用于 type hints 的 lazy import）：

```python
"""...
Can be imported and used standalone:
    from scripts.mediawiki_api_extract.converters.html_to_markdown import HtmlToMarkdownConverter
"""
```

移动后更新为：
```python
"""...
Can be imported and used standalone:
    from scripts.lib.extraction.converter import HtmlToMarkdownConverter
"""
```

文件内部无 `import` 自身代码（仅 docstring 中的示例），无需额外处理。

### D4: 函数重命名方式

**Decision**: 使用 `edit` 工具或 `sed` 在 6 个文件中执行精确替换：

| 文件 | 替换 |
|------|------|
| `phases/discovery_homepage.py` | `def run_phase_0` → `def run_homepage_discovery` |
| `phases/discovery_allpages.py` | `def run_phase_a` → `def run_allpages_discovery` |
| `phases/fetch.py` | `def run_phase_fetch` → `def run_fetch` |
| `phases/convert.py` | `def run_phase_convert` → `def run_convert` |
| `phases/assemble.py` | `def run_phase_c` → `def run_assemble` |
| `orchestrator.py` | import 行 + 调用行（共 10 处） |

**Rationale**: 精确文本替换，不设向后兼容别名（phase 模块是内部模块，无外部调用方）。

### D5: orchestrator.py 精简

**Decision**: 如果 `run_pipeline()` 中有可提取的独立逻辑块（如状态管理段或链路修复段），提取为独立辅助函数以将文件减至 ≤350 行。但此项为尽最大努力，不为行数目标而做无意义拆分。

当前 `run_pipeline()` 从行 76 到行 456（约 380 行），可以尝试提取：
- 行 130-150: 发现摘要生成（约 20 行，可提取到独立函数）
- 行 270-300: 恢复状态初始化（约 30 行，可提取到独立函数）
- 行 400-460: 后处理（link_fix + L6 validation + final summary）（约 60 行，可提取到独立函数）

## Risks / Migration

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Import 路径更新遗漏 | Low | High | `grep -rn "html_to_markdown" scripts/` 确认无残留旧路径引用 |
| 函数重命名遗漏调用方 | Low | Medium | `grep -rn "run_phase_" scripts/` 确认零匹配 |
| `sample_converter.py` 的 importlib 调用破裂 | Low | High | 运行 explore 流程 + 验证 `convert_html_to_markdown()` 仍可用 |
| 移动后 `converters/__init__.py` 的 re-export 断裂 | Low | Medium | `from scripts.pipeline.converters import HtmlToMarkdownConverter` 测试 |
| orchestrator.py 精简引入逻辑错误 | Low | Low | 纯机械提取，无逻辑变更；跑现有 pipeline 测试验证 |
