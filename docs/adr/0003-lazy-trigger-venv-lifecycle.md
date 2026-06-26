# 0003 — 懒触发 venv 生命周期

## 状态

已接受

## 背景

chrome-agent 的三类 Python 执行上下文（应用层 .venv、scrapling 引擎 venv、cloakbrowser 引擎 venv）需要统一的生命周期模型。scrapling 已有验证的懒触发 preflight 模式（`scrapling-cli.sh preflight`：检测→缺了自动装→装完可用），cloakbrowser 和 repo venv 是否照搬？

抉择：全部照搬懒触发 vs 引擎懒触发 + repo venv 显式 setup vs 全部显式手动。

## 决策

**全部采用懒触发 preflight 模式**。统一语义：cli.mjs 的每个能力 spawn 前（或 doctor 检测时）调用对应的 preflight 脚本/函数，检测 Python 执行上下文是否可用，不可用则自动 `uv venv` + `uv pip install`，装完返回可用。

- 应用层：`resolveAppPython()` 检测 `.venv/bin/python` 存在且能 `import bs4, yaml`，否则调 `scripts/repo-venv.sh preflight` 自动建
- scrapling：保持现有 `scrapling-cli.sh preflight` 不变
- cloakbrowser：仿 scrapling 新建 `scripts/cloakbrowser-cli.sh preflight`（用 `uv` + `--python 3.11`）

三个入口，同一心智模型：**首次 run 即装，后续 run 复用**。

## 后果

- **正**：开发者心智模型统一（"跑就行了"）；`git clone` 后直接 `chrome-agent explore <url>` 零配置就绪；与 engine-registry 已有的 preflight 检测一致性（doctor 的 explore_deps 检查和实际 spawn 走同一逻辑，检测=执行）
- **负**：首次能力调用会卡几秒装包（preflight 打印进度到 stderr，可缓解）；不能像 `pip install --break-system-packages` 那样"一次污染系统 Python 然后忘记"（好的负后果——故意的）
