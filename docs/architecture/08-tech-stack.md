# 08 — Tech Stack & Development Guide

> **Source**: AGENTS.md §6 development content
>
> **Applicable to**: Contributors modifying `scripts/`, `configs/`, or `sites/`

## 1. Runtime Dependencies

### Node.js Dependencies (`package.json`)

| Package | Version | Purpose |
|---------|---------|---------|
| `better-sqlite3` | `^12.8.0` | SQLite database access (CLI cache/manifest) |
| `yaml` | `^2.8.3` | YAML frontmatter parsing for strategy files |

No TypeScript, no build step. All `.mjs` files are pure ESM executed directly.

### Python Dependencies

| Scope | Package | Version | Purpose |
|-------|---------|---------|---------|
| Explore (`scripts/explore/requirements.txt`) | `beautifulsoup4` | `>=4.12` | HTML parsing (BS4 mode) |
| Explore | `pyyaml` | `>=6.0` | YAML frontmatter parsing |
| Explore | `selectolax` | `>=0.3` | Fast HTML parsing (selectolax mode) |
| Pipeline (`scripts/pipeline/`) | *(none declared)* | — | Uses stdlib + selectolax (via html_to_markdown) |

### External Engine Dependencies

Managed via `configs/engine-versions.json`:

| Engine | Install Method | Managed Path |
|--------|---------------|--------------|
| Scrapling | Python venv (pip) | `$HOME/.cache/chrome-agent-scrapling/` |
| Obscura | Precompiled binary (GitHub Release) | `$HOME/.cache/chrome-agent-obscura/bin/` |
| CloakBrowser | pip module | System Python (`~/.cloakbrowser/chromium-{ver}/`) |

See `docs/architecture/06-engine-selection.md` for version details and upgrade procedures.

## 2. Language Conventions

### Node.js (`.mjs` files)

| Convention | Rule |
|-----------|------|
| Module system | Pure ESM (`import`/`export`), no CommonJS |
| TypeScript | Not used — no compilation step |
| Function style | Top-level function declarations (`function xxx()`), not arrow functions |
| Path resolution | `__dirname` + `path.resolve` for `repoRoot` inference |
| CLI output | JSON-first (`--format json`), text mode is rendering layer only |
| Error handling | `process.exit(1)` for CLI errors, exceptions for library code |

### Python (`.py` files)

| Convention | Rule |
|-----------|------|
| Compatibility | **Python 3.9+**: Use `from typing import Optional` instead of `X \| Y` union syntax |
| Import style | Relative imports within packages (`from .module import func`) |
| Pipeline invocation | `python3 -m scripts.pipeline <subcommand>` (not direct file execution) |
| Explore invocation | `python3 scripts/explore/main.py <args>` (uses `sys.path.insert` for local imports) |
| Logging | `logging.getLogger(__name__)` pattern |
| Type annotations | `from __future__ import annotations` enables PEP 604 syntax in type hints |

**Key compatibility note**: `sample_converter.py` uses `from typing import Optional` (line 8) — no `dict | None` syntax that would break on Python 3.9. Meanwhile, `html_to_markdown.py` uses `from __future__ import annotations` (line 1) which defers type evaluation, allowing `dict | None` in annotations without runtime errors even on Python 3.9.

### Shell Scripts (`.sh` files)

| Convention | Rule |
|-----------|------|
| Shebang | `#!/bin/sh` or `#!/usr/bin/env bash` |
| Error handling | `set -eu` or `set -euo pipefail` |
| Path calculation | `SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)` + `REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)` |
| Logging | `printf '%s\n' "$*" >&2` to stderr |

## 3. LSP Code Intelligence Patterns

This repository uses `lsp-pi` extension with pyright (Python) and TypeScript language servers. Four verified patterns cover the most common code investigation tasks.

### Pattern 1: Dead Code Detection

```
lsp references(file="path/to/module.py", line=<def_line>, column=5)
```

From the **function definition line** (not call site), check all references:
- Self-definition line → not a real reference
- Import statements → module dependency only, not runtime usage
- Actual call sites → real consumers

**Dead code verdict**: If references contain only self-definition + imports (no calls), the function is dead code. If importers are also dead, it's a **dead chain** safe to remove entirely.

### Pattern 2: Dead Import Verification

```
lsp references(file="registry.py", line=20, column=29)
```

Column must point to the **symbol name** (not `from` keyword). Dead imports don't affect runtime but add maintenance burden.

### Pattern 3: Cross-File Call Chain Tracing

```
# Jump to definition from call site
lsp definition(file="phases/fetch.py", line=9, column=23)

# From definition, find all callers
lsp references(file="phase_b.py", line=27, column=5)
```

More reliable than `grep -rn "func_name" | grep -v __pycache__` for Python code.

### Pattern 4: Refactoring Impact Assessment

```
# Step 1: Find all references
lsp references(file="phase_b.py", line=44, column=5)

# Step 2: Verify call context
lsp hover(file="phases/convert.py", line=86, column=22)

# Step 3: Post-edit verification
lsp diagnostics(file="phases/convert.py", severity="error")
```

