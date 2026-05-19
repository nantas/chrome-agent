# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-package-identity`
- 来源: `proposal.md` Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 基于 `docs/plans/2026-05-19-structure-refactor-and-docs.md` § Change 3 设计确认

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: package-rename
系统 SHALL 将 `scripts/mediawiki-api-extract/` 目录重命名为 `scripts/pipeline/`，所有内部相对 import 保持不变，所有绝对 import 路径从 `scripts.mediawiki_api_extract` 更新为 `scripts.pipeline`。

#### Scenario: directory-rename
- **WHEN** `mv scripts/mediawiki-api-extract scripts/pipeline` 执行完成
- **THEN** `scripts/pipeline/` 目录存在，所有文件内容保留

#### Scenario: absolute-imports-updated
- **WHEN** 在 `scripts/pipeline/` 中搜索 `mediawiki_api_extract`
- **THEN** 所有 Python 绝对 import 路径已更新为 `scripts.pipeline`
- **AND** docstring 和注释中的旧路径引用也已更新

### Requirement: main-simplification
`__main__.py` SHALL 删除 re-invoke workaround（因 `pipeline` 无连字符），直接执行 `from .cli import main`。

#### Scenario: no-reinvoke
- **WHEN** `python3 -m scripts.pipeline` 被执行
- **THEN** 直接进入 `cli.main()`，无需 subprocess re-invoke
- **AND** `__main__.py` 不包含 `subprocess.call` 调用

### Requirement: cli-spawn-path-update
`chrome-agent-cli.mjs` SHALL 将所有硬编码的 `mediawiki-api-extract` 路径替换为 `pipeline`。

#### Scenario: mjs-path-update
- **WHEN** `chrome-agent-cli.mjs` 中搜索 `mediawiki-api-extract`
- **THEN** 返回 0 匹配（路径检查、spawn 参数、fallback 消息全部更新为 `pipeline`）

### Requirement: logger-name-update
所有 Python 模块中的 `getLogger("mediawiki-api-extract")` SHALL 更新为 `getLogger("pipeline")`。

#### Scenario: logger-consistency
- **WHEN** 在 `scripts/pipeline/` 中搜索 `getLogger("mediawiki-api-extract")`
- **THEN** 返回 0 匹配
- **AND** 所有 logger 统一使用 `getLogger("pipeline")`（子模块可用 `pipeline.converters` 等点分格式）

### Requirement: external-reference-update
`scripts/explore/` 中引用 `mediawiki-api-extract` 路径的文件（`architecture_gate.py`、`sample_converter.py`、`strategy_scaffold_generator.py`）SHALL 更新路径引用。

#### Scenario: explore-references
- **WHEN** 在 `scripts/explore/` 中搜索 `mediawiki-api-extract`
- **THEN** 返回 0 匹配

### Requirement: test-reference-update
测试文件中引用旧包路径的 SHALL 更新。

#### Scenario: test-path-update
- **WHEN** 在 `scripts/pipeline/tests/` 中搜索 `mediawiki-api-extract`
- **THEN** 返回 0 匹配
