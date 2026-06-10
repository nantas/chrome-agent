# Specification Delta

## Capability 对齐（已确认）

- Capability: `golden-diff`
- 来源: `proposal.md`
- 变更类型: new
- 用户确认摘要: grill session 确认——E3 分层（结构断言守底线，`--update-golden` 刷新）

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Golden file storage
Golden files SHALL be stored at `sites/strategies/<domain>/samples/<page>.md`, co-located with the site strategy.

#### Scenario: Golden file path convention
- **WHEN** a sample page has the safe path `Page_123`
- **THEN** the golden file SHALL be at `sites/strategies/<domain>/samples/Page_123.md`

### Requirement: Golden diff comparison
The test runner SHALL compare the converted Markdown output against the golden file using exact text diff.

#### Scenario: Output matches golden
- **WHEN** the converted MD for a sample page is identical to its golden file
- **THEN** the test SHALL pass

#### Scenario: Output differs from golden
- **WHEN** the converted MD differs from the golden file
- **THEN** the test SHALL fail with a unified diff showing the differences

### Requirement: Golden file update mode
The test runner SHALL support `--update-golden` flag to refresh golden files when intentional output changes are made.

#### Scenario: Update golden files
- **WHEN** `python3 scripts/test_runner.py site-samples --domain <domain> --update-golden` is executed
- **THEN** all sample golden files for that domain SHALL be overwritten with the current conversion output
- **THEN** the test SHALL report which files were updated

### Requirement: Structural assertion baseline
The test runner SHALL apply a set of built-in structural assertions to all sample outputs, regardless of golden diff result.

Built-in assertions:
- `no_raw_html_tags`: Output SHALL NOT contain unmatched HTML tags (`<div>`, `<span>`, etc.)
- `links_resolved`: Output SHALL NOT contain raw relative links matching `../Pages/Page_*.html`
- `valid_md_tables`: If output contains `|` table delimiters, the table structure SHALL be well-formed (consistent column count per row)

#### Scenario: Structural assertion failure
- **WHEN** the converted MD contains `../Pages/Page_123.html` links
- **THEN** the `links_resolved` assertion SHALL fail with a descriptive message listing unresolved links

#### Scenario: Structural assertion passes with golden diff failure
- **WHEN** the output passes all structural assertions but differs from golden
- **THEN** the test SHALL still fail (golden diff takes precedence for regression detection)
