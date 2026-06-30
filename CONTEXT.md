# CONTEXT.md — chrome-agent 领域语言词汇表

> 定义 chrome-agent 项目的核心术语：Python 环境治理 + 业务架构维度（4 维模型）。`grill-with-docs` / `improve-codebase-architecture` skill 读取此文件对齐语言。

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
共享提取库。`converter.py`（HtmlToMarkdownConverter）是 HTML→Markdown 转换的**共享内核**（intended single implementation），同时被 pipeline 直接 import、被 explore 通过 `sample_converter.py` 间接使用。`preprocessor.py` 同时被 pipeline 和 explore 直接 import。`html_to_markdown.py` 是历史遗留实现，计划消解。
_Avoid_: 在共享层外另建独立的 HTML→Markdown 实现、共享层模块被不同管线取不同入口而实为非共享

## 业务架构维度 (Business Architecture Dimensions)

> chrome-agent 的抓取/转换/提取业务领域是 **4 维正交**的。每个模块同时是这 4 维空间的一个点。
> 架构的所有表达层必须能区分'同一模块'和'镜像/变体模块'。

**架构维度 (Architecture Dimension)**：
模块在 4 轴空间中的一根轴。chrome-agent 有 4 个正交维度。
_Avoid_: 把维度压扁成一个文件、用一个参数运行时切换维度

**能力 (Capability)**：
A 轴——横切关注点：fetch、convert、extract、discover、assemble。当前架构唯一显式建模的维度。
_Avoid_: 所有模块只按能力命名，忽略其他维度

**执行路径 (Execution Path)**：
B 轴——哪个管线在调用：explore（采样审计）、pipeline（批量生产）、site-samples（质量回归）。
同一能力在不同执行路径的实现是 **镜像 (Mirror)**：必须声明等价关系并提供等价证明。
_Avoid_: 不加声明地在不同路径复制同一能力、用 context 参数运行时切换路径

**策略变体 (Strategy Variant)**：
C 轴——站点特定的特化：generic、fandom、wiki.gg 等。变体要么通过 strategy.md frontmatter 配置驱动（推荐），要么显式声明特化文件。
_Avoid_: 变体和内核混淆在同一文件、变体完全复制内核不共享代码

**输入格式 (Input Format)**：
D 轴——rendered HTML、wikitext、API JSON。
_Avoid_: 格式转换与内容提取耦合

**镜像 (Mirror)**：
同一能力在不同执行路径下的等价投影。explore convert 和 pipeline convert 是镜像。必须声明等价关系 + 提供等价证明（测试/golden snapshot）。
_Avoid_: 镜像各自独立实现、无等价声明

**变体 (Variant)**：
站点特定的策略适配层。应复用共享内核，仅在 strategy.md 配置声明差异。
_Avoid_: 不加声明地完全复制实现

**共享内核 (Shared Kernel)**：
所有镜像和变体共用的权威单一实现。一个能力只有一个共享内核。
_Avoid_: 名义共享但各镜像取不同入口（实际非共享）

**维度归属 (Dimensional Coordinates)**：
一个模块在 4 维空间中声明的坐标。新 agent 面对任一模块，应能从结构回答：
① 单一还是镜像/变体 ② 镜像伙伴/变体基类 ③ 等价证明在哪。
_Avoid_: 靠读全量代码推断、靠问作者才知道关系
