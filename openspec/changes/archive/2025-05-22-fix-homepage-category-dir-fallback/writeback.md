# Writeback

## Summary

Fixed `_build_homepage_manifest()` cat_dir resolution to auto-fallback when strategy has no dir mapping, added target_path conflict detection in `run_convert()`, and completed Isaac wiki strategy categories.

## Changes to Project Files

### `docs/architecture/01-overview.md`

**Update needed**: None — changes are internal pipeline behavior improvements, no architecture-level impact.

### `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`

**Change**: Added two entries to `api.homepage.categories`:
- `{name: "Completion Marks", dir: "completion_marks"}`
- `{name: "Attributes", dir: "attributes"}`

**Impact**: Homepage discovery now correctly resolves these categories to their own directories instead of falling through to `items/`.

## Writeback Evidence

- [x] `strategy.md` updated directly (not a docs page, is a config artifact)
- [x] No architecture docs require update — internal pipeline fix
- [x] KI table update not needed — no issue tracking system referenced

## Verification Reference

See `verification.md` for full test evidence (11/11 tests passed).
