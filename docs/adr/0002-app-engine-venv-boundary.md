# 0002 — Application Layer / Engine Layer venv 边界

## 状态

已接受

## 背景

chrome-agent 的 Python 代码覆盖两类职责（repo 级解析/转换 vs 引擎级抓取），两者依赖形态不同（纯 Python lib vs 带 ~200MB patched binary），且现有 cli.mjs 的 6 个 `spawnSync` 点全部硬编码 `python3`（指向 PEP 668 锁定的系统 Python），导致干净环境上 5/6 条路径不可用。需要一刀切出清晰边界，让每类能力都知道自己的 Python 从哪来。

抉择：一个 venv 统管全部 vs 应用层-引擎层分层隔离 vs 每个能力独立 venv。

## 决策

**应用层（explore / pipeline / shared lib/extraction）统一用仓库 `.venv/`**，装 bs4、selectolax、pyyaml、markdownify 四个纯 Python lib，通过 `resolveAppPython()` 解析。

**引擎层（scrapling / cloakbrowser）各自保持独立 venv**，托管在 `~/.cache/chrome-agent-<engine>/`，维持各自 preflight 脚本管理生命周期。

边界不可交叉：不在 `.venv` 里装引擎包，不在引擎 venv 里跑应用层代码。

## 后果

- **正**：应用层 4 个 spawn（explore main/freeze/iterate + pipeline）共享同一 .venv，消除依赖重复与归属混乱；引擎层继承 scrapling 已验证的 preflight 懒触发模式；`docs/architecture/06-engine-selection.md` 的引擎 fallback chain 语义不变
- **负**：新增了一个"边界"概念（应用层 vs 引擎层）需要文档化（CONTEXT.md）；pipeline 的"零声明依赖"谎言被显式打破（08-tech-stack.md 需同步更新）；.venv/ 需要 gitignore
