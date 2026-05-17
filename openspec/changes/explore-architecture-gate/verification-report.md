# Verification Report: explore-architecture-gate

> Generated: 2026-05-17 | Implementation: `scripts/explore/architecture_gate.py` (580 lines)

## Summary

| Dimension | Status | Detail |
|-----------|--------|--------|
| Completeness | ⚠️ 23/23 tasks done, 1 real violation found | Gate correctly identifies 9 dead cleanup ops in live strategy |
| Correctness | ✅ 5/5 spec requirements implemented | Full scenario coverage, blocking exit code works |
| Coherence | ✅ Design fully followed | All 5 audit checks implemented, config-driven guard detection |

---

## 1. Completeness

### Task Completion

| # | Task | Status | Evidence |
|---|------|--------|----------|
| 1.1 | Spec coverage confirmed | ✅ | 5 requirements in `specs/explore-architecture-gate/spec.md` |
| 1.2 | Pipeline source path confirmed | ✅ | `_PIPELINE_REL = "scripts/explore/sample_converter.py"` |
| 1.3 | Audit 5 items cover commit 55ac8d4 violations | ✅ | Checks A-E: selectors, CSS classes, domains, file patterns, unconditional ops |
| 2.1.1 | `architecture_gate.py` created | ✅ | File exists at `scripts/explore/architecture_gate.py` (580 lines) |
| 2.1.2 | `_detect_dead_config()` | ✅ | Lines 92-110, regex-based field consumer detection |
| 2.1.3 | Cleanup operation enumeration | ✅ | `detect_dead_cleanup_operations()` at line 139 |
| 2.1.4 | Dead config verification | ✅ | Gate correctly detects 9 dead cleanup ops in Isaac Wiki strategy (see §4) |
| 2.2.1 | `_audit_pipeline()` | ✅ | Lines 167-249, returns violation dicts |
| 2.2.2 | Check A: Hardcoded selectors | ✅ | `_check_hardcoded_selectors()` lines 251-301 |
| 2.2.3 | Check B: Hardcoded CSS classes | ✅ | `_check_hardcoded_css_classes()` lines 303-365 |
| 2.2.4 | Check C: Hardcoded domains | ✅ | `_check_hardcoded_domains()` lines 433-475 |
| 2.2.5 | Check D: Hardcoded filename patterns | ✅ | `_check_hardcoded_filename_patterns()` lines 477-510 |
| 2.2.6 | Check E: Unconditional operations | ✅ | `_check_unconditional_operations()` lines 512-580 |
| 2.2.7 | Audit verification | ✅ | Commit 08e3ea9 pipeline passes P→S audit (0 violations) |
| 2.3.1 | `validate()` output format | ✅ | Returns `{status, strategy_to_pipeline, pipeline_to_strategy}` |
| 2.3.2 | main.py integration | ✅ | `main.py:162` — Gate called after self-check, before output |
| 2.3.3 | Gate blocks on failure | ✅ | `main.py:193-198` — exit code 2 on gate fail |
| 3.1-3.3 | Regression verification | ✅ | Gate logic tests pass (clean passes, dirty fails) |

### Dead Config Detection — Live Result

Running the gate against the current `bindingofisaacrebirth.wiki.gg` strategy:

```
Strategy→Pipeline: FAIL
dead_config:
  - cleanup.strip_footer
  - cleanup.strip_edit_links
  - cleanup.strip_skip_links
  - cleanup.strip_empty_parens
  - cleanup.convert_nested_images
  - cleanup.normalize_internal
  - cleanup.strip_category_links
  - cleanup.normalize_infobox
  - cleanup.fix_separators
```

These 9 cleanup operations are listed in the strategy's `extraction.cleanup` but have **zero consumers** in `sample_converter.py`. The pipeline only supports 3 cleanup ops: `strip_fandom_infobox_tables`, `convert_ambox_to_text`, `unwrap_image_wrappers`.

---

## 2. Correctness

### Requirement Implementation Mapping

| Requirement | Implementation | Evidence |
|------------|---------------|----------|
| gate-position | Phase 8 in main.py:162, after self-check, before output | `main.py:162-170` |
| strategy-to-pipeline-validation | `_detect_dead_config()` + `detect_dead_cleanup_operations()` | `architecture_gate.py:92-163` |
| pipeline-to-strategy-audit | `_audit_pipeline()` with 5 sub-checks | `architecture_gate.py:167-580` |
| gate-must-pass-before-confirmation | Exit code 2 on fail; `output.architecture_gate` includes result | `main.py:193-198` |
| gate-output-format | `validate()` returns `{status, strategy_to_pipeline: {status, dead_config[]}, pipeline_to_strategy: {status, violations[]}}` | `architecture_gate.py:81-90` |

### Scenario Coverage

