# Verification

## Spec-to-Implementation Matrix

### pipeline-registry
| Requirement | Status | Evidence |
|-------------|--------|----------|
| strategy-registry-module | ✅ PASS | `scripts/pipeline/pipeline/registry.py` exists, 149 lines ≤ 160, contains all required symbols |
| build-pipeline-factory | ✅ PASS | `build_pipeline()` present with identical signature and behavior |
| derive-capabilities-function | ✅ PASS | `derive_capabilities()` present with identical behavior |
| strategy-registry-public-api | ✅ PASS | `__init__.py` re-exports `STRATEGY_REGISTRY`, `PROFILE_KEY_MAP`, etc. via `from .registry import ...` |

### pipeline-discovery-summary
| Requirement | Status | Evidence |
|-------------|--------|----------|
| discovery-summary-module | ✅ PASS | `scripts/pipeline/pipeline/discovery_summary.py` exists, contains all 6 functions |
| discovery-summary-imports | ✅ PASS | No import of `orchestrate.py` or `orchestrator.py`; imports only `...lib.config_resolver` |
| unit-test-compatibility | ✅ PASS | 12/12 tests pass: `python3 scripts/pipeline/tests/test_discovery_summary.py` |

### pipeline-phases-fetch
| Requirement | Status | Evidence |
|-------------|--------|----------|
| fetch-phase-module | ✅ PASS | `scripts/pipeline/pipeline/phases/fetch.py` exists with `run_phase_fetch()` and `_fetch_one()` |
| fetch-phase-imports | ✅ PASS | No import of orchestrator; uses `...client`, `..phase_b`, `..cache`, `...strategies` |
| fetch-phase-no-behavior-change | ✅ PASS | Code identical to original (verified by diff) |

### pipeline-phases-convert
| Requirement | Status | Evidence |
|-------------|--------|----------|
| convert-phase-module | ✅ PASS | `scripts/pipeline/pipeline/phases/convert.py` exists with `run_phase_convert()` |
| convert-phase-imports | ✅ PASS | No import of orchestrator; uses `..phase_b`, `..registry`, `..cache`, `...strategies` |
| convert-phase-no-behavior-change | ✅ PASS | Code identical to original (verified by diff) |

### pipeline-orchestration
| Requirement | Status | Evidence |
|-------------|--------|----------|
| orchestrator-responsibility | ✅ PASS | `orchestrate.py` contains only exit codes, `validate_api_config()`, `run_pipeline()`; all extracted code removed |
| orchestrator-size-limit | ⚠️ PARTIAL | 457 lines (target ≤ 350). `run_pipeline()` alone is ~370 lines — target infeasible without splitting `run_pipeline()` (Change 5) |
| run-pipeline-no-behavior-change | ✅ PASS | `run_pipeline()` delegates to extracted modules; `python3 -m scripts.pipeline --help` succeeds |
| public-api-compatibility | ✅ PASS | `__init__.py` re-exports all public symbols from `orchestrate.py` + `registry.py` |

### pipeline-package-identity
| Requirement | Status | Evidence |
|-------------|--------|----------|
| package-rename | ✅ PASS | `scripts/pipeline/` exists; `grep mediawiki_api_extract scripts/pipeline/ → 0 matches` |
| main-simplification | ✅ PASS | `__main__.py` is 8 lines, no `subprocess.call`, direct `from .cli import main` |
| cli-spawn-path-update | ✅ PASS | `grep mediawiki-api-extract scripts/chrome-agent-cli.mjs → 0 matches` |
| logger-name-update | ✅ PASS | `grep getLogger.*mediawiki-api-extract scripts/ → 0 matches` |
| external-reference-update | ✅ PASS | `grep mediawiki-api-extract scripts/explore/ → 0 matches` |
| test-reference-update | ✅ PASS | `grep mediawiki-api-extract scripts/pipeline/tests/ → 0 matches` |

## Task-to-Evidence Matrix

| Task | Status | Evidence |
|------|--------|----------|
| 1.1 Spec coverage | ✅ | 6 specs exist in `openspec/changes/split-orchestrator-rename-package/specs/` |
| 1.2 Prerequisites | ✅ | `lib/` imports in orchestrate.py confirmed; `_extract_infobox` removed |
| 2.1 registry.py | ✅ | File created, 149 lines, compile OK |
| 2.2 discovery_summary.py | ✅ | File created, compile OK |
| 2.3 phases/ dir | ✅ | `phases/__init__.py` created |
| 2.4 phases/fetch.py | ✅ | File created, compile OK |
| 2.5 phases/convert.py | ✅ | File created, compile OK |
| 2.6 orchestrate.py slimmed | ✅ | Extracted code removed, delegates via imports |
| 2.7 __init__.py exports | ✅ | Public API preserved, `python3 -m scripts.pipeline --help` works |
| 2.8 E2E verification (pre-rename) | ✅ | 12/12 tests pass, no circular imports |
| 2.9 Directory rename | ✅ | `scripts/pipeline/` exists |
| 2.10 Absolute imports | ✅ | 0 matches for `mediawiki_api_extract` in `.py` files |
| 2.11 __main__.py simplified | ✅ | 8 lines, no subprocess |
| 2.12 CLI paths | ✅ | 0 matches for `mediawiki-api-extract` in `.mjs` |
| 2.13 Logger names | ✅ | All updated to `getLogger("pipeline")` |
| 2.14 Explore references | ✅ | 0 matches in `scripts/explore/` |
| 2.15 Test references | ✅ | 0 matches in `scripts/pipeline/tests/` |
| 2.16 User-Agent | ✅ | Updated to `chrome-agent/pipeline` |
| 2.17 strategies.py docstring | ✅ | Updated to `scripts.pipeline.strategies` |
| 2.18 converters docstrings | ✅ | 0 matches for old paths |
| 3.1 Evidence checklist | ✅ | All verifications pass |
| 3.2 AGENTS.md writeback targets | ✅ | Identified: §7 registry path, §9 package conventions |

## Test Results

| Test Suite | Result | Details |
|------------|--------|---------|
| Python unit tests | 12/12 PASS | `python3 scripts/pipeline/tests/test_discovery_summary.py` |
| Node.js runtime tests | 9/9 PASS | `node --test tests/chrome-agent-runtime.test.mjs` |
| `python3 -m scripts.pipeline --help` | PASS | CLI loads and displays help |
| Old reference grep | CLEAN | 0 matches across `.py` and `.mjs` |

## Notes

1. **orchestrate.py line count (457 vs target 350)**: The `run_pipeline()` function alone is ~370 lines. Further reduction requires splitting `run_pipeline()` into sub-functions, which is explicitly scoped to Change 5 (CLI runCrawl refactoring). The 350-line target was estimated before measuring `run_pipeline()`'s actual size.
2. **Behavior preservation**: All code extraction was done via copy-paste of identical code blocks — no logic changes, no refactoring of extracted functions.
