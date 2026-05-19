# Verification Report

**Change**: `split-fetch-convert-phases`
**Date**: 2026-05-19
**Verification Round**: 2 (post-fix)

## Summary

| Section | Status | Notes |
|---------|--------|-------|
| Python cache module | ✅ Pass | Unit-tested: save/load/cached/uncached/list |
| Phase B refactor | ✅ Pass | fetch_single_page + convert_single_page extracted, process_single_page preserved |
| `convert_single_page` content_acquisition detection | ✅ Pass | Now uses cache metadata field + field presence fallback |
| Dead code in convert_single_page | ✅ Removed | Unreachable `if not wikitext:` guard eliminated |
| run_phase_fetch | ✅ Pass | Importable, correct signature |
| run_phase_convert | ✅ Pass | Importable, correct signature, stats aligned |
| `--phase convert` requires `--from-manifest` | ✅ Fixed | Fails with error when --from-manifest is absent |
| CLI --phase choices | ✅ Pass | New choices (all/discover/fetch/convert/assemble) shown in help |
| --re-fetch flag | ✅ Pass | Present in help output |
| Deprecated value rejection | ✅ Pass | --phase extract/A/B/C/homepage all rejected by argparse |
| Deprecated flag warnings | ✅ Pass | --keep-html writes warning, --no-markdown writes tip |
| JS CLI --phase parsing | ✅ Fixed | `--phase <value>` and `--re-fetch` now parsed and forwarded |
| JS CLI dispatch | ✅ Fixed | `phase` and `reFetch` passed from parseArgs to runCrawl() |
| JS CLI syntax | ✅ Pass | node --check clean |
| .gitignore | ✅ Pass | `.cache/` excluded |
| Isaac wiki strategy | ✅ Pass | File exists, parseable |

## Fixes Applied During Verification

### Fix 1: JS CLI `parseArgs()` missing `--phase` and `--re-fetch`

**Problem**: `parseArgs()` in `scripts/chrome-agent-cli.mjs` had no handler for `--phase` or `--re-fetch` flags. The return object and dispatch `case "crawl":` block also didn't include these fields.

**Changes** (`scripts/chrome-agent-cli.mjs`):
- Added `let phase = null;` and `let reFetch = false;` variable declarations
- Added `--phase <value>` / `--phase=<value>` and `--re-fetch` parsing handlers after `--exclude-category` handler
- Added `phase` and `reFetch` to the `return {}` in `parseArgs()`
- Added `phase: parsed.phase` and `reFetch: parsed.reFetch` to `runCrawl()` opts in `case "crawl":` dispatch

**Verification**: `node --check scripts/chrome-agent-cli.mjs` passes; grep confirms variables declared, parsed, returned, and dispatched.

### Fix 2: `--phase convert` silently runs discovery when `--from-manifest` absent

**Problem**: When `--phase convert` was specified without `--from-manifest`, the pipeline silently performed discovery then attempted conversion, rather than failing with an error as the spec requires.

**Changes** (`scripts/mediawiki-api-extract/pipeline/orchestrate.py`):
- Added explicit check before Convert Phase block:
  ```python
  if "convert" in phases and "all" not in phases and not from_manifest:
      log.error("--phase convert requires --from-manifest")
      return EXIT_INVALID_ARGS
  ```

**Verification**: `python3 -m scripts.mediawiki-api-extract pipeline --phase convert ...` now outputs `[ERROR] --phase convert requires --from-manifest` and exits.

### Fix 3: Unreachable code in `convert_single_page()`

**Problem**: `if wikitext:` block contained `if not wikitext:` guard that was structurally unreachable (always false).

**Changes** (`scripts/mediawiki-api-extract/pipeline/phase_b.py`):
- Removed the dead guard `if not wikitext:` and its early-return dict

### Fix 4: Content acquisition path detection uses `content_acquisition` field

**Problem**: `convert_single_page()` used field presence detection (`html and not wikitext`) rather than the explicit `content_acquisition` field saved in cache, causing robustness concerns.

**Changes** (`scripts/mediawiki-api-extract/pipeline/phase_b.py`):
- Reads `raw.get("content_acquisition")` from cached data
- Uses it as primary heuristic for HTML vs wikitext path selection
- Falls back to field presence detection for backward compatibility

## Verification Steps Requiring Manual Execution (with network)

| Step | Command | Expected |
|------|---------|----------|
| 5.2-1 | `chrome-agent crawl <url> --discovery-only` | Produces manifest |
| 5.2-2 | `--phase fetch --from-manifest <manifest>` | .cache/ files created |
| 5.2-3 | `--phase convert --from-manifest <manifest>` | .md files created, no network |
| 5.2-4 | Modify extraction rules → `--phase convert` | Output reflects changes |
| 5.2-5 | `--phase fetch` again | All pages skipped (cached) |
| 5.2-6 | Delete 1 cache file → `--phase fetch` | Only that page re-fetched |
| 5.2-7 | `--phase fetch --re-fetch` | All pages overwritten |
| 5.2-8 | Offline `--phase convert` | Succeeds with no network |

## Regression Checks

| Check | Result |
|-------|--------|
| `process_single_page()` still exported | ✅ |
| `run_phase_b()` signature unchanged | ✅ |
| `run_pipeline()` accepts old CLI flow (`--phase all`) | ✅ |
| `__future__` annotations preserved | ✅ |

## Known Issues

All issues identified during verification have been fixed:
- 🔴 CRITICAL: JS CLI --phase parsing — ✅ fixed
- 🟡 WARNING: --phase convert requires --from-manifest — ✅ fixed
- 🟡 WARNING: unreachable code — ✅ fixed
- 🟢 SUGGESTION: content_acquisition field detection — ✅ implemented

No remaining known issues. The implementation strictly follows the spec deltas in `openspec/changes/split-fetch-convert-phases/specs/`.
