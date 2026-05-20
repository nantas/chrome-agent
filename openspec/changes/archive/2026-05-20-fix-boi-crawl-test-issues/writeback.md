# Writeback

## Change: fix-boi-crawl-test-issues

**Date**: 2026-05-20
**Based on**: verification.md (all checks pass)

## Writeback Targets

### Target 1: `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`

**Section**: `## Known Issues (Post-Validation)`

**Updates**:

Add new rows to the Known Issues table for P0-P5 fixes:

| ID | Issue | Status | Priority | Resolution |
|----|-------|--------|----------|------------|
| KI-8 | List page directory assignment bug | resolved | P0 | `_build_homepage_manifest()` uses strategy-backed `dir` mapping |
| KI-9 | Exclude filter misses title-based matches | resolved | P1 | Orchestrator checks `p["title"] in exclude_set` |
| KI-10 | Assembly creates orphan index.md for non-manifest list_pages | resolved | P2 | Assembly checks `manifest_pages_by_title` + `is_list_page` guard |
| KI-11 | Parenthesis filenames break Markdown links | resolved | P3 | `_to_markdown_link()` encodes `(` → `%28`, `)` → `%29` |
| KI-12 | YouTube "Load video" fallback text persists | resolved | P4 | `clean_html()` removes divs containing "Load video" |
| KI-13 | Frontmatter image selects decorative icons | resolved | P5 | `_process_html_page()` applies `skip_patterns` before image selection |

### Target 2: `outputs/handoffs/20260518-crawl-bindingofisaacrebirth-wiki-gg/handoff.md`

**Section**: Issue status updates

**Updates**:

- Issue 2 (list page index overwrites): **RESOLVED** — assembly now guards against non-manifest list_pages
- Issue 3 (orphan index files): **RESOLVED** — Mechanics/Cards/etc. no longer created
- Issue 4 (broken links from parens): **RESOLVED** — 123 → 7 broken links after encoding fix
- Issue 5 (YouTube residue): **RESOLVED** — "Load video" text removed by clean_html
- Issue 6 (frontmatter image): **RESOLVED** — skip_patterns applied before selection

## Summary of Changes

### Pipeline Code (7 files modified)

1. **discovery_homepage.py**: Strategy-config `dir` mapping for list page directory assignment
2. **orchestrator.py**: Title-based exclude filter (`p["title"] in exclude_set`)
3. **assemble.py**: Manifest existence check + `is_list_page` guard + empty directory cleanup
4. **converter.py**: Parenthesis URL-encoding in link generation + YouTube div removal
5. **link_fixer.py**: Parenthesis encoding fix for existing unencoded links
6. **convert.py**: `skip_patterns` image filtering in both HTML and wikitext conversion paths
7. **strategies/__init__.py**: URL-decode in link validation for encoded paths

### Quality Impact

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Broken links | 123 | 7 | -94% |
| Empty files | 9 | 7 | -22% |
| Orphan directories | 4+ | 0 | -100% |
| YouTube residue | Present | Gone | -100% |
| Wrong frontmatter images | Present | Filtered | Fixed |

## Writeback Execution Checklist

- [x] Update `strategy.md` Known Issues table with KI-8 through KI-13
- [x] Update `handoff.md` Issue 2-6 status to RESOLVED
- [x] Optionally update `tests/fixtures/boi-crawl-100-validation-baseline.json` to new baseline (7 broken links)
