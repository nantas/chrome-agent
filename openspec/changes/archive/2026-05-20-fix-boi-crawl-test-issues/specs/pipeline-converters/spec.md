# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-converters`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 修复括号文件名链接 URL-encode、YouTube 残留清理、frontmatter image 过滤

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件
- 本文件是 `fix-pipeline-quality-gaps` 中同名 spec 的增量补充

## MODIFIED Requirements

### Requirement: parenthesis-filename-url-encoding

`HtmlToMarkdownConverter._to_markdown_link()` and `fix_links_in_dir()` SHALL encode parentheses `(` → `%28` and `)` → `%29` in the filename portion of internal wiki links when the filename contains parentheses, preventing Markdown link syntax from parsing `)` as the link terminator.

#### Scenario: parenthesis-in-filename

- **WHEN** converting a link to a page titled `V1.06.0192 (Re-release)`
- **THEN** the generated Markdown link SHALL be `[text](V1.06.0192_%28Re-release%29.md)`
- **AND** SHALL NOT be `[text](V1.06.0192_(Re-release).md)` (where `)` breaks parsing)

#### Scenario: link-fixer-applies-encoding

- **WHEN** `fix_links_in_dir()` encounters a markdown link with an unencoded parenthesis in the URL portion
- **THEN** it SHALL URL-encode the parentheses
- **AND** SHALL count the fix in its `fixed` counter

### Requirement: youtube-load-video-residue-cleanup

`HtmlToMarkdownConverter.clean_html()` SHALL remove the YouTube fallback text elements that contain "Load video" / "YouTube" / "Privacy Policy" / "Continue Dismiss" strings after the `extract_video_links()` step.

#### Scenario: no-load-video-text-in-output

- **WHEN** the raw HTML contains YouTube oEmbed fallback elements (e.g., `<div>Load video</div><div>YouTube...</div><div>Privacy Policy...</div><div>Continue Dismiss</div>`)
- **THEN** the converted Markdown SHALL NOT contain the text "Load video", "YouTube might collect personal data", "Privacy Policy", or "Continue Dismiss"
- **AND** the video link SHALL still be present in the `## In-game Footage` section

### Requirement: frontmatter-image-skip-patterns

`_process_html_page()` and `convert_single_page()` SHALL apply the strategy's `image_filtering.skip_patterns` to the `images` list before selecting the first image for the frontmatter `image` field. If the first image matches a skip pattern, the converter SHALL try subsequent images until it finds one that does not match, or omit the `image` field entirely if all images are skipped.

#### Scenario: decorative-image-skipped-for-frontmatter

- **WHEN** the page's `images` list is `["Font_TeamMeat_T.png", "Collectible_The_Sad_Onion_icon.png"]`
- **AND** `image_filtering.skip_patterns` includes `"Font_TeamMeat"`
- **THEN** the frontmatter `image` field SHALL be `"Collectible_The_Sad_Onion_icon.png"`
- **AND** SHALL NOT be `"Font_TeamMeat_T.png"`

#### Scenario: all-images-skipped

- **WHEN** all images in the `images` list match a skip pattern
- **THEN** the frontmatter SHALL omit the `image` field entirely
