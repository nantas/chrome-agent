# Design

## Context

chrome-agent 的 Python 执行环境混乱的根因已在 proposal 中定义，治理决策由 grill 逐项确认并沉淀为 ADR-0002（应用层/引擎层 venv 边界）和 ADR-0003（懒触发生命周期）。本 design 说明如何实现已在 specs 中确认的 4 个 capability 的行为规格。

## Goals / Non-Goals

**Goals:**

- 应用层 4 个 spawn 点 + cloakbrowser 1 个 spawn 点统一 Python 解析策略（不再硬编码 `python3`）
- 应用层依赖声明收敛到单一根 `requirements.txt`
- cloakbrowser 引擎获得与 scrapling 同等的 managed venv 治理
- doctor 的 explore_deps / version_cloakbrowser 检测路径与新解析策略对齐
- test_runner 默认用 `.venv/bin/python`

**Non-Goals:**

- 不改变 scrapling / obscura 现有 preflight 机制
- 不改变 engine-registry.json 的引擎能力定义字段（仅更新 engine-versions.json 的 managed_path）
- 不接管 cloakbrowser Chromium 二进制管理
- 不自动化 C10 全局同步（手动同步保持）

## Decisions

### D1: `resolveAppPython` 为应用层唯一解析入口

所有应用层 spawn（explore main/freeze/iterate, pipeline `-m scripts.pipeline`）和 doctor explore_deps 都通过 `resolveAppPython(repoRoot)` 解析 Python，不再各自判断。实现位置：`scripts/lib/python-resolver.mjs`（已在上一 round 创建，本 change 重命名 `resolveExplorePython` → `resolveAppPython` 并扩展覆盖范围）。

### D2: 懒触发 preflight 脚本分层

两个新 preflight 脚本，全部仿 `scrapling-cli.sh` 模式（`preflight` / `STATUS=` / `SOURCE=` / `RESOLVED_CLI_PATH=` 输出格式）：

| 脚本 | 管理路径 | 安装命令 | 依赖清单 | 谁调用 |
|------|---------|---------|---------|--------|
| `scripts/repo-venv.sh` | `.venv/` | `uv venv` + `uv pip install -r requirements.txt` | `requirements.txt`（根） | `resolveAppPython()` 探测阶段 |
| `scripts/cloakbrowser-cli.sh` | `$HOME/.cache/chrome-agent-cloakbrowser/` | `uv venv --python 3.11` + `uv pip install cloakbrowser` | `cloakbrowser`（pypi） | cli.mjs `runCloakbrowserFetch` + doctor version_check |

### D3: `requirements.txt` 放在仓库根

单一 `requirements.txt` 声明应用层全量依赖（bs4 / selectolax / pyyaml / markdownify），替换 `scripts/explore/requirements.txt`。version 策略：`>=` 下限（与旧文件一致），不锁死 `==`。

### D4: 重命名传播范围

`resolveExplorePython` → `resolveAppPython` 的重命名仅影响 3 个文件：
- `scripts/lib/python-resolver.mjs`（定义）
- `scripts/chrome-agent-cli.mjs`（2 处 import 引用）
- `tests/python-resolver.test.mjs`（测试）

### D5: test_runner 不修改脚本本身

test_runner.py 的 `#!/usr/bin/env python3` shebang 不变。治理体现在调用指令更新（08-tech-stack.md §4 文档示例改为 `.venv/bin/python scripts/test_runner.py all`），这样开发者显式选择用哪个 python 跑测试。

## Risks / Migration

| 风险 | 缓解 |
|------|------|
| 首次懒触发安装卡顿（几秒 uv venv + pip install） | preflight 输出进度日志到 stderr（仿 scrapling-cli.sh 的 `log()` 函数），用户可见进度 |
| 没有 `uv` 的环境无法自动建 venv | repo-venv.sh 和 cloakbrowser-cli.sh 在 preflight 开头检查 `uv` 可用性，缺了给出安装指令（`curl -LsSf https://astral.sh/uv/install.sh \| sh`）并 exit 非零 |
| `python-resolver.test.mjs` 重命名后需要 git mv 保持历史 | 本 change 不做 git mv（`scripts/lib/python-resolver.mjs` 是上一 round 新增的 untracked 文件，无 git history），直接 rename + 修改内容 |
| 删 `scripts/explore/requirements.txt` 后，如有外部引用可能断链 | 确认该文件仅被 `pip install -r` 引用（之前 system python3 路径），无外部依赖；删除后在 .venv 不再需要的场景下由 repo-venv.sh preflight 接管 |
| `cloakbrowser-cli.sh preflight` 首次安装下载 ~200MB Chromium | 使用 `uv pip install cloakbrowser` 仅装 Python 包（~几 MB）；Chromium 二进制在首次 `launch()` 时由 cloakbrowser 包自己异步下载到 `~/.cloakbrowser/`，不阻塞 preflight |
