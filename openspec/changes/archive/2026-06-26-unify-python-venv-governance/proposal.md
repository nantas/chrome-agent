# Proposal

## 问题定义

chrome-agent 有 3 个 Python 执行上下文（system python3 / scrapling 引擎 venv / repo venv），但 cli.mjs 的 6 个 `spawnSync` 点中 5 个硬编码 `python3`（指向 PEP 668 锁定的 Homebrew Python），导致干净机器上 explore 管线（freeze/iterate）、pipeline、cloakbrowser 五条路径全部不可用。同时依赖声明碎片化：只有 `scripts/explore/requirements.txt` 一份，pipeline 实际依赖 selectolax 却写"(none declared)"，文档撒谎。引擎层 governance 不一致：scrapling 有完整 venv preflight 机制，cloakbrowser 只有只读检测脚本（报错"pip install"后就完事），无安装、无 managed_path。

**根因一句话**：没有"repo 级 Python 应该从哪来"的统一策略。

## 范围边界

**在范围内**：
- 应用层 Python 执行上下文的统一治理（explore + pipeline + shared lib → 单一 `.venv/`，一份根 `requirements.txt`）
- 引擎层 cloakbrowser 治理对齐 scrapling（managed venv + preflight 脚本 + 懒触发安装）
- cli.mjs 全部应用层 spawn 点改用 `resolveAppPython()`（当前已修 1/6，补 5/6）
- doctor 检测路径同步更新（explore_deps 走 resolveAppPython，version_cloakbrowser 走 managed venv）
- test_runner 的 Python 来源从 system python3 改为 `.venv/bin/python`
- 相关文档（08-tech-stack、06-engine-selection、setup）同步修正

**不在范围内**：
- scrapling / obscura 引擎的现有 governance（不变，cloakbrowser 仅仿 scrapling 模式）
- cloakbrowser 的 Chromium 二进制缓存管理（留在 `~/.cloakbrowser/`，属于上游包职责）
- `mediawiki-api` 引擎（它是 API 引擎无 Python 依赖）
- pip 包版本升级策略（沿用 C4 约束，`configs/engine-versions.json` 同步）
- C10 全局同步（改 cli.mjs 后手动同步，不在本次 change 自动化）

## Capabilities

### New Capabilities

- `app-layer-venv-governance`: 仓库级应用层 Python venv 治理。单一根 `requirements.txt`（bs4 / selectolax / pyyaml / markdownify）为应用层依赖 SSOT；`resolveAppPython()` 函数（`scripts/lib/python-resolver.mjs`）统一解析 Python 解释器（优先级 `CHROME_AGENT_PYTHON` env > `.venv/bin/python` > `python3` fallback）；懒触发 `repo-venv.sh preflight` 自动创建 venv 并装依赖

### Modified Capabilities

- `cli`: 全部应用层 `spawnSync` 点（explore freeze.py / iterate.py / pipeline `-m scripts.pipeline`）从硬编码 `"python3"` 迁移为 `resolveAppPython(repoRoot)`；cloakbrowser_fetcher spawn 改用 `cloakbrowser-cli.sh` 解析出的 managed venv python
- `engine-registry`: cloakbrowser-fetch 引擎新增 managed venv 治理（`managed_path: $HOME/.cache/chrome-agent-cloakbrowser/`，`cloakbrowser-cli.sh preflight` 仿 scrapling-cli.sh 模式），检测方法 `python_attribute` → `python_importlib`（在 managed venv 内执行）
- `doctor-repo-freshness`: `explore_deps` 检查改用 `resolveAppPython(repoRoot)` 解析的 Python（不再是裸 `python3`）；`version_cloakbrowser` 检测改用 cloakbrowser managed venv python（不再是裸 `python3`）

## Capabilities 待确认项

- [x] 能力清单已确认（与 grill 决策树一致，见 ADR-0002 / ADR-0003）

## Impact

| 维度 | 影响 |
|------|------|
| **开发者体验** | `git clone` 后直接 `chrome-agent explore <url>` 零配置可用（懒触发自动建 .venv / cloakbrowser venv）；不再需要 `pip install --break-system-packages` |
| **test_runner** | 命令从 `python3 scripts/test_runner.py all` 改为 `.venv/bin/python scripts/test_runner.py all`——测试 Python = 运行时 Python，消除 selectolax 缺失的 2 个既有 error |
| **doctor 语义** | `explore_deps` 从"检查 system python3 有无 bs4"变为"检查应用层 venv（懒触发创建后）是否 bs4/yaml 可用"；`version_cloakbrowser` 从 `not installed` 变为 managed venv 内检测（懒触发安装后转绿） |
| **文档** | 消除 08-tech-stack.md §1 pipeline "(none declared)" 谎言；06-engine-selection.md CloakBrowser preflight 节更新 |
| **文件变更** | 新增 4 文件（`requirements.txt`, `scripts/repo-venv.sh`, `scripts/cloakbrowser-cli.sh`, `tests/python-resolver.test.mjs` 重命名），修改 6 文件（cli.mjs, engine-version-check.sh, engine-versions.json, python-resolver.mjs, 两个架构文档），删除 2 文件（`scripts/explore/requirements.txt`, `scripts/cloakbrowser-preflight.sh`） |
| **破坏性** | 无——向后兼容：无 `.venv` 时 `resolveAppPython()` fallback 到 `python3` |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：`openspec/specs/engine-registry/`, `openspec/specs/scrapling-cli-environment/`, `openspec/specs/doctor-repo-freshness/`
  - 项目页：`docs/architecture/06-engine-selection.md`, `docs/architecture/08-tech-stack.md`, `docs/adr/0002-`, `docs/adr/0003-`
  - 回写目标：同上 2 个架构文档 + `docs/setup/cloakbrowser-setup.md` + `configs/engine-versions.json`
