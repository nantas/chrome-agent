# Design

## Context

外部仓库/agent 通过 chrome-agent workflow skill 执行爬取操作时，遇到管线异常、策略缺口、引擎故障等内部分失败后，缺乏强制停止的机械闸门。当前 `failure` + `next_action` 只是软性建议，无法阻止外部 agent 编写绕过的 curl/wget 脚本（W-line 问题）。

本 change 在 CLI 中新增 handoff 文档生成机制，在 SKILL.md 中新增 Handoff Gate 闸门，从"建议修复"升级为"强制停止并路由到 chrome-agent 仓库"。

## Goals / Non-Goals

**Goals:**
- CLI 在内部分失败场景自动生成 handoff.md，写入 `outputs/handoffs/<run-tag>/handoff.md`
- handoff 文档包含完整上下文、错误详情、run artifacts 路径和下一步指引
- handoff 路径通过 CLI JSON 结果中的 `handoff_path` 字段传递给调用方
- SKILL.md 新增 Handoff Gate，检测 `handoff_path` 后立即停止工作流并路由到 chrome-agent 仓库
- SKILL.md 呈现结构化消息：故障摘要、handoff 路径、chrome-agent 修复步骤
- SKILL.md 明确禁止绕过行为（直接调用引擎、编写替代脚本等）

**Non-Goals:**
- 不修改 `result` 字段的枚举值（保持 `success` / `partial_success` / `failure`）
- 不修改 `reports/` 的现有报告机制
- 不在运行时做 P-line/S-line/W-line 分类（分类推迟到 chrome-agent 仓库离线阶段）
- 不提供绕过 Handoff Gate 的选项
- 不修改 doctor 命令的行为
- 不修改 pipeline 脚本的 exit code 约定

## Decisions

### D1: `generateHandoff()` 为独立函数，不拆分模块

**Decision**: 在 `scripts/chrome-agent-cli.mjs` 中新增 `generateHandoff()` 函数，不抽取为独立模块。

**Rationale**: handoff 生成的职责范围明确——接受 context + error details → 写出 handoff.md → 返回 path。函数体约 60-80 行，不足以独立成文件。保持与现有 `buildFetchReport()`、`buildCrawlReport()` 等 report 函数同级，延续现有组织模式。

**Alternatives considered**:
- 单独 `scripts/handoff.sh` 或 `scripts/handoff.mjs`：过度分层，且需要额外 IPC
- 在 CLI 入口 handler 中内联：可读性差，不利于后续扩展

### D2: Handoff 触发在具体命令的 failure 路径末尾、result 创建之前

**Decision**: 在 `runFetch()`、`runCrawl()`、`runExplore()`、`runScrape()` 的 failure 返回路径中，在构造 result 对象之前调用 `generateHandoff()`。外层 `resolveRepository()` 的环境配置失败不触发 handoff。

**Rationale**: 命令处理器已有完整的执行上下文（target URL、run directory、error details），生成 handoff 所需信息已就位。外层的 repo resolution 失败属于调用方配置问题，不产生 handoff。

**Trigger 判断逻辑（在失败分支中）**：
```
if (isInternalFailure(command, error)) {
  handoffInfo = generateHandoff({ command, target, repoRef, runDir, error, strategy });
  result.handoff_path = handoffInfo.path;
  result.handoff_summary = handoffInfo.summary;
}
```

`isInternalFailure()` 的判定规则：
- Pipeline exit code >= 10 → internal
- Strategy 缺失 + deep discovery 失败 → internal
- Engine preflight 安装尝试后仍失败 → internal
- Sample conversion / self-check 不可恢复失败 → internal
- 目标 HTTP error / 无效 URL / env 配置缺失 → external

#### D3: Handoff 的 next_action 字段标准化

**Decision**: 当 `handoff_path` 存在时，`next_action` 固定为：
```
"The problem must be resolved in the chrome-agent repository. See handoff document at <handoff_path>."
```
不再保留原有的 caller-side remediation 文本。

