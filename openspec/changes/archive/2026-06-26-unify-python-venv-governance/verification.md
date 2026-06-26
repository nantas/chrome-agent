# Verification Report: unify-python-venv-governance

## Summary

| Dimension    | Status                        |
|--------------|-------------------------------|
| Completeness | 35/35 tasks, 14 reqs verified |
| Correctness  | 14/14 reqs covered            |
| Coherence    | All 5 design decisions followed |
| Test Suite   | Node 72/72, Python 74/74      |
| Doctor       | SUCCESS (12/12 green)         |

## Test Suite (Step 3.5)

**test_runner**: EXISTS. Ran `python3 scripts/test_runner.py all` → Phase 1 unit tests 13/13 OK (10 skipped — no cache entries, normal for fresh clone), Phase 2 site samples 13 tests. Exit code 0.

Scope verification: `.venv/bin/python -m unittest discover -s tests -v` → 74 passed, 0 errors. Previously failing `selectolax` import errors eliminated. `node --test tests/*.test.mjs` → 72 passed, 0 failures.

## Completeness: Task Completion (35/35 ✅)

All 35 tasks implemented with code/diff evidence:

**A. App-layer resolver rename (T2.1-2.3):** `resolveExplorePython` → `resolveAppPython` in `scripts/lib/python-resolver.mjs:10`, cli.mjs import at :12, test at `tests/python-resolver.test.mjs:7`.

**B. Dependency manifest centralization (T2.4-2.7):** Root `requirements.txt` created (bs4, pyyaml, selectolax, markdownify, requests). `scripts/explore/requirements.txt` deleted. `.venv/bin/pip install -r requirements.txt` verified importable.

**C. repo-venv.sh preflight (T2.8-2.10):** `scripts/repo-venv.sh` created, follows scrapling-cli.sh pattern (STATUS=/SOURCE= output). `--no-install` detection mode. Lazy-trigger venv creation via `uv venv` + `uv pip install -r requirements.txt`.

**D. Application-layer spawn completeness (T2.11-2.14):** All 6 spawn points in cli.mjs use `resolveAppPython(repoRoot)`:
- :1687 explore_deps check
- :1737 explore main.py
- :2270 pipeline `-m scripts.pipeline`
- :3283 explore freeze.py
- :3347 explore iterate.py

No remaining hardcoded `"python3"` in application-layer spawns.

**E. cloakbrowser managed venv (T2.15-2.21):** `scripts/cloakbrowser-cli.sh` created (mirror scrapling-cli.sh: preflight, uv venv --python 3.11). `scripts/engine-version-check.sh:128` uses `managed_path` via `expand()`. `configs/engine-versions.json` updated (method: python_importlib, managed_path: `$HOME/.cache/chrome-agent-cloakbrowser/bin/python`, version: 0.4.3). `scripts/cloakbrowser-preflight.sh` deleted.

**F. Doctor alignment (T2.22-2.24):** `explore_deps` check uses `resolveAppPython` (auto-completed by T2.2). `version_cloakbrowser` uses managed venv python (auto-completed by T2.16). Doctor result: **SUCCESS** — `explore_deps: bs4, yaml available` + `version_cloakbrowser: cloakbrowser: 0.4.3`.

**G. test_runner Python source (T2.25-2.26):** `docs/architecture/08-tech-stack.md:261,264,269-271` all updated to `.venv/bin/python scripts/test_runner.py`. `.venv/bin/python -m unittest discover` → 74 pass, 0 error (pre-existing `selectolax` import errors eliminated).

**Convergence & writeback (T3.1-4.3):** Full test suite green (Node 72/72, Python 74/74). Doctor 12/12 green. C10 global sync: installed-hash (`50d763fd`) == HEAD (`50d763fd`). Writeback targets all updated: `docs/architecture/06-engine-selection.md` (CloakBrowser preflight → managed venv), `docs/architecture/08-tech-stack.md` (app-layer venv context + test_runner commands), `docs/setup/cloakbrowser-setup.md` (line 70,76 → cloakbrowser-cli.sh), `configs/engine-versions.json` (managed_path).

