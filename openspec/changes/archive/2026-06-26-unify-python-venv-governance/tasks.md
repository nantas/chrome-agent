# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 4 个 capability spec（app-layer-venv-governance, cli, engine-registry, doctor-repo-freshness）的实现范围与边界
- [x] 1.2 确认前置条件：机器有 `uv`（`which uv`），无则安装

## 2. 核心实现任务 (Vertical Slices)

### A. 应用层 resolver 重命名 (app-layer-venv-governance + cli)

- [x] 2.1 **RED**: 将 `tests/python-resolver.test.mjs` 中的测试名和 import 从 `resolveExplorePython` 改为 `resolveAppPython`，新增 test case 验证 `resolveAppPython` 与 `resolveExplorePython` 行为一致（回归守卫）
- [x] 2.2 **GREEN**: `scripts/lib/python-resolver.mjs` 中 `resolveExplorePython` → `resolveAppPython` 重命名，同步更新 cli.mjs 中 2 处 import 引用（:12, :1683, :1733）
- [x] 2.3 **GREEN (验证)**: `node --test tests/python-resolver.test.mjs` → 3+1=4 pass

### B. 应用层依赖清单集中化 (app-layer-venv-governance)

- [x] 2.4 **GREEN**: 仓库根创建 `requirements.txt`，内容 `beautifulsoup4>=4.12`, `pyyaml>=6.0`, `selectolax>=0.3`, `markdownify`（合并自 `scripts/explore/requirements.txt` + pipeline 实际依赖 + shared lib 实际依赖）
- [x] 2.5 **GREEN**: 删除 `scripts/explore/requirements.txt`
- [x] 2.6 **RED**: 在 `tests/python-resolver.test.mjs` 新增 test case：`resolveAppPython` 不显式调用但验证 requirements.txt 存在且包含 4 个包
- [x] 2.7 **GREEN (验证)**: `.venv/bin/pip install -r requirements.txt` 确认已装依赖无误（当前 .venv 已有 bs4/pyyaml/selectolax，需补 markdownify）

### C. repo-venv.sh preflight 脚本 (app-layer-venv-governance)

- [x] 2.8 **GREEN**: 创建 `scripts/repo-venv.sh`（仿 `scrapling-cli.sh` 模式：`preflight` 命令，检查 `.venv/bin/python` 可 import 全量 deps，缺了自动 `uv venv` + `uv pip install -r requirements.txt`，输出 `STATUS=`/`SOURCE=` 格式）
- [x] 2.9 **RED**: 在 `tests/python-resolver.test.mjs` 新增 test case（或独立 `tests/repo-venv.test.mjs`）：spawn `scripts/repo-venv.sh preflight --no-install` 验证探测逻辑
- [x] 2.10 **GREEN (验证)**: 删除 `.venv` 后运行 `scripts/repo-venv.sh preflight` → 自动重建 + deps 可 import

### D. 应用层 spawn 点补漏 (cli)

- [x] 2.11 **GREEN**: cli.mjs `freeze.py` spawn (line 3279→3280) 从 `spawnSync("python3", ...)` 改为 `spawnSync(resolveAppPython(repoRoot), ...)`
- [x] 2.12 **GREEN**: cli.mjs `iterate.py` spawn (line 3343→3344) 从 `spawnSync("python3", ...)` 改为 `spawnSync(resolveAppPython(repoRoot), ...)`
- [x] 2.13 **GREEN**: cli.mjs pipeline spawn (line 2266) 从 `spawnSync("python3", apiArgs, ...)` 改为 `spawnSync(resolveAppPython(repoRoot), apiArgs, ...)`
- [x] 2.14 **GREEN (验证)**: `node --check scripts/chrome-agent-cli.mjs` + doctor explore_deps 仍绿

### E. cloakbrowser-cli.sh managed venv (engine-registry)

