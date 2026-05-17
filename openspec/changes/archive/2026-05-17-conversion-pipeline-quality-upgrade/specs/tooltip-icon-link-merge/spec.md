# Specification Delta

## Capability 对齐（已确认）

- Capability: `tooltip-icon-link-merge`
- 来源: `proposal.md` — New Capabilities
- 变更类型: `new`
- 用户确认摘要: 用户确认新增 MediaWiki tooltip 模式的内联图片+文字链接合并预处理

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: merge-tooltip-icon-text-links

The system SHALL provide `merge_tooltip_links(html: str) -> str` that identifies MediaWiki tooltip patterns and merges icon links with their adjacent text links into a single combined link element.

The method SHALL process HTML in this order:
1. Remove opening `<span class="tooltip" ...>` tags (keep inner content)
2. Remove opening `<span style="--tb-icon-size: ...">` tags (keep inner content)
3. Remove ALL closing `</span>` tags
4. Identify consecutive `<a href="SAME_URL">` pairs where the first contains only an `<img>` and the second contains plain text
5. Merge each pair into a single `<a href="URL"><img.../> Text</a>` element

#### Scenario: merge-standard-tooltip-item-link
- **WHEN** `merge_tooltip_links()` processes HTML containing:
  `<span class="tooltip"><span style="--tb-icon-size: 1.4em"><a href="/wiki/Wire_Coat_Hanger"><img src="/images/icon.png"/></a></span><a href="/wiki/Wire_Coat_Hanger">Wire Coat Hanger</a></span>`
- **THEN** the output SHALL be:
  `<a href="/wiki/Wire_Coat_Hanger"><img src="/images/icon.png"/> Wire Coat Hanger</a>`

#### Scenario: no-merge-different-href
- **WHEN** two consecutive `<a>` tags have **different** href values
- **THEN** they SHALL NOT be merged
- **AND** both SHALL remain as separate link elements

#### Scenario: no-merge-non-img-first-link
- **WHEN** the first `<a>` in a pair does NOT contain an `<img>` tag
- **THEN** the pair SHALL NOT be merged

#### Scenario: merge-with-tooltip-data-attributes
- **WHEN** a tooltip span contains `data-tooltip` and `data-tooltip-dlc` attributes
- **THEN** the opening tooltip span SHALL be removed regardless of these attributes
- **AND** the data attributes SHALL NOT affect the merge behavior

#### Scenario: multiple-tooltips-in-content
- **WHEN** `merge_tooltip_links()` processes HTML containing 5 distinct tooltip patterns
- **THEN** all 5 tooltip patterns SHALL be merged into combined image+text links
- **AND** non-tooltip content SHALL remain unchanged

### Requirement: merge-before-image-conversion

The tooltip merge SHALL execute BEFORE `convert_images_to_md()` in the conversion pipeline.

#### Scenario: merge-precedes-conversion
- **WHEN** the conversion pipeline processes a page body
- **THEN** `merge_tooltip_links()` SHALL be called before `convert_images_to_md()`
- **AND** the merged `<a href="URL"><img/> Text</a>` elements SHALL be present when image conversion runs
