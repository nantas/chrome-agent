# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-converters`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户选择三层方案，需修复 converter 的 URL 编码解码问题

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: url-encoded-title-resolution

`HtmlToMarkdownConverter._to_markdown_link()` SHALL decode percent-encoded characters in wiki page titles before performing manifest lookup.

The resolution logic SHALL:
1. Extract the title slug from the href (path segment after `/wiki/`)
2. Strip query parameters and fragments
3. Apply `urllib.parse.unquote()` to decode percent-encoding (`%27` → `'`, `%26` → `&`, etc.)
4. Replace underscores with spaces
5. Look up in `title_to_path` with the decoded title
6. Fall back to underscore-form title if decoded title not found

#### Scenario: percent-encoded-apostrophe

- **WHEN** `_to_markdown_link()` processes href `https://bindingofisaacrebirth.wiki.gg/wiki/Mom%27s_Knife`
- **THEN** the title slug SHALL be decoded from `Mom%27s_Knife` to `Mom's Knife`
- **THEN** `title_to_path.get("Mom's Knife")` SHALL be attempted
- **THEN** if found, the link SHALL be converted to a relative Markdown link

#### Scenario: percent-encoded-ampersand

- **WHEN** `_to_markdown_link()` processes href containing `Jacob_%26_Esau`
- **THEN** the title slug SHALL be decoded to `Jacob & Esau`
- **THEN** manifest lookup SHALL use the decoded title

#### Scenario: no-encoding-present

- **WHEN** `_to_markdown_link()` processes href `https://example.wiki.gg/wiki/Simple_Title`
- **THEN** `unquote()` SHALL be a no-op (no percent-encoding in title)
- **THEN** behavior SHALL be identical to pre-fix behavior
- **THEN** existing tests SHALL pass without modification

#### Scenario: fallback-to-underscore

- **WHEN** decoded title `"Mom's Knife"` is not found in `title_to_path`
- **THEN** the system SHALL attempt `title_to_path.get("Mom's_Knife")` as fallback
- **THEN** if still not found, SHALL return None (preserving absolute URL)

### Requirement: converter-link-fixer-alignment

The URL decoding behavior in `HtmlToMarkdownConverter._to_markdown_link()` SHALL be consistent with the decoding behavior already implemented in `converters/link_fixer.py`'s `fix_links_in_dir()`.

#### Scenario: converter-and-fixer-consistent

- **WHEN** the same page with percent-encoded links is processed through both the converter and the link fixer
- **THEN** both SHALL resolve the same set of internal links
- **THEN** the converter SHALL NOT leave links unresolved that the link fixer can resolve

### Requirement: standalone-title-url-decoding

`standalone.py`'s `fetch_and_convert()` SHALL decode URL-encoded characters in the page title extracted from the URL before passing to the MediaWiki API.

The title extraction logic SHALL:
1. Extract the title slug from the URL path (after `/wiki/`)
2. Apply `urllib.parse.unquote()` to decode percent-encoding
3. Replace underscores with spaces

#### Scenario: url-encoded-title-in-standalone

- **WHEN** `fetch_and_convert()` is called with URL `https://domain/wiki/Mom%27s_Knife`
- **THEN** the extracted title SHALL be `"Mom's Knife"` (not `"Mom%27s Knife"`)
- **THEN** the API call SHALL use the decoded title
- **THEN** the API SHALL NOT return a "Bad title" error

#### Scenario: already-decoded-title

- **WHEN** `fetch_and_convert()` is called with URL `https://domain/wiki/Simple_Title`
- **THEN** `unquote()` SHALL be a no-op
- **THEN** behavior SHALL be identical to pre-fix

