# Proposal

## 问题定义

`docs/plans/2026-05-19-structure-refactor-and-docs.md` 规划的 5 个实现 change 已完成主要工作，但留有 3 项未闭合的清理任务：

1. **`html_to_markdown.py` 未移动到 `lib/extraction/converter.py`**：Change 2 统一了 `lib/extraction/infobox.py` 和 `lib/extraction/preprocessor.py`，但将 `html_to_markdown.py`（813 行）的整体移动推迟到了 Change 3。Change 3 执行了包重命名和 orchestrator 拆分，但遗漏了此项移动。当前 `html_to_markdown.py` 仍在 `pipeline/converters/` 中，且有 4 个外部 import 方。

2. **Phase 函数名未更新**：Change 4 将文件名从 `phase_0.py` / `phase_a.py` / `phase_c.py` 重命名为 `discovery_homepage.py` / `discovery_allpages.py` / `assemble.py`，但内部的函数名仍为 `run_phase_0()` / `run_phase_a()` / `run_phase_c()` / `run_phase_fetch()` / `run_phase_convert()`。文件重命名只完成了一半。

3. **`orchestrator.py` 超过目标行数**：当前 456 行，规划目标 ≤350 行。`run_pipeline()` 函数从 line 76 延伸至 line 456（约 380 行）。虽然结构已清晰，但未达标。

## 范围边界

**范围内：**
- 将 `html_to_markdown.py` 从 `pipeline/converters/` 移动到 `lib/extraction/converter.py`，更新所有 import 引用
- 重命名 5 个 phase 函数：`run_phase_0` → `run_homepage_discovery`，`run_phase_a` → `run_allpages_discovery`，`run_phase_c` → `run_assemble`，`run_phase_fetch` → `run_fetch`，`run_phase_convert` → `run_convert`
- 尝试精简 `orchestrator.py` 中的 `run_pipeline()` 函数（提取重复的错误处理和状态管理逻辑）

**范围外：**
- 不新增功能
- 不修改 `lib/extraction/infobox.py` 或 `lib/extraction/preprocessor.py` 的逻辑
- 不执行 Spec 合并（Change D2，86→20 specs）
- 不修改 `chrome-agent-cli.mjs`

## Capabilities

### Modified Capabilities

- `pipeline-converters`: 将 HtmlToMarkdownConverter 类从 `pipeline/converters/html_to_markdown.py` 移动到 `lib/extraction/converter.py`，更新 `converters/__init__.py`、`strategies/__init__.py`、`standalone.py`、`sample_converter.py` 中的导入路径；移动后 `pipeline/converters/` 中不再包含核心转换器实现
- `mediawiki-api-extraction-pipeline`: 将 phase 函数名从 `run_phase_0`/`run_phase_a`/`run_phase_c`/`run_phase_fetch`/`run_phase_convert` 重命名为 `run_homepage_discovery`/`run_allpages_discovery`/`run_assemble`/`run_fetch`/`run_convert`，与文件名对齐；更新 `orchestrator.py` 中的 import 和调用

## Capabilities 待确认项

- [x] 能力清单已与用户确认（基于 `docs/plans/2026-05-19-structure-refactor-and-docs.md` 的 Change 3/4 设计，与之前 session 的讨论一致）

## Impact

| 影响维度 | 详情 |
|---------|------|
| 文件移动 | `pipeline/converters/html_to_markdown.py` → `lib/extraction/converter.py` |
| Import 更新 | 4 个文件需要更新路径：`converters/__init__.py`、`strategies/__init__.py`、`standalone.py`、`sample_converter.py` |
| 函数重命名 | 6 个文件：`orchestrator.py` + 5 个 phase 文件（`discovery_homepage.py`、`discovery_allpages.py`、`fetch.py`、`convert.py`、`assemble.py`） |
| 行为变更 | 无 — 纯代码移动和重命名，运行时行为完全不变 |
| 向后兼容 | `strategies/__init__.py` 保持 `HtmlToMarkdownConverter` 的 re-export；`convert_html_to_markdown()` 便捷函数保留 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页：
  - `pipeline-converters`
  - `mediawiki-api-extraction-pipeline`
  - `homepage-driven-discovery`
- 已确认项目页：
  - `docs/plans/2026-05-19-structure-refactor-and-docs.md`（Change 3/4 章节）
  - `openspec/changes/fix-pipeline-quality-gaps/specs/pipeline-converters/`
  - `openspec/changes/fix-pipeline-quality-gaps/specs/mediawiki-api-extraction-pipeline/`
