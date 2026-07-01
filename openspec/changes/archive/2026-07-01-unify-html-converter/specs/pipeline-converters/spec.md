# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-converters`
- 来源: `proposal.md` — Modified Capability
- 变更类型: `modified`
- 用户确认摘要: convert change Stage 3 drift 1：删除死代码 fandom_html_to_markdown.py，所有策略变体走配置驱动

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## REMOVED Requirements

### Requirement: fandom-html-to-markdown-module

**Reason**: `scripts/pipeline/converters/fandom_html_to_markdown.py` has zero callers. All fandom-specific HTML cleanup is handled by `converter.py` (selectolax kernel) combined with `preprocessor.py` strategy-driven cleanup ops (e.g., `strip_fandom_infobox_tables`, `convert_ambox_to_text`, `strip_footer`).

**Migration**: No migration needed. Fandom strategy pages already flow through the shared kernel path. The file is unused and can be deleted without affecting any production or test path.

## ADDED Requirements

### Requirement: strategy-variant-config-driven

All site-specific HTML conversion variations SHALL be expressed through `strategy.md` frontmatter configuration fields (`extraction.cleanup`, `extraction.image_filtering`, `extraction.selectors`), NOT through separate converter module files. The system SHALL NOT create new `*_html_to_markdown.py` files for individual wiki domains or platforms.

#### Scenario: fandom-variant-via-config
- **WHEN** a fandom wiki page is converted
- **THEN** the conversion SHALL go through `HtmlToMarkdownConverter` with the shared kernel
- **AND** fandom-specific cleanup SHALL be driven by the strategy's `extraction.cleanup` configuration
- **AND** no fandom-specific converter file SHALL be imported or executed

#### Scenario: new-variant-via-config-only
- **WHEN** a new wiki platform requires HTML conversion
- **THEN** the new platform's behavior SHALL be expressed entirely in `strategy.md` configuration
- **AND** no new `*_html_to_markdown.py` file SHALL be created

## MODIFIED Requirements

_None — existing `table-rendering-refactored`, `block-tags-completeness`, and other requirements unchanged._
