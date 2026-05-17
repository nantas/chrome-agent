# Specification Delta

## Capability 对齐（已确认）

- Capability: `balanced-element-removal`
- 来源: `proposal.md` — New Capabilities
- 变更类型: `new`
- 用户确认摘要: 用户确认新增通用的 HTML 平衡元素移除方法，替代非贪婪 regex `.*?` 处理嵌套元素的精确删除

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: remove-balanced-element

The system SHALL provide `remove_balanced_element(html: str, tag: str, attr_pattern: str) -> str` that removes an HTML element by opening tag match followed by balanced closing tag detection, using depth counting rather than non-greedy regex `.*?`.

The method SHALL:
1. Find the first `<tag ...attr_pattern...>` opening tag
2. Track nesting depth starting at 1
3. For each subsequent `<tag>` opening tag, increment depth by 1
4. For each subsequent `</tag>` closing tag, decrement depth by 1
5. When depth reaches 0, remove the entire span from the opening tag to this closing tag
6. Return the result with the matched element excised

#### Scenario: remove-nested-toc-div
- **WHEN** `remove_balanced_element(html, "div", r'id="toc"')` is called on HTML containing `<div id="toc"><div class="inner"><h2>Contents</h2></div></div><h2>Effects</h2>`
- **THEN** the TOC div (including its nested inner div and heading) SHALL be removed
- **AND** `<h2>Effects</h2>` and all subsequent content SHALL remain intact
- **AND** the non-greedy regex `.*?</div>\s*</div>\s*</div>` pattern SHALL NOT be used

#### Scenario: remove-nested-edit-section-span
- **WHEN** `remove_balanced_element(html, "span", r'class="[^"]*mw-editsection"')` is called on HTML containing `<h2><span class="mw-headline">Trivia</span><span class="mw-editsection"><span class="mw-editsection-bracket">[</span><a href="..."><span>edit</span></a><span class="mw-editsection-bracket">]</span></span></h2>`
- **THEN** the entire `mw-editsection` span (including all nested bracket and edit spans) SHALL be removed
- **AND** the `mw-headline` span SHALL remain inside the `h2`

#### Scenario: no-match-returns-unchanged
- **WHEN** `remove_balanced_element(html, tag, attr_pattern)` is called and no matching opening tag is found
- **THEN** the original `html` SHALL be returned unchanged

#### Scenario: deeply-nested-content-table
- **WHEN** `remove_balanced_element(html, "table", r'class="[^"]*nav-box"')` is called on HTML containing `<table class="nav-box"><tr><td><table class="inner"><tr><td>content</td></tr></table></td></tr></table>`
- **THEN** the outer nav-box table (including its nested inner table) SHALL be removed
- **AND** content outside the nav-box SHALL remain intact

### Requirement: remove-all-matching-elements

The system SHALL provide `remove_all_matching(html: str, tag: str, attr_pattern: str) -> str` that repeatedly calls `remove_balanced_element` until no matching opening tags remain.

#### Scenario: remove-multiple-navbox-tables
- **WHEN** `remove_all_matching(html, "table", r'class="[^"]*nav-box"')` is called on HTML containing 3 nav-box tables
- **THEN** all 3 nav-box tables (including their balanced closing tags) SHALL be removed
- **AND** content between and after the tables SHALL remain intact

#### Scenario: remove-all-sidebar-dl
- **WHEN** `remove_all_matching(html, "dl", r'')` is called with a wrapper that checks content keywords
- **THEN** each matched `<dl>...</dl>` element SHALL be removed individually using balanced matching
- **AND** the iteration SHALL terminate when no more matching `<dl>` elements exist