**Rationale**: `handoff_path` 的语义是"问题归属 chrome-agent 仓库"，next_action 应与之对齐。原有的 caller-side 修复建议不再适用，因为 handoff 意味着不属于调用方能自行解决的问题。

### D4: Handoff 目录路径复用现有 run-tag 约定

**Decision**: Handoff 文件路径使用 `outputs/handoffs/<run-tag>/handoff.md`，其中 `<run-tag>` 由 `buildRunPaths()` 的 slug 规则产生（`<timestamp>-<command>-<slug>`）。

**Rationale**: 与现有 `outputs/<run-tag>/` 的目录命名规则一致，避免引入新的路径生成逻辑。当命令同时有 run directory 时，两者共享同一个 run-tag 但分属不同父目录，关系明确。

**示例**：
- Run directory: `outputs/20260518T153000-crawl-bindingofisaacrebirth-wiki-gg/`
- Handoff directory: `outputs/handoffs/20260518T153000-crawl-bindingofisaacrebirth-wiki-gg/`
- Handoff file: `outputs/handoffs/20260518T153000-crawl-bindingofisaacrebirth-wiki-gg/handoff.md`

### D5: Handoff 文档的 `run_directory` 指向原始运行目录

**Decision**: 当命令有 run directory 时，handoff 中的 `run_directory` 字段指向 `outputs/<run-tag>/`（即原始 run directory），而非 handoff 自身所在的 `outputs/handoffs/<run-tag>/`。

**Rationale**: 原始 run directory 包含 manifest.json、logs、HTML/Markdown 产出等诊断所需的关键文件。指向它可以让 chrome-agent 仓库的离线分析能直接找到全部运行上下文。

### D6: SKILL.md Handoff Gate 紧跟在 Result Packaging 之后

**Decision**: Handoff Gate 章节插入在 SKILL.md 的「Result Packaging」之后、现有的「Route to Sample Conversion」或「Runtime Boundaries」之前，作为结果处理后的下一步路由判断。

**Rationale**: 与现有工作流路由规则的编排逻辑一致——先执行命令→封装结果→检查是否有 handoff→若有则停止，若无则继续。放在 Result Packaging 之后能使流程连续。

### D7: no-handoff 的 failure 保持现有行为不变

**Decision**: 对于外部失败（目标网站 error、无效 URL、env 配置缺失），不生成 handoff，不改变现有行为。CLI 继续返回 `result: "failure"` 和 `next_action`。SKILL.md 按原样透传。

**Rationale**: 这些失败无需 chrome-agent 仓库修复，调用方自行解决问题即可。将 handoff 限定在内部分失败范围，避免 handoff 噪音。

## Risks / Migration

### Risk 1: 内部/外部区分判断错误导致漏报或误报

**Mitigation**: `isInternalFailure()` 的实现采用白名单+黑名单模式：
- 白名单：明确标注为 internal 的失败路径（pipeline exit code、strategy gap 等）
- 黑名单：明确标注为 external 的失败路径（HTTP 4xx/5xx、env 缺失）
- 不在列表中的失败路径默认不触发 handoff（偏向保守）
- 后续可通过 openspec change 扩展触发范围

### Risk 2: Handoff 文件堆积未被清理

**Mitigation**: `outputs/handoffs/` 位于 `outputs/` 下，已受 .gitignore 排除。`chrome-agent clean` 命令的 `--scope all` 模式应覆盖 `outputs/handoffs/`。用户可手动清理。

### Risk 3: 已有调用方可能因 handoff_path 字段出现而产生意外行为

**Mitigation**: `handoff_path` 为新增可选字段，仅在内部失败时出现。未解析该字段的调用方忽略它不影响现有行为。SKILL.md 的 Handoff Gate 仅当字段存在时触发，不存在时保持原行为。无需迁移步骤。

### Risk 4: Handoff 文档内容过时（chrome-agent 已修复但 handoff 仍在文件系统上）

**Mitigation**: Handoff 是运行时瞬间快照，不设"追踪"语义。修复完成后，chrome-agent 仓库的 agent 可以删除或归档 handoff 文件。推荐：验证通过后执行 `rm outputs/handoffs/<run-tag>/handoff.md`。
