# CONTEXT.md — chrome-agent 领域语言词汇表

> 定义 chrome-agent 项目 Python 环境治理的核心术语。`grill-with-docs` / `improve-codebase-architecture` skill 读取此文件对齐语言。

## 执行上下文

**Application Layer (应用层)**：
repo 级 Python 代码（explore / pipeline / shared lib/extraction）运行所需的 Python 解释器和依赖集合。托管在仓库 `.venv/` 中，由 `resolveAppPython()` 解析，懒触发创建。
_Avoid_: 系统 Python、全局依赖、--break-system-packages

**Engine Layer (引擎层)**：
抓取引擎（scrapling / cloakbrowser）各自独立的 Python 执行上下文，托管在 `~/.cache/chrome-agent-<engine>/` 中，由各自 preflight 脚本管理生命周期。
_Avoid_: 引擎混装、repo venv 塞引擎包

**Managed Path (托管路径)**：
引擎 venv 在 `~/.cache/` 下的标准位置，格式 `~/.cache/chrome-agent-<engine>/`。每个引擎一个路径，不重叠。
_Avoid_: 手动路径、引擎 venv 放 repo 里

**Preflight (预检)**：
引擎或应用层 venv 的探测+自动安装流程。模式：检查是否可用 → 不可用则自动装 → 装完可用。统一输出 STATUS/SOURCE/RESOLVED_CLI_PATH 行，doctor + 各能力 spawn 前都调用。
_Avoid_: 手动 pip install、setup 脚本、环境配置文档

## 动作 / 操作

**resolveAppPython(repoRoot)**：
解析应用层能力的 Python 解释器。优先级：`CHROME_AGENT_PYTHON` env > `.venv/bin/python` > 系统 `python3`（fallback）。定义在 `scripts/lib/python-resolver.mjs`，被 doctor `explore_deps` 检查 + cli.mjs 的 4 个应用层 spawn（explore main/freeze/iterate + pipeline）共用。
_Avoid_: 硬编码 "python3"、每个 spawn 各自判断

**Lazy Trigger (懒触发)**：
venv 不预建，在第一次被需要时自动创建的模式。首次 `doctor` 或首次能力 spawn 触发 `scripts/repo-venv.sh preflight`（或引擎 preflight），自动完成 `uv venv` + `uv pip install`，后续调用直接复用。
_Avoid_: 显式 setup 脚本、README 里写"先跑 xxx 再跑 yyy"

**Version Check (版本校验)**：
`scripts/engine-version-check.sh` 对每个引擎执行版本检测。应用层不参与 version check（应用层通过 `resolveAppPython()` + doctor `explore_deps` 的 `import bs4, yaml` 间接校验）。

## 边界

**Application Layer ↔ Engine Layer boundary**：
应用层（`.venv/`）装纯 Python lib：bs4、selectolax、pyyaml、markdownify。引擎层（`~/.cache/`）装带二进制的抓取器：scrapling、cloakbrowser。**永不交叉**：不在 `.venv` 里装引擎，不在引擎 venv 里跑应用层代码。
_Avoid_: 一个 venv 全管、引擎脚本用 system python3

**shared lib/extraction/**：
`lib/extraction/converter.py`（依赖 selectolax）同时被 pipeline 和 explore import，是共享层。**共享层依赖进应用层 venv**（根 `requirements.txt` 包含 selectolax），因为 explore 和 pipeline 都属应用层。
_Avoid_: 按"explore 需要"或"pipeline 需要"切分共享层依赖
