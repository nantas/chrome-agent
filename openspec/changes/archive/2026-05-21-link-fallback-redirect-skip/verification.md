# Verification

## Change: link-fallback-redirect-skip

## Test Environment

- **Baseline**: BOI 100-page manifest (`tests/fixtures/boi-crawl-100-manifest.json`)
- **Strategy**: `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
- **Command**: `python3 -m scripts.pipeline pipeline ... --phase convert --validate`
- **Cache**: 97 cached pages from previous fetch

## Results

### Redirect Detection

| Metric | Value |
|--------|-------|
| Redirect pages detected | 6 |
| Redirect pages skipped (no .md output) | 6 |
| Redirect targets extracted successfully | 6 |

**Detected redirect pages:**

| Source Title | Redirect Target |
|-------------|----------------|
| The Shop | Greed Mode#Floors |
| Epilogue | Endings#Epilogue (Mom Ending) |
| Item | Items |
| Bloodshot Eye (Enemy) | Eye#Bloodshot Eye |
| Soul Heart | Hearts#Soul Heart |
| Isaac's last will | Isaac's Last Will |

### Empty Files

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Empty files | 7 | 1 | ✅ -6 |

Remaining empty file: `modes/index.md` (Category:Modes — not a redirect, expected)

### Broken Links

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Broken links | 8 | 8 | = |

All 8 broken links are pre-existing "Ending N" links that resolve to incorrect relative paths. None are caused by this change.

### Link Resolver Fallback

Verified that:
- ✅ `ExactTitleLinkResolver.resolve()` returns wiki URL for non-manifest targets
- ✅ `ShortNameLinkResolver.resolve()` returns wiki URL for non-manifest targets
- ✅ Manifest matches still produce relative `.md` paths (unchanged)
- ✅ Namespace-prefixed targets (File:, Category:) unaffected
- ✅ `domain` from constructor used in fallback URL

### Redirect Map Integration

- ✅ Redirect pages correctly skipped during convert phase
- ✅ Pipeline state records `status: "redirect"` for redirect pages
- ✅ Stats include `redirect_count: 6`
- ✅ Link fixer step 3 does not convert wiki URLs for redirect sources to broken .md paths

## Spec Coverage

| Spec Requirement | Verified |
|-----------------|----------|
| `link-resolver-fallback`: unresolved-link-fallback-to-wiki-url | ✅ Both resolvers return wiki URL |
| `link-resolver-fallback`: manifest-match-still-produces-relative-path | ✅ |
| `link-resolver-fallback`: domain-from-constructor | ✅ |
| `redirect-detection`: detect-mw-redirect | ✅ 6/6 detected |
| `redirect-detection`: redirect-page-skip-output | ✅ No .md files for redirect pages |
| `redirect-detection`: redirect-stats-reported | ✅ Logged + in extraction_results |
| `redirect-detection`: redirect-source-link-resolution | ✅ redirect_map injected |
| `pipeline-converters`: redirect-html-detection-before-convert | ✅ Pre-scan approach |
| `pipeline-converters`: normal-page-unaffected-by-redirect-check | ✅ 91/91 normal pages converted |

## Conclusion

All spec requirements verified. Empty files reduced from 7 to 1. No regressions in broken links. Change is ready for writeback and archive.
