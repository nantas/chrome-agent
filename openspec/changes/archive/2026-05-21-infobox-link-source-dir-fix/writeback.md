# Writeback

## Change: infobox-link-source-dir-fix

## Writeback Targets

### Target: `openspec/specs/pipeline-converters/spec.md`

**Action:** Add new requirement

**Content to append:**

```markdown
### Requirement: infobox-link-source-dir-passthrough

`_extract_selectolax()` SHALL accept `source_dir: str = ""` parameter and pass it as `source_dir` keyword argument when calling `render_inline_children_fn`.

`extract_infobox()` SHALL accept `source_dir: str = ""` parameter and pass it through to `_extract_selectolax()` in the selectolax branch.

`HtmlToMarkdownConverter._render_infobox_table()` SHALL pass its current `source_dir` parameter value when calling `extract_infobox()`.

#### Scenario: infobox-link-uses-correct-relative-path

- **WHEN** converting `bosses/Ultra_Greed.md` infobox
- **AND** infobox contains a link to `endings/index.md`
- **THEN** the infobox link SHALL be `[Ending 18](../endings/index.md)`
- **AND** SHALL NOT be `[Ending 18](endings/index.md)`

#### Scenario: infobox-link-same-directory

- **WHEN** converting `items/Item_Pool.md` infobox
- **AND** infobox contains a link to `items/Item_Pool.md`
- **THEN** the infobox link SHALL be `[Item Pool](Item_Pool.md)` (no prefix)

#### Scenario: bs4-path-unaffected

- **WHEN** `extract_infobox()` uses BS4 mode (explore path)
- **THEN** behavior SHALL be identical to before this change (BS4 path does not use `source_dir`)
```

## Verification Reference

- `verification.md` — all scenarios PASS
- Baseline test: broken links 7→0, no regressions
