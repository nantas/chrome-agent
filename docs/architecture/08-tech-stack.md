# 08 — Tech Stack & Development Guide

> **Source**: AGENTS.md §6 development content
>
> **Applicable to**: Contributors modifying `scripts/`, `configs/`, or `sites/`

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    chrome-agent Component Dependencies              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────┐                                          │
│  │  Node.js CLI Layer   │  scripts/chrome-agent-cli.mjs            │
│  │  (command dispatch)  │  scripts/chrome-agent-runtime.mjs        │
│  └──────────┬───────────┘                                          │
│             │ spawn / exec                                          │
│             │                                                       │
│  ┌──────────▼───────────────────────────────────┐                   │
│  │         Python Execution Layer                │                   │
│  │                                               │                   │
│  │  ┌──────────────────┐  ┌────────────────────┐│                   │
│  │  │  Pipeline        │  │  Explore           ││                   │
│  │  │  scripts/pipeline│  │  scripts/explore   ││                   │
│  │  │  (MediaWiki API) │  │  (deep discovery)  ││                   │
│  │  └────────┬─────────┘  └──────────┬─────────┘│                   │
│  │           │                       │          │                   │
│  │           └───────────┬───────────┘          │                   │
│  │                       │                      │                   │
│  │           ┌───────────▼───────────┐          │                   │
│  │           │  Shared lib/          │          │                   │
│  │           │  scripts/lib/         │          │                   │
│  │           │  - extraction/        │          │                   │
│  │           │  - config_resolver.py │          │                   │
│  │           │  - strategy_loader.py │          │                   │
│  │           └───────────┬───────────┘          │                   │
│  └───────────────────────┼──────────────────────┘                   │
│                          │                                          │
│  ┌───────────────────────▼──────────────────────┐                   │
│  │           Engine Layer                        │                   │
│  │                                               │                   │
│  │  ┌──────────────┐ ┌──────────┐ ┌───────────┐│                   │
│  │  │  Scrapling   │ │  Obscura │ │ CloakBrowser│                   │
│  │  │  (Python venv│ │  (binary)│ │ (pip pkg)  │                   │
│  │  │   stealthy)  │ │          │ │            │                   │
│  │  └──────────────┘ └──────────┘ └───────────┘│                   │
│  └──────────────────────────────────────────────┘                   │
│             │                                                       │
│             ▼                                                       │
│  ┌──────────────────────┐                                          │
│  │  Output Layer        │  outputs/<domain>/<category>/*.md        │
│  │  + .cache/           │  configs/engine-versions.json (manifest) │
│  │  + reports/          │  sites/strategies/registry.json          │
│  └──────────────────────┘                                          │
└─────────────────────────────────────────────────────────────────────┘

箭头方向 = 依赖方向（上层调用下层）
无循环依赖
```
<!-- Source: scripts/ directory structure, package.json, configs/engine-versions.json -->

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

### 安装脚本链流程图

```
install-chrome-agent-cli.sh
    │
    ├── 注册 chrome-agent CLI 命令
    │   管理路径: /usr/local/bin/chrome-agent (symlink)
    │
    └── 调度各 engine preflight 脚本
        │
        ├── 1. scrapling-cli.sh preflight
        │       │   创建 Scrapling Python venv
        │       │   安装 scrapling + 依赖
        │       │   管理路径: $HOME/.cache/chrome-agent-scrapling/
        │       └── ✓ Scrapling 就绪
        │
        ├── 2. obscura-cli-preflight.sh
        │       │   下载 Obscura 二进制 (GitHub Release)
        │       │   校验 MD5 + 文件大小
        │       │   管理路径: $HOME/.cache/chrome-agent-obscura/bin/
        │       └── ✓ Obscura 就绪
        │
        ├── 3. cloakbrowser-preflight.sh
        │       │   pip install CloakBrowser
        │       │   管理路径: ~/.cloakbrowser/chromium-{ver}/
        │       └── ✓ CloakBrowser 就绪
        │
        └── 4. engine-version-check.sh --json
                │   验证所有引擎版本与 configs/engine-versions.json 一致
                │   校验: expected_version + expected_md5 + expected_size
                └── ✓ 环境诊断通过
```
<!-- Source: scripts/*.sh, scripts/engine-version-check.sh -->

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

### 目录结构

```
tests/
├── __init__.py
├── lib/                      ← scripts/lib/ 模块测试
│   ├── __init__.py
│   ├── test_html_to_markdown.py
│   ├── test_markdown_link_resolver.py
│   └── test_cdp_image_downloader.py
└── pipeline/                 ← scripts/pipeline/pipeline/ 模块测试
    ├── __init__.py
    ├── test_fetch_cdp.py
    └── test_convert_html.py

sites/strategies/<domain>/
├── strategy.md               ← frontmatter 含 samples 字段
└── samples/                  ← golden files（跟策略走）
    └── <page>.md
```

### 统一测试入口

```bash
# 运行所有测试（单元 + 站点样本回归）
python3 scripts/test_runner.py all

# 仅单元测试（stdlib discover）
python3 scripts/test_runner.py unit
# 或直接:
python3 -m unittest discover -s tests -v

# 站点样本回归
python3 scripts/test_runner.py site-samples
python3 scripts/test_runner.py site-samples --domain developer.nintendo.com
python3 scripts/test_runner.py site-samples --update-golden
```

### 框架约定

| 语言 | 框架 | 禁止 |
|------|------|------|
| Python | `unittest` | `pytest`、第三方测试库 |
| Node.js | `node:test` | Jest、Mocha |

### 站点样本回归机制

1. **样本声明**：`strategy.md` frontmatter `samples` 字段列出测试页面（`page` + `label`）
2. **数据来源**：从 `.cache/<platform>/<domain>/` 读取缓存的 HTML
3. **转换**：调用 `html_to_markdown()` 转换 → 与 golden file 对比
4. **I2 动态 TestCase**：为每个 `(domain, page)` 独立生成 `unittest.TestCase`，每个样本独立 pass/fail
5. **结构断言**：转换输出先经过三内置断言（`no_raw_html_tags`、`links_resolved`、`valid_md_tables`），再与 golden diff
6. **Golden 更新**：`--update-golden` 覆写 golden file（有意输出变更时使用）

### 结构断言规则集

| 断言 | 检测内容 |
|------|----------|
| `assert_no_raw_html_tags` | 残留 HTML 标签（`<div>`、`<span>` 等） |
| `assert_links_resolved` | 未解析的 `../Pages/Page_*.html` 链接 |
| `assert_valid_md_tables` | Markdown 表格列数不一致 |

### Node.js Tests

```bash
node --test tests/chrome-agent-runtime.test.mjs
```

- Framework: `node:test` + `node:assert/strict` (no third-party dependencies)
- Must run from repository root

### 旧测试保留

`scripts/pipeline/tests/` 下的旧测试保留原位（不迁移到 `tests/`），已全部迁移到 `unittest.TestCase`。新测试统一放 `tests/`。

### TDD 约定

> 本节描述 chrome-agent 项目的测试驱动开发方法论。核心原则转写自 TDD skill。

**Vertical Slice 原则**：一个测试 → 一个实现 → 通过，重复。不要写完全部测试再写全部实现（horizontal slicing），这会产生测试想象中行为而非实际行为的劣质测试。

**禁止 Horizontal Slicing**：不要把 RED 阶段理解为"写完所有测试"，GREEN 阶段理解为"写完所有代码"。正确做法是每次只写一个测试，立即实现使其通过。

**行为优先于实现**：测试验证公共接口的行为，不验证内部实现细节。好的测试在重构后仍然通过，因为行为没有改变。

**重构只在 GREEN 之后**：所有测试通过后才重构。重构时持续运行测试确认行为不变。不要在 RED 状态下重构。

```text
正确（vertical）：
  RED→GREEN: test1 → impl1
  RED→GREEN: test2 → impl2
  RED→GREEN: test3 → impl3

错误（horizontal）：
  RED:   test1, test2, test3
  GREEN: impl1, impl2, impl3
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
| `scripts/lib/extraction/converter.py` | Python | MediaWiki HTML → Markdown converter |
| `scripts/explore/main.py` | Python | Deep discovery pipeline entry |
| `scripts/explore/architecture_gate.py` | Python | Strategy↔pipeline alignment validation |
| `scripts/explore/ki_lifecycle.py` | Python | Known Issue classification and tracking |
| `scripts/explore/sample_converter.py` | Python | Strategy-driven sample conversion |
| `configs/engine-registry.json` | JSON | Engine definitions and capabilities |
| `configs/engine-versions.json` | JSON | Version manifest (single source of truth) |
| `sites/strategies/registry.json` | JSON | Strategy file index |

## 关联文档

- [01 — 系统总览](01-overview.md) — 多后端架构全景
- [05 — 转换器架构](05-converter-architecture.md) — lib/extraction/ 统一提取引擎
- [06 — 引擎选择](06-engine-selection.md) — Scrapling/Obscura/CloakBrowser 引擎详情
