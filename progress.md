# Progress

## Status
In Progress

## Tasks
- [x] Fix S5 regex false-positive in self_check.py
- [x] Update strategy.md with V4 validation results (config-driven approach)

## Files Changed
- `scripts/explore/self_check.py` — S5 version-number regex: exclude backtick-wrapped and multi-segment entity IDs
- `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — Strategy-driven config updates:
  - Expanded cleanup_selectors (div.nav-box, div.nav-main, etc.)
  - Expanded image_filtering.skip_patterns (SmallIsaac.png, MainPage*.png)
  - New extraction.infobox block (selector, field/label/value selectors)
  - New extraction.lazyload block (placeholder_pattern, real_src_attr)
  - New extraction.url_conversion block
  - New extraction.youtube_cleanup block
  - Added unwrap_image_wrappers to cleanup list
  - New api.parse_options block (redirects, prop)
  - Added ## Validation (2026-05-17) section
  - Added ## Known Issues (Post-Validation) section with KI-1..KI-6
  - Appended validation timestamp to Evidence section

## Design Principle
Strategy file is the single source of truth. Pipeline code reads config and executes.
No site-specific class names or HTML structure assumptions in pipeline code.

### sample_converter.py Refactor (strategy-driven pipeline)

- [x] Add imports: NavigableString, re, urllib.request, urllib.parse
- [x] Add _fetch_via_mediawiki_api() — generic MediaWiki API fetch with redirect following
- [x] Register mediawiki-api engine in _fetch_sample()
- [x] Add _extract_infobox() — generic infobox extraction driven by config selectors
- [x] Rewrite _apply_extraction() as pure config interpreter:
  - Phase 1: Infobox extraction reads infobox selector/field/label/value from config
  - Phase 2: cleanup_selectors from config → generic CSS selector stripping
  - Phase 3: lazyload config → placeholder_pattern + real_src_attr
  - Phase 4: cleanup list operations (existing ops preserved as optional)
  - Phase 5: Content selection from config selectors
  - Phase 6: Post-conversion normalization from config (url_conversion, youtube_cleanup, text_normalization)
- [x] Update convert() to route mediawiki-api engine to _fetch_via_mediawiki_api()

Verified: No hardcoded site-specific class names in _apply_extraction or _extract_infobox.
All 8 config keys (infobox, cleanup_selectors, lazyload, skip_patterns, url_conversion, youtube_cleanup, cleanup, text_normalization) are read from extraction_rules.
