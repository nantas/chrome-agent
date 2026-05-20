# Specification: pipeline-converters

## Capability 对齐

- Capability: `pipeline-converters`
- 来源: `fix-pipeline-quality-gaps` / `fix-complex-table-rendering` changes
- 变更类型: `modified`

## 规范真源声明

- 本文件是该 capability 的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件
- 本文件合并自 `fix-pipeline-quality-gaps` 和 `fix-complex-table-rendering` 的 delta specs

## Requirements

### Requirement: table-rendering-refactored

`HtmlToMarkdownConverter._render_table(node, source_dir)` SHALL be refactored to use the grid-based parsing pipeline:

1. Call `self._build_table_grid(node, source_dir)` to produce a normalized 2D grid — grid builder SHALL only collect direct child `<tr>` elements to avoid mixing rows from nested tables
2. If the grid is empty, return `""`
3. Read `self.config.get("table_options", {}).get("transpose_wider_than")` to determine the transpose threshold
4. If the grid's column count exceeds the threshold, call `self._transpose_grid(grid, header_row_count)` to transpose
5. Call `self._render_grid_as_table(grid, header_row_count)` to produce the Markdown output

The method SHALL NOT contain any fallback logic to flat list rendering.

#### Scenario: complex-character-table-produces-markdown-table

- **WHEN** converting the Characters page table (29 rows, 22 columns, with colspan/rowspan)
- **AND** `transpose_wider_than` is `10`
- **THEN** the output SHALL be a valid Markdown table
- **AND** SHALL NOT contain `- cell | cell | ...` bullet-list fallback output
- **AND** the transposed table SHALL have characters as rows and stats (Health, Damage, ...) as columns

#### Scenario: simple-table-still-works

- **WHEN** converting a simple 3×2 table without colspan/rowspan
- **AND** `transpose_wider_than` is `10` (not triggered for 2 columns)
- **THEN** the output SHALL be a standard Markdown table with header row and separator
- **AND** the output SHALL match pre-refactor behavior

#### Scenario: nav-table-preserved

- **WHEN** converting a `table.navbox` element (already stripped by `clean_html`)
- **THEN** the navbox SHALL NOT appear in the converted output
- **AND** this behavior SHALL be unchanged from pre-refactor (navboxes removed before table rendering)

### Requirement: build-table-grid-integration

`HtmlToMarkdownConverter` SHALL expose `_build_table_grid(node, source_dir)` as specified in `specs/table-grid-parser/spec.md`. The method SHALL be called from `_render_table()` and MAY be called from other methods in the future.

### Requirement: render-grid-as-table-integration

`HtmlToMarkdownConverter` SHALL expose `_render_grid_as_table(grid, header_row_count)` as specified in `specs/table-grid-parser/spec.md`.

### Requirement: transpose-grid-integration

`HtmlToMarkdownConverter` SHALL expose `_transpose_grid(grid, header_row_count)` as a static method, as specified in `specs/table-transpose-config/spec.md`.

### Requirement: strategy-config-integration

`HtmlToMarkdownConverter._render_table()` SHALL read `self.config.table_options.transpose_wider_than` to determine whether to transpose, as specified in `specs/table-transpose-config/spec.md`.

### Requirement: block-tags-completeness

`HtmlToMarkdownConverter._BLOCK_TAGS` SHALL include all HTML5 semantic block-level elements. The set SHALL contain at minimum: `"article"`, `"blockquote"`, `"div"`, `"h1"`–`"h6"`, `"hr"`, `"ol"`, `"p"`, `"pre"`, `"section"`, `"table"`, `"ul"`.

When a block-level container element (e.g., `<section>`, `<article>`) is encountered, `_has_block_children()` SHALL return `True`, causing `_render_block()` to route through `_render_blocks()` which separates child blocks with `\n\n`.

#### Scenario: section-rendered-as-block-container

- **WHEN** a `<section>` contains two `<article>` elements, each wrapping a `<table>`
- **AND** `"article"` and `"section"` are in `_BLOCK_TAGS`
- **THEN** the two tables' Markdown output SHALL be separated by `\n\n`
- **AND** SHALL NOT be concatenated as inline content

### Requirement: nested-table-cell-handling

When `_build_table_grid()` encounters a nested `<table>` inside a `<th>` or `<td>` cell, the nested table SHALL NOT be recursively rendered. Cell content SHALL be extracted from non-table inline children only.

Additionally, `_build_table_grid()` SHALL only collect direct child `<tr>` elements (via `<tbody>` if present) using `_child_nodes()` traversal, preventing nested table rows from contaminating the parent grid.

#### Scenario: nested-table-in-cell-content-skipped

- **WHEN** a `<td>` contains a nested `<table>` element
- **THEN** `_render_cell_content()` SHALL detect the nested table and skip its recursive rendering
- **AND** the cell SHALL contain only non-table inline text content
- **AND** the outer table's grid SHALL remain correctly column-aligned

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

### Requirement: redirect-detection-and-skip

Convert phase SHALL detect wiki redirect pages via `redirectMsg` HTML marker in the page's rendered HTML. When detected, the page SHALL be skipped (no .md output), marked `status: "redirect"` in pipeline state, and a redirect map (source_title → target_title) SHALL be built. The redirect map SHALL be injected into link resolution so that links pointing to redirect sources are resolved to redirect targets.

Added by the `link-fallback-redirect-skip` change; authoritative spec delta resides in the change directory.

## REMOVED Requirements

### Requirement: is-simple-markdown-table-check

**Reason**: `_is_simple_markdown_table()` is replaced by `_build_table_grid()` which handles both simple and complex tables uniformly. The grid-based approach eliminates the need for a separate simplicity heuristic.

**Migration**: All callers of `_render_table()` (only `_render_block()`) are automatically migrated by the refactored `_render_table()` method. No external callers exist.

### Requirement: fallback-to-flat-list-rendering

**Reason**: The fallback branch in `_render_table()` that produces `- cell | cell | ...` output is replaced by grid-based rendering which always produces valid Markdown tables.

**Migration**: No migration needed. All tables now render as Markdown tables. The change is a quality improvement with no loss of functionality.
