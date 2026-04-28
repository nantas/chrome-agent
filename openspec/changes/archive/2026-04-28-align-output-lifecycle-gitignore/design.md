# Design

## Context

`output-lifecycle` 规范将 artifacts 分为 durable(`reports/`) 与 disposable(`outputs/`)；但仓库 `.gitignore` 当前忽略 `reports/` 且未忽略 `outputs/`，导致治理语义与仓库行为冲突。

## Goals / Non-Goals

**Goals:**
- 让仓库 git 跟踪默认行为与 lifecycle 分类一致。
- 在 output lifecycle 规范中显式固化 git ignore 对齐要求。
- 增加 durable report 产出门控，避免常规简单抓取默认写入 `reports/`。
- 以最小变更完成修复，不引入额外运行时行为。

**Non-Goals:**
- 不在本 change 中实现或扩展 `chrome-agent clean` 的删除策略。
- 不引入报告保留周期（retention）或归档自动化。
- 不修改站点策略与引擎选择逻辑。

## Decisions

- 将 `.gitignore` 从忽略 `reports/` 调整为忽略 `outputs/`。
- 在 `openspec/specs/output-lifecycle/spec.md` 中新增 requirement，明确 git 跟踪默认策略：
  - `outputs/` 是 disposable，默认忽略。
  - `reports/` 是 durable，默认不全局忽略。
- 在 change delta 中拆分：
  - `output-lifecycle-git-governance` 负责新增 git lifecycle 边界。
  - `output-lifecycle` 负责更新既有 artifact class requirement 的完整语义。
  - `report-emission-gating` 负责定义报告产出条件与默认行为。
- 报告产出策略采用工作流+显式参数双门控：
  - `explore` 默认产出 durable report。
  - `fetch`/`crawl` 等简单任务默认不产出 durable report。
  - 显式 `report` 参数可在任意工作流开启 durable report 产出。

## Risks / Migration

- 风险：移除 `reports/` ignore 后，历史本地报告文件会在 `git status` 中出现，可能带来一次性待筛选项。
- 风险：默认关闭简单任务报告后，部分用户可能依赖历史“每次都出报告”的行为。
- 迁移：仓库维护者需按需挑选可提交报告；如需排除个别大型临时报告，使用更细粒度 ignore（文件级）而不是目录级全局屏蔽。
- 迁移：需要在 CLI 帮助与工作流文档中明确 `--report`（或等价参数）用于非 explore 场景的显式报告产出。