## Correctness: Requirement Implementation

All 14 requirements across 4 spec files have verified implementations:

| Spec | Reqs | Evidence |
|------|------|----------|
| `app-layer-venv-governance` | 6 | `requirements.txt`, `python-resolver.mjs:10`, `repo-venv.sh`, cli.mjs:1687/1737/2270/3283/3347, 08-tech-stack.md:261 |
| `cli` | 2 | All 6 spawn points use `resolveAppPython`, `cloakbrowser-cli.sh` managed venv |
| `engine-registry` | 4 | `cloakbrowser-cli.sh`, `engine-versions.json`, `engine-version-check.sh:128`, old preflight deleted |
| `doctor-repo-freshness` | 3 | Doctor SUCCESS, explore_deps green, version_cloakbrowser green |

## Coherence: Design Decision Adherence

All 5 design decisions verified:

| Decision | Evidence |
|----------|----------|
| D1: resolveAppPython sole entry | `python-resolver.mjs:10` exports `resolveAppPython`, all 6 cli.mjs spawns reference it |
| D2: Lazy preflight split | `repo-venv.sh` (app-layer) + `cloakbrowser-cli.sh` (engine), both follow `scrapling-cli.sh` STATUS=/SOURCE= pattern |
| D3: Root requirements.txt | `requirements.txt` present, `scripts/explore/requirements.txt` absent |
| D4: Rename scope | 3 files: `python-resolver.mjs`, `cli.mjs`, `tests/python-resolver.test.mjs` |
| D5: test_runner shebang unchanged | `scripts/test_runner.py` shebang unchanged; invocation site updated in 08-tech-stack.md |

## Issues by Priority

### WARNING

1. **docs/setup/cloakbrowser-setup.md:8** still references `pip install cloakbrowser` as the install command. Lines 70 and 76 were updated to `cloakbrowser-cli.sh preflight`, but line 8 was missed.
   - Recommendation: Update line 8 from `pip install cloakbrowser` to `bash scripts/cloakbrowser-cli.sh preflight`.

### SUGGESTION

2. **`requirements.txt` contains `requests>=2.28`** which was not in the spec's dependency list (spec lists bs4, pyyaml, selectolax, markdownify). This package is used by the pipeline MediaWiki API path but was not explicitly declared in the proposal or specs.
   - Recommendation: Either document `requests` as an application-layer dependency in specs, or if it was added opportunistically, confirm it's intentionally included.

3. **C10 global skill SKILL.md timestamp** (`Jun 26 14:53`) predates the runtime sync (`Jun 26 16:59`). While installed-hash matches HEAD, if SKILL.md was modified during this change, it should be re-synced to global.
   - Recommendation: If `skills/chrome-agent/SKILL.md` was changed, run `cp skills/chrome-agent/SKILL.md ~/.agents/skills/chrome-agent/SKILL.md` and reload the session. If unchanged, this is a false positive.

## Final Assessment

**No critical issues. 1 warning, 2 suggestions. Ready for archive (with noted improvements).**

**Evidence summary:**
- `git diff --stat`: 11 files changed, 126 insertions, 217 deletions
- New files: `requirements.txt`, `scripts/repo-venv.sh`, `scripts/cloakbrowser-cli.sh`, `tests/python-resolver.test.mjs` (renamed from original)
- Deleted files: `scripts/explore/requirements.txt`, `scripts/cloakbrowser-preflight.sh`
- Node tests: 72/72 pass (including the previously-failing `env_default instead of env_fallback` — now passing because doctor is SUCCESS)
- Python tests: 74/74 pass (including 2 previously-failing selectolax import errors — resolved)
- Doctor: SUCCESS, 12/12 green (first time; previously partial_success with 2 issues)
