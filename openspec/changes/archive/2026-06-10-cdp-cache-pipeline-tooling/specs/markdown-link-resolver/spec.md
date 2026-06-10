# Specification Delta

## Capability 对齐（已确认）

- Capability: `markdown-link-resolver`
- 来源: `proposal.md`
- 变更类型: new
- 用户确认摘要: 确认 — Markdown 链接批量修复工具

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Internal link resolution
The resolver SHALL convert internal page links (`../Pages/Page_xxx.html`) to relative `.md` file references when the target page exists in the crawl output mapping.

- The mapping SHALL be built by scanning all `.md` files in the output directory and extracting `> Source:` URLs.
- A page SHALL be considered "in scope" if its Source URL contains the target Page ID.
- Resolved links SHALL use the target `.md` filename, maintaining the same directory context.

#### Scenario: Internal link to crawled page
- **WHEN** a Markdown file contains `[1 Introduction](../Pages/Page_239857945.html)` and `1_Introduction.md` exists in the same directory
- **THEN** the link SHALL be replaced with `[1 Introduction](1_Introduction.md)`

#### Scenario: Internal link to uncrawled page
- **WHEN** a Markdown file contains `[<< Title Sheet](../title.html)` and no `.md` mapping exists for `title.html`
- **THEN** the link SHALL be replaced with the full URL `https://developer.nintendo.com/.../contents/title.html`

### Requirement: Image link resolution
The resolver SHALL convert internal image links (`../Attachments/...`, `../template/...`) to full URLs when no local image mapping exists, and to relative `../images/` paths when images have been downloaded locally.

#### Scenario: Downloaded image
- **WHEN** an image URL `https://...Attachments/Attach_xxx/yyy.png` has been downloaded to `images/Attachments/Attach_xxx/yyy.png`
- **THEN** the Markdown image reference SHALL be updated to `../images/Attachments/Attach_xxx/yyy.png`

#### Scenario: Undownloaded external image
- **WHEN** an image URL has no local copy
- **THEN** the reference SHALL remain as the full external URL

### Requirement: Absolute URL passthrough
The resolver SHALL NOT modify links that already point to absolute URLs (`http://`, `https://`, `//`), anchor-only references (`#section`), or JavaScript pseudo-URLs (`javascript:void(0)`).

#### Scenario: External URL unchanged
- **WHEN** a Markdown file contains `[External Docs](https://example.com/page)`
- **THEN** the link SHALL remain unchanged

#### Scenario: Anchor unchanged
- **WHEN** a Markdown file contains `[Jump](#section-name)`
- **THEN** the link SHALL remain unchanged

### Requirement: Directory-scoped mapping
The resolver SHALL build independent page mappings per document directory, so links within `Online_Play_Guide/` resolve only against other files in `Online_Play_Guide/`.

#### Scenario: Cross-doc link treated as external
- **WHEN** a page in `Account_Guide/` references `../Pages/Page_241536127.html` which belongs to `Online_Play_Guide/`
- **THEN** the link SHALL be resolved to the full external URL, since the mapping is directory-scoped