- [x] 2.15 **GREEN**: 创建 `scripts/cloakbrowser-cli.sh`（仿 `scrapling-cli.sh` 完整模式：`preflight` 命令，managed_path=`$HOME/.cache/chrome-agent-cloakbrowser/`，`uv venv --python 3.11` + `uv pip install cloakbrowser`）
- [x] 2.16 **GREEN**: 更新 `scripts/engine-version-check.sh` `detect_cloakbrowser` 函数：改用 `$HOME/.cache/chrome-agent-cloakbrowser/bin/python` 替代裸 `python3`
- [x] 2.17 **GREEN**: 更新 `configs/engine-versions.json` cloakbrowser 条目：`detection.method` → `"python_importlib"`，`detection.managed_path` → `"$HOME/.cache/chrome-agent-cloakbrowser/bin/python"`
- [x] 2.18 **GREEN**: 删除 `scripts/cloakbrowser-preflight.sh`（功能被 cloakbrowser-cli.sh 取代）
- [x] 2.19 **GREEN**: cli.mjs `runCloakbrowserFetch` (line 780→794) spawn 改用 `cloakbrowser-cli.sh` 解析出的 managed python（RESOLVED_CLI_PATH 行输出）
- [x] 2.20 **RED**: 新增 `tests/cloakbrowser-cli.test.mjs`：spawn `scripts/cloakbrowser-cli.sh preflight --no-install` 验证探测逻辑（探测缺了不装，只输出状态）
- [x] 2.21 **GREEN (验证)**: `scripts/cloakbrowser-cli.sh preflight`（无 `--no-install`）→ 自动建 managed venv + `python -c "import cloakbrowser; print(cloakbrowser.__version__)"` 成功

### F. doctor 检测路径对齐 (doctor-repo-freshness)

- [x] 2.22 **GREEN**: 医生 `explore_deps` 检查已使用 `resolveAppPython(repoRoot)`（已在 task 2.2 完成，此处为确认）
- [x] 2.23 **GREEN**: 医生命令中 `engine-version-check.sh` 的 cloakbrowser 检测使用 managed venv python（已在 task 2.16 完成，此处为确认）
- [x] 2.24 **GREEN (验证)**: `chrome-agent doctor --format json` → `explore_deps: bs4, yaml available` 绿 + `version_cloakbrowser` 不再是 `not installed`

### G. test_runner Python 来源 (app-layer-venv-governance)

- [x] 2.25 **GREEN**: 更新 `docs/architecture/08-tech-stack.md` §4 Test Infrastructure 命令示例：`python3 scripts/test_runner.py all` → `.venv/bin/python scripts/test_runner.py all`
- [x] 2.26 **GREEN (验证)**: `.venv/bin/python -m unittest discover -s tests -v` → 无 `ModuleNotFoundError: selectolax`（之前 2 个 error 消失）

## 3. 收敛与验证准备

- [x] 3.1 全量 Node.js 测试：`node --test tests/*.test.mjs` → 72 pass, 0 fail
- [x] 3.2 全量 Python 测试：`.venv/bin/python -m unittest discover -s tests -v` → 74 pass, 0 error
- [x] 3.3 doctor 全绿：`chrome-agent doctor --format json` → 12/12 ok （含 version_cloakbrowser: 0.4.3）
- [x] 3.4 整理 verification.md 需要收集的证据清单

## 4. 验证与回写收敛

- [x] 4.1 基于实施结果生成 `verification.md`（证据：测试输出、doctor JSON、git diff --stat）
- [x] 4.2 基于 verification.md 生成 `writeback.md`（回写目标：`docs/architecture/06-engine-selection.md`、`docs/architecture/08-tech-stack.md`、`docs/setup/cloakbrowser-setup.md`、`configs/engine-versions.json`）
- [x] 4.3 执行回写 + C10 全局同步（cli.mjs 变更后手动 `cp scripts/chrome-agent-runtime.mjs ~/.agents/scripts/chrome-agent.mjs` + `git rev-parse HEAD > ~/.agents/scripts/.chrome-agent-installed-hash` + reload skill）