| Scenario | Covered? | Evidence |
|----------|----------|----------|
| dead-config-detection | ✅ | 4 regex patterns for `.get()`, `[]`, `in`, `if` |
| cleanup-operations-validation | ✅ | `detect_dead_cleanup_operations()` checks `"op_name" in cleanup` pattern |
| nested-fields-validation | ✅ | Parent key detection; sub-fields validated via consumer pattern |
| no-hardcoded-selectors | ✅ | `_check_hardcoded_selectors()` with 21 generic selector exemptions |
| no-hardcoded-domain-names | ✅ | `_check_hardcoded_domains()` with 8 skip-domain exemptions |
| no-unconditional-site-operations | ✅ | `_check_unconditional_operations()` detects 3 guarded ops (youtube, url_conversion, lazyload) |
| gate-failure-blocks-confirmation | ✅ | Exit code 2 returns `partial_success` |
| gate-pass-allows-confirmation | ✅ | Exit code 0 on pass |
| output-structure | ✅ | `validate()` returns all 3 blocks |

---

## 3. Coherence

### Design Adherence

| Design Decision | Followed? | Evidence |
|----------------|-----------|----------|
| Phase 2 positioning (after self-check, before confirmation) | ✅ | `main.py:162` — Phase 8 label |
| Check 1: programmatic dead config | ✅ | `_detect_dead_config()` + cleanup enum check |
| Check 2: agent audit checklist 5 items | ✅ | All 5 sub-checks (A-E) implemented |
| Gate must pass before confirmation | ✅ | Exit code 2 blocks |
| Architecture violations don't count toward 3-iteration limit | ✅ | Gate runs separately from self-check loop |
| Output format matches design | ✅ | `{status, strategy_to_pipeline{status, dead_config[]}, pipeline_to_strategy{status, violations[]}}` |

### Code Pattern Consistency

| Pattern | Consistent? | Note |
|---------|------------|------|
| File location | ✅ | `scripts/explore/architecture_gate.py` — same dir as other explore modules |
| Import style | ✅ | `from architecture_gate import validate` — same pattern as other imports in main.py |
| Function naming | ⚠️ | `_detect_dead_config` (private) vs `detect_dead_cleanup_operations` (public) — inconsistent underscore prefix |
| Error handling | ✅ | Pipeline file missing → returns fail dict, not raise |
| Docstrings | ✅ | Module + all functions have docstrings |

---

## 4. Issues

### CRITICAL

**C1: 9 dead cleanup operations in production strategy**

The `bindingofisaacrebirth.wiki.gg` strategy lists 10 cleanup operations, but only 1 (`unwrap_image_wrappers`) is consumed by the pipeline. The other 9 are dead config that the gate correctly identified.

```
Strategy lists:     Pipeline consumes:
  strip_footer           (none)
  strip_edit_links       (none)
  strip_skip_links       (none)
  strip_empty_parens     (none)
  convert_nested_images  (none)
  normalize_internal     (none)
  strip_category_links   (none)
  normalize_infobox      (none)
  fix_separators         (none)
  unwrap_image_wrappers  unwrap_image_wrappers ✓
```

**Recommendation**: Either (a) implement these 9 cleanup operations in `sample_converter.py` as config-driven handlers, or (b) remove them from the strategy's `cleanup` list and move their effects to other config fields (e.g., `text_normalization` for `fix_separators`).

### WARNING

**W1: Function naming inconsistency**

`_detect_dead_config()` uses private prefix but `detect_dead_cleanup_operations()` does not. Both are internal implementation details.

**Recommendation**: Rename `detect_dead_cleanup_operations` → `_detect_dead_cleanup_operations` for consistency.

### SUGGESTION

**S1: Guard detection regex could be more robust**

`_check_unconditional_operations()` relies on regex to find config guards. Complex guard patterns (e.g., nested conditions with `and`/`or`) might not be detected.

**Recommendation**: Not blocking — current patterns cover all known cases. Consider AST-based analysis in future iteration.

**S2: Hardcoded selector check has blind spots**

`_check_hardcoded_selectors()` only detects `soup.select_one("...")` and `soup.select("...")` calls. It does not detect `BeautifulSoup(...)` HTML parsing calls or hardcoded selectors in f-strings.

**Recommendation**: Acceptable for v1. The 21 generic selector exemptions cover all current pipeline patterns. Extend in v2 if new violation types emerge.

---

## Final Assessment

**1 CRITICAL issue found. Fix before archiving.**

The Architecture Gate is correctly implemented and operational — it has already caught a real dead config issue in the production Isaac Wiki strategy. The gate's blocking behavior (exit code 2) and integration point (main.py:162) match the spec exactly.

The critical issue (C1) is not a bug in the gate — it's a bug the gate **found**. Fix the 9 dead cleanup operations in the strategy (or pipeline), then run `/opsx-verify` again for a clean pass.