### Known LSP Behaviors

- **Python relative imports**: `references` from an import line sometimes returns empty results. Work around by starting from the **function definition line** instead.
- **Column precision**: Column must point to the symbol name's start position. Pointing at whitespace or brackets returns empty results. Use `symbols` first to confirm line numbers.
- **Diagnostics noise**: `orchestrator.py`'s `manifest` variable generates "possibly unbound" warnings from pyright's conservative analysis — these are false positives from conditional branch assignments.

## 4. Test Infrastructure

### Node.js Tests

```bash
node --test tests/chrome-agent-runtime.test.mjs
```

- Framework: `node:test` + `node:assert/strict` (no third-party dependencies)
- 9 test cases covering CLI runtime repo resolution
- Must run from repository root (tests use `spawnSync` to invoke scripts)
- Creates temporary mock repos to validate resolution priority:
  1. `CHROME_AGENT_REPO` env var
  2. `repo://` override
  3. Registry fallback

### Python Tests

```bash
python3 scripts/pipeline/tests/test_discovery_summary.py
```

- Framework: `unittest` (no third-party test dependencies)
- 12 test cases for `pipeline/discovery_summary.py` pure functions
- Tests `_build_homepage_categories` and related functions
- Run directly (no `-m` required)

### Explore Module Tests

`scripts/explore/` currently has **no automated tests**. Changes require manual verification using:
```bash
python3 scripts/explore/main.py <repo_root> <url> --samples <json_array>
```

## 5. Common Pitfalls

### Python 3.9 Compatibility

| Issue | Symptom | Fix |
|-------|---------|-----|
| `X \| Y` type annotation | `TypeError` on Python 3.9.6 (macOS) | Use `Optional[X]` or add `from __future__ import annotations` |
| `dict \| None` parameter | Same as above | Use `Optional[dict]` from `typing` |

**Verified mitigations in codebase**:
- `sample_converter.py` line 8: `from typing import Optional` ✓
- `html_to_markdown.py` line 1: `from __future__ import annotations` ✓

### Pipeline Module Naming

| Pitfall | Correct |
|---------|---------|
| Package name has hyphen | Package is `pipeline` (no hyphen) |
| `python3 scripts/pipeline/cli.py` | `python3 -m scripts.pipeline <subcommand>` |
| `__main__.py` workaround | `__main__.py` directly imports `from .cli import main` |

### Engine Version Synchronization

| Issue | Cause | Fix |
|-------|-------|-----|
| `hash_mismatch` after upgrade | Updated binary without updating `configs/engine-versions.json` | Run `md5 -q` + `stat -f '%z'` on new binaries, update manifest |
| `version_mismatch` after pip upgrade | Updated pip package without updating manifest | Update `expected_version` in `configs/engine-versions.json` |
| Repeated re-downloads | Obscura preflight detects hash mismatch | Synchronize both `expected_md5` AND `expected_size` fields |

### Scrapling CLI Path

| Scenario | Behavior |
|----------|----------|
| `SCRAPLING_CLI_PATH` set | Uses that path directly |
| Not set | Falls back to `$HOME/.cache/chrome-agent-scrapling/bin/scrapling` |
| Neither exists | Preflight triggers auto-install |

**Do not** write `SCRAPLING_CLI_PATH` to `/Users/nantas-agent/.zshenv` without user confirmation.

### Strategy Registry

| Scenario | Action Required |
|----------|----------------|
| `bootstrap-strategy` creates strategy | Auto-updates `registry.json` |
| Manual strategy creation | Must manually add entry to `registry.json` |
| Strategy frontmatter vs registry conflict | **Frontmatter is authoritative** |

## 6. Key File Reference

| File | Language | Purpose |
|------|----------|---------|
| `scripts/chrome-agent-cli.mjs` | Node.js ESM | CLI main entry (all commands) |
| `scripts/chrome-agent-runtime.mjs` | Node.js ESM | Global launcher (repo resolution + dispatch) |
| `scripts/lib/extraction/infobox.py` | Python | Unified infobox extraction |
| `scripts/lib/extraction/preprocessor.py` | Python | Config-driven HTML preprocessing |
| `scripts/pipeline/converters/html_to_markdown.py` | Python | MediaWiki HTML → Markdown converter |
| `scripts/explore/main.py` | Python | Deep discovery pipeline entry |
| `scripts/explore/architecture_gate.py` | Python | Strategy↔pipeline alignment validation |
| `scripts/explore/ki_lifecycle.py` | Python | Known Issue classification and tracking |
| `scripts/explore/sample_converter.py` | Python | Strategy-driven sample conversion |
| `configs/engine-registry.json` | JSON | Engine definitions and capabilities |
| `configs/engine-versions.json` | JSON | Version manifest (single source of truth) |
| `sites/strategies/registry.json` | JSON | Strategy file index |
