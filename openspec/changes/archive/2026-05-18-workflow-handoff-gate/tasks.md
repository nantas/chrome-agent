# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `specs/handoff-emission/spec.md` 的实现范围：`generateHandoff()` 函数、内部/外部失败区分、handoff 文档格式、存储路径、result 字段
- [x] 1.2 确认 `specs/handoff-gate/spec.md` 的实现范围：SKILL.md 中 Handoff Gate 章节的定义、halting 协议、禁止绕过规则、用户消息格式
- [x] 1.3 确认 `specs/global-workflow-skill/spec.md` 的修改范围：Result Packaging 增加 handoff_path/handoff_summary 字段处理、Handoff Gate 与现有结果封装的交互
- [x] 1.4 阅读 `scripts/chrome-agent-cli.mjs` 中失败返回路径的现有代码结构（runFetch / runCrawl / runExplore / runScrape 的 failure 分支）

## 2. 核心实现任务

### 2.1 CLI: `generateHandoff()` 函数

- [x] 2.1.1 在 `scripts/chrome-agent-cli.mjs` 中新增 `generateHandoff(context)` 函数，接受参数：command, target, repoRef, runDir (可选), error (exit code + stderr), strategy (可选)
- [x] 2.1.2 函数创建 `outputs/handoffs/<run-tag>/` 目录并写入 `handoff.md`
- [x] 2.1.3 函数按 spec 要求的格式生成 handoff 内容（Context / What Went Wrong / Error Details / Run Artifacts / Next Steps）
- [x] 2.1.4 函数返回 `{ path: string, summary: string }`（handoff.md 绝对路径 + 一行摘要）
- [x] 2.1.5 run-tag 复用 `buildRunPaths()` 的时间戳-slug 规则（`<timestamp>-<command>-<slug>`）

### 2.2 CLI: 内部/外部失败区分函数

- [x] 2.2.1 在 `scripts/chrome-agent-cli.mjs` 中新增 `isInternalFailure(command, error)` 辅助函数
- [x] 2.2.2 内部失败判定逻辑：
  - Pipeline exit code >= 10 → internal
  - Strategy 缺失且 deep discovery 失败（scaffold 未生成）→ internal
  - Engine preflight 安装尝试后仍失败 → internal
  - Sample conversion / self-check 不可恢复失败 → internal
- [x] 2.2.3 外部失败判定逻辑（不触发 handoff）：
  - 目标网站 HTTP 4xx/5xx
  - 无效 URL 格式
  - CHROME_AGENT_REPO 未设置或无效
  - 网络超时 / DNS 解析失败

### 2.3 CLI: `runFetch()` 失败路径集成

- [x] 2.3.1 在 `runFetch()` 的 fetchResult.ok === false 分支中，在返回 failure result 之前调用 `isInternalFailure()`
- [x] 2.3.2 若为 internal，调用 `generateHandoff()` 并将结果中的 path/summary 注入 result 对象的 `handoff_path` / `handoff_summary`
- [x] 2.3.3 设置 `next_action` 为 "The problem must be resolved in the chrome-agent repository. See handoff document at <handoff_path>."

### 2.4 CLI: `runCrawl()` 失败路径集成

- [x] 2.4.1 在 `runCrawl()` 的以下 failure 分支中应用 handoff 生成：
  - Strategy 缺失且无法创建（strategy === null 且非 MediaWiki API 路径）
  - Entry point 无法解析
  - Scrapling preflight 失败
  - MediaWiki API pipeline exit code >= 10 且 fallback 也失败
- [x] 2.4.2 每个分支中：判断 internal → 生成 handoff → 注入 result 字段

### 2.5 CLI: `runExplore()` 失败路径集成

- [x] 2.5.1 在 `runExplore()` 的以下 failure 分支中应用 handoff 生成：
  - Deep discovery pipeline 依赖缺失（Python deps）
  - Deep discovery pipeline 返回非零退出
  - Deep discovery pipeline 返回无效 JSON
- [x] 2.5.2 按 2.3.2 相同模式注入 handoff_path / handoff_summary

### 2.6 CLI: `runScrape()` 失败路径集成

- [x] 2.6.1 阅读 `runScrape()` 现有实现，定位 failure 分支
- [x] 2.6.2 对内部失败场景应用 handoff 生成（按与 fetch/crawl 相同的模式）

### 2.7 SKILL.md: Handoff Gate 章节

- [x] 2.7.1 在 `skills/chrome-agent/SKILL.md` 的「Result Packaging」章节之后新增「Handoff Gate」章节
- [x] 2.7.2 定义 Handoff Gate 核心规则：
  - 检测 CLI 结果中的 `handoff_path` 字段
  - 存在时停止所有工作流 dispatch
  - 禁止绕过行为（直接调用引擎、编写替代脚本等）
- [x] 2.7.3 定义用户呈现模板：
  - Halting notice: "工作流中断"
  - handoff_summary
  - handoff_path
  - chrome-agent 仓库修复步骤
  - 原始 CLI 命令
- [x] 2.7.4 定义无 handoff 场景的原有行为保持不变

### 2.8 SKILL.md: Result Packaging 更新

- [x] 2.8.1 在 preferred final shape 中增加可选字段：`handoff_path` 和 `handoff_summary`
- [x] 2.8.2 指定当 `handoff_path` 存在时，`next_action` 的固定值
- [x] 2.8.3 指定当 `handoff_path` 存在时，skill 跳过正常的 result passthrough，直接进入 Handoff Gate 呈现

## 3. 收敛与验证准备

- [x] 3.1 确认测试场景：
  - Pipeline exit code → handoff 生成 + 路径正确
  - Strategy 缺失 + deep discovery 失败 → handoff 生成
  - Engine preflight 失败 → handoff 生成
  - 目标网站 404 → 不生成 handoff
  - 无效 URL → 不生成 handoff
  - CHROME_AGENT_REPO 未设置 → 不生成 handoff
  - SKILL.md Handoff Gate 正确识别 handoff_path 并停止工作流
  - SKILL.md 在无 handoff_path 时保持原有行为
- [x] 3.2 标记需要进入 writeback 的文件：
  - `skills/chrome-agent/SKILL.md`（Handoff Gate + Result Packaging 更新）
  - `AGENTS.md`（handoff 工作流说明）

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 verification.md（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 verification.md 结论生成或更新 writeback.md（目标、字段映射、前置条件）
- [x] 4.3 执行 writeback.md 中定义的回写目标，并记录可审计证据（链接、时间、执行人、结果）
