# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-converters`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: converters-as-independent-package
`HtmlToMarkdownConverter`、`convert_wikitext_to_markdown`、`extract_card_stats`、`split_card_list_pages` SHALL 位于 `scripts/mediawiki_api_extract/converters/` 子包中，可被外部代码直接导入，无需启动管线或导入 `ApiClient`。

#### Scenario: import-html-converter-standalone
- **WHEN** 外部脚本执行 `from scripts.mediawiki_api_extract.converters import HtmlToMarkdownConverter`
- **THEN** 导入 SHALL 成功，无需安装或配置 `ApiClient`

#### Scenario: import-wikitext-converter-standalone
- **WHEN** 外部脚本执行 `from scripts.mediawiki_api_extract.converters import convert_wikitext_to_markdown`
- **THEN** 导入 SHALL 成功

### Requirement: strategies-split-by-role
策略类 SHALL 按 Discovery、Acquisition、LinkResolver、TemplateProcessor、ListPageAssembler 五种角色分别位于 `scripts/mediawiki_api_extract/strategies/` 子包的独立模块中。

#### Scenario: import-strategy-from-submodule
- **WHEN** 外部代码执行 `from scripts.mediawiki_api_extract.strategies.discovery import AllPagesDiscoveryStrategy`
- **THEN** 导入 SHALL 成功，行为与原 `strategies.py` 中的实现一致

### Requirement: backward-compatible-reexports
`strategies/__init__.py` SHALL 重新导出所有策略类和转换器，使 `from scripts.mediawiki_api_extract.strategies import HtmlToMarkdownConverter` 等原有导入路径继续可用。

#### Scenario: legacy-import-path
- **WHEN** 既有代码执行 `from scripts.mediawiki_api_extract.strategies import HtmlToMarkdownConverter`
- **THEN** 导入 SHALL 成功，返回与 converters 子包中相同的类

#### Scenario: phase-b-import-path
- **WHEN** `phase_b.py` 执行 `from .strategies import HtmlToMarkdownConverter, convert_wikitext_to_markdown`
- **THEN** 导入 SHALL 成功，功能不变

### Requirement: pipeline-orchestration-extracted
`run_pipeline`、`build_pipeline`、`parse_strategy`、`resolve_rate_limit_config` SHALL 位于 `scripts/mediawiki_api_extract/pipeline/` 子包中，`pipeline.py` 重命名为 `pipeline/orchestrate.py`。

#### Scenario: main-imports-pipeline
- **WHEN** `__main__.py` 执行 `from .pipeline import run_pipeline`（通过 `pipeline/__init__.py` re-export）
- **THEN** 导入 SHALL 成功，管线行为不变

### Requirement: no-behavior-change
拆分后所有既有管线的输出 SHALL 与拆分前完全一致（相同输入产生相同 .md 文件）。

#### Scenario: full-pipeline-output-unchanged
- **WHEN** 对相同站点策略运行全量管线（Phase A→B→C）
- **THEN** 输出 .md 文件内容 SHALL 与拆分前逐字节一致
