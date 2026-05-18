# Writeback

## Change: converter-unification
## Status: PASS (verification complete)

## Summary

Unified the two HTML→Markdown conversion paths into one. The explore path's `sample_converter.py` now delegates to `HtmlToMarkdownConverter` via the new public API. Infobox rendering is extracted into a shared module. Architecture Gate simplified to single-file validation.

## Writeback Targets

### 1. `scripts/mediawiki-api-extract/converters/html_to_markdown.py`

**Status**: Modified
**Changes**:
- Added `convert_html_to_markdown()` public API function for external callers
- `_render_infobox_table()` now delegates to shared `infox_renderer.py` module
- Empty label bug fixed (labels with no text content are skipped)

### 2. `scripts/explore/sample_converter.py`

**Status**: Modified
**Changes**:
- `_apply_extraction()` Phase 5 now uses `HtmlToMarkdownConverter.convert_html_to_markdown()` instead of `markdownify.markdownify()`
- `markdownify` import removed
- All CLI subcommands (`apply`, `fetch-and-apply`) remain backward-compatible

### 3. `scripts/explore/architecture_gate.py`

**Status**: Modified
**Changes**:
- `_PIPELINE_FILES` reduced to single file: `html_to_markdown.py`
- `_detect_dead_config_dual()` replaced with `_detect_dead_config()` (single-file version)
- `partial_coverage` tracking removed from gate output
- `files_checked` retained in output

## New Files

### `scripts/mediawiki-api-extract/converters/infox_renderer.py`

**Status**: New
**Purpose**: Shared infobox rendering module, importable by both converters
**Key function**: `render_infobox_table(infobox_node, extraction_config, wiki_domain, ...) -> str`

## Dependency Changes

- `scripts/explore/requirements.txt`: Removed `markdownify>=0.11` (no longer needed by explore path)

## Known Differences (accepted per proposal)

- Infobox labels now bolded (`**label**` instead of plain text)
- Image alt text defaults to `image` instead of empty
- Output format consistent between pipeline and explore paths

## Pre-existing Issues (not introduced)

- Architecture Gate `fail` for BOI strategy due to cleanup operations only in `sample_converter.py` — this was masked by dual-file check and is a separate concern.
