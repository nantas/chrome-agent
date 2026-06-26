# Writeback

## Change: unify-python-venv-governance

### Writeback Targets

Per `binding.md`, 4 targets require synchronization after implementation.

---

## Target 1: `docs/architecture/06-engine-selection.md`

**Changes needed:**

1. §4 CloakBrowser Preflight section (lines 114-118): Update from read-only preflight to managed venv model
2. §6 Detection Methods table (line 167): Update CloakBrowser row

**Before:**
```
### CloakBrowser Preflight

- **Module check**: Verifies `cloakbrowser` Python module is importable
- **Binary cache**: Chromium binary auto-downloads to `~/.cloakbrowser/chromium-{version}/` on first use
- **Reference**: `scripts/cloakbrowser-preflight.sh`
```

**After:**
```
### CloakBrowser Preflight

- **Managed venv**: CloakBrowser runs in a dedicated Python 3.11 venv at `$HOME/.cache/chrome-agent-cloakbrowser/`
- **Auto-install**: If missing, `scripts/cloakbrowser-cli.sh preflight` provisions the venv via `uv venv --python 3.11` + `uv pip install cloakbrowser`
- **Binary cache**: Chromium binary auto-downloads to `~/.cloakbrowser/chromium-{version}/` on first use (managed by cloakbrowser package, not the venv)
- **Reference**: `scripts/cloakbrowser-cli.sh`
```

**Detection table update:**
```
| CloakBrowser | `pip_module` | `python_importlib` in managed venv | `$HOME/.cache/chrome-agent-cloakbrowser/bin/python` |
```

---

## Target 2: `docs/architecture/08-tech-stack.md`

**Already updated in task 2.25:**
- §2 Explore invocation table: `resolveExplorePython()` → `resolveAppPython()`, prefix updated to `.venv/bin/python`
- §4 Test Infrastructure: all `python3 scripts/test_runner.py` commands → `.venv/bin/python scripts/test_runner.py`

**Additional change needed:**
- §2 Conventions table: Add "Application-layer venv" row

**New row:**
```
| Application-layer venv | Single `.venv/` at repo root governed by `scripts/repo-venv.sh preflight` (lazy-trigger via `resolveAppPython()`); deps declared in root `requirements.txt` (beautifulsoup4, pyyaml, selectolax, markdownify, requests) |
```

Also update Table Caveats §1 "pipeline (none declared)":
```
- **pipeline 依赖声明**: Pipeline 依赖 `selectolax`（用于 HTML 解析）声明在根 `requirements.txt` 中，随 `.venv/` 统一安装。
```

---

## Target 3: `docs/setup/cloakbrowser-setup.md`

**Changes needed:**

1. §安装: `pip install cloakbrowser` → `scripts/cloakbrowser-cli.sh preflight`
2. §验证安装: Update preflight reference + method 2
3. §故障排查: Update install instructions

**Before §安装:**
```bash
pip install cloakbrowser
```

**After §安装:**
```bash
# Auto-provision managed venv (Python 3.11 + cloakbrowser)
bash scripts/cloakbrowser-cli.sh preflight
```

**Before §验证安装:**
```bash
# 方法 1: 使用 preflight 脚本
bash scripts/cloakbrowser-preflight.sh

# 方法 2: 直接检查模块
python3 -c "from cloakbrowser import launch; print('OK')"
```

**After §验证安装:**
```bash
# 方法 1: 使用 managed venv preflight
bash scripts/cloakbrowser-cli.sh preflight

# 方法 2: 直接检查 managed venv 模块
~/.cache/chrome-agent-cloakbrowser/bin/python -c "from cloakbrowser import launch; print('OK')"
```

**Before §故障排查:**
```
| `ModuleNotFoundError: No module named 'cloakbrowser'` | 运行 `pip install cloakbrowser` |
| Binary 未下载 | 手动运行 `python3 -c "from cloakbrowser import launch; b = launch(); b.close()"` 触发下载 |
```

**After §故障排查:**
```
| `ModuleNotFoundError: No module named 'cloakbrowser'` | 运行 `bash scripts/cloakbrowser-cli.sh preflight` |
| Binary 未下载 | 手动运行 `~/.cache/chrome-agent-cloakbrowser/bin/python -c "from cloakbrowser import launch; b = launch(); b.close()"` 触发下载 |
```

---

## Target 4: `configs/engine-versions.json`

**Already updated in tasks 2.17 + 2.21:**
- `detection.method`: `"python_attribute"` → `"python_importlib"`
- `detection.managed_path`: `null` → `"$HOME/.cache/chrome-agent-cloakbrowser/bin/python"`
- `detection.command`: updated to reflect managed venv
- `expected_version`: `"0.3.27"` → `"0.4.3"`
