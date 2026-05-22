# Writeback

## Change: fix-source-category-multi-match-fallback

## Verification Status

**PASS** — See `verification.md` for full evidence.

## Writeback Targets

### Target 1: `openspec/specs/page-assignment/spec.md`

**Action**: Merge spec delta (Step 3.5 fallback requirement) into live spec.

**Content to merge**:

Add the following requirement to the live spec:

#### Requirement: source-category-fallback-after-mw
After Step 3 (MW category matching) completes and before Step 4 (default to misc), the system SHALL perform a fallback assignment step (Step 3.5) for pages that remain unassigned. This step SHALL use first-match-wins on `source_categories` against `assignment_priority` — the same priority order used in Step 2, but without the exact-1-match restriction.

**New assignment_method value**: `"source_category_fallback"`

**Scenarios**:
1. **fallback-assigned-with-first-match-wins**: Unassigned page with multi-match source_categories → assigned to first priority match
2. **fallback-skipped-for-already-assigned**: Already-assigned pages (Step 2) not reassigned
3. **fallback-skipped-for-mw-match**: MW-matched pages not overridden
4. **fallback-uses-priority-ordering**: Uses `assignment_priority` order, not `source_categories` list order
5. **no-fallback-match**: No matching categories → remains unassigned → Step 4 → misc

## Writeback Execution

- [x] Merge spec delta into `openspec/specs/page-assignment/spec.md`
