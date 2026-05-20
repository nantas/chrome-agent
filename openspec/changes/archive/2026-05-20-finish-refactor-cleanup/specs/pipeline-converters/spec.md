# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-converters`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 将 HtmlToMarkdownConverter 从 `pipeline/converters/html_to_markdown.py` 移动到 `lib/extraction/converter.py`，更新所有 import 路径

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: converter-location-in-lib

The `HtmlToMarkdownConverter` class SHALL reside in `scripts/lib/extraction/converter.py` and SHALL be importable via `from scripts.lib.extraction.converter import HtmlToMarkdownConverter`.

The `convert_html_to_markdown()` convenience function SHALL co-locate with `HtmlToMarkdownConverter` in `converter.py`.

The original `scripts/pipeline/converters/html_to_markdown.py` SHALL be removed after the move.

#### Scenario: import-after-move

- **WHEN** any module imports `HtmlToMarkdownConverter`
- **THEN** the import path SHALL resolve to `scripts/lib/extraction/converter.py`

#### Scenario: original-file-removed

- **WHEN** the move is complete
- **THEN** `scripts/pipeline/converters/html_to_markdown.py` SHALL NOT exist
- **AND** `grep -r "from.*pipeline.*converters.*html_to_markdown" scripts/` SHALL return zero matches for the old path

### Requirement: converter-importers-updated

All modules that previously imported from `pipeline/converters/html_to_markdown.py` SHALL be updated to import from `lib/extraction/converter.py`.

The following 4 importers SHALL be updated:

1. `pipeline/converters/__init__.py` — the public re-export of `HtmlToMarkdownConverter`
2. `pipeline/strategies/__init__.py` — the backward-compatible re-export of `HtmlToMarkdownConverter`
3. `pipeline/standalone.py` — direct import of `HtmlToMarkdownConverter`
4. `scripts/explore/sample_converter.py` — `importlib.import_module()` call for `convert_html_to_markdown()`

#### Scenario: converters-init-re-export

- **WHEN** `from scripts.pipeline.converters import HtmlToMarkdownConverter` is used
- **THEN** the import SHALL succeed
- **AND** the class SHALL be the same as imported from `scripts.lib.extraction.converter`

#### Scenario: strategies-init-re-export

- **WHEN** `from scripts.pipeline.strategies import HtmlToMarkdownConverter` is used
- **THEN** the import SHALL succeed
- **AND** the class SHALL be the same as imported from `scripts.lib.extraction.converter`

#### Scenario: standalone-import

- **WHEN** `pipeline/standalone.py` runs `from .converters.html_to_markdown import HtmlToMarkdownConverter`
- **THEN** the import SHALL resolve to `lib/extraction/converter.py`

#### Scenario: sample-converter-importlib

- **WHEN** `scripts/explore/sample_converter.py` calls `importlib.import_module()`
- **THEN** the module string SHALL be `'scripts.lib.extraction.converter'` (NOT `'scripts.mediawiki-api-extract.converters.html_to_markdown'` or `'scripts.pipeline.converters.html_to_markdown'`)
- **AND** `convert_html_to_markdown()` SHALL remain callable with the same signature

### Requirement: converter-internal-imports

`HtmlToMarkdownConverter` SHALL import its dependencies from the correct relative paths after the move:

- `self._render_infobox_table()` SHALL import from `scripts.lib.extraction.infobox` (replacing the deleted `infox_renderer.py`)
- `clean_html()` MAY optionally use `scripts.lib.extraction.preprocessor`

#### Scenario: infobox-import-in-converter

- **WHEN** `_render_infobox_table()` is called
- **THEN** it SHALL import `extract_infobox` from `scripts.lib.extraction.infobox`
- **AND** it SHALL NOT import from `scripts.pipeline.converters.infox_renderer` (file deleted in Change 2)
