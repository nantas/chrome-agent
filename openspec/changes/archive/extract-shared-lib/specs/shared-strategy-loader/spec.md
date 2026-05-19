# shared-strategy-loader Specification

## Scope

提供统一的策略 YAML frontmatter 解析入口，消除跨模块/跨路径的重复 YAML 解析实现。当前阶段仅提取 `parse_strategy()` 函数并作为共享库发布，不强制替换其余 5 处独立实现。

## ADDED Requirements

### Requirement: `parse_strategy()` 共享暴露

The system SHALL provide `parse_strategy(strategy_path: str) -> dict` as a shared function importable from `scripts.lib.strategy_loader`.

The function SHALL:
1. Open the file at `strategy_path` with UTF-8 encoding
2. Split content on `---` markers (first pair only) to extract YAML frontmatter
3. Parse frontmatter with `yaml.safe_load()`
4. Return the full parsed dict

#### Scenario: Standard strategy file
- **WHEN** `parse_strategy()` receives a path to a valid `strategy.md` with YAML frontmatter delimited by `---`
- **THEN** SHALL return the frontmatter as a dict
- **AND** SHALL raise `ValueError` if frontmatter is missing

### Requirement: `parse_frontmatter_from_content()` 预留占位

The system SHALL provide `parse_frontmatter_from_content(content: str) -> Optional[dict]` as a shared utility for parsing YAML frontmatter from raw file content strings using regex.

The function SHALL:
1. Apply regex `^---\n(.*?)\n---` with `re.S | re.M` flags
2. Parse matched group with `yaml.safe_load()`
3. Return `None` if no match found

#### Scenario: Content string with frontmatter
- **WHEN** `parse_frontmatter_from_content()` receives a string starting with `---\nkey: value\n---`
- **THEN** SHALL return `{"key": "value"}`
- **AND** SHALL return `None` for strings without `---` markers

### Requirement: 导入路径一致性

The system SHALL ensure that `scripts.lib` is importable as a Python 3 sub-package under the `scripts` package (which has no `__init__.py` at present — the import path relies on `sys.path` manipulation or `-m` invocation).

Given that pipeline scripts are invoked via `python3 -m scripts.mediawiki-api-extract`, the relative import `from ...lib.strategy_loader import parse_strategy` SHALL work correctly when invoked from `scripts/mediawiki-api-extract/pipeline/orchestrate.py`.

#### Scenario: Pipeline import
- **WHEN** `orchestrate.py` is loaded via `python3 -m scripts.mediawiki-api-extract`
- **AND** it uses `from ...lib.strategy_loader import parse_strategy`
- **THEN** SHALL resolve correctly without `ModuleNotFoundError`
