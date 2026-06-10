# Specification Delta

## Capability 对齐（已确认）

- Capability: `link-resolution-integration`
- 来源: `proposal.md`
- 变更类型: modified
- 用户确认摘要: 单点修复 nintendo site sample 回归失败，集成 markdown_link_resolver

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: Link resolution applied after HTML-to-Markdown conversion
The site sample conversion flow SHALL apply `markdown_link_resolver.fix_all_links()` after `html_to_markdown()` conversion, resolving `../Pages/Page_*.html` patterns to either `.md` filenames (when the target exists in the page mapping) or full external URLs.

#### Scenario: Nintendo page with internal Page links
- **WHEN** a Nintendo HTML page contains `<a href="../Pages/Page_123.html">` links
- **AND** the corresponding `.md` file exists in the output directory with a `> Source:` matching `Pages/Page_123.html`
- **THEN** the converted Markdown SHALL contain `[label](filename.md)` instead of `[label](../Pages/Page_123.html)`

#### Scenario: Nintendo page with unmapped Page links
- **WHEN** a Nintendo HTML page contains `<a href="../Pages/Page_999.html">` links
- **AND** no corresponding `.md` file exists in the output directory
- **THEN** the converted Markdown SHALL contain a full external URL instead of the raw `../Pages/Page_999.html` pattern

### Requirement: Site sample regression tests pass
After link resolution integration, all `developer.nintendo.com` site sample regression tests SHALL pass the `assert_links_resolved` structural assertion.

#### Scenario: Running site sample regression
- **WHEN** `python3 scripts/test_runner.py site-samples --domain developer.nintendo.com` is executed
- **THEN** all 3 samples SHALL pass with zero `links_resolved` failures
