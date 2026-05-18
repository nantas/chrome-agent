# Proposal

## 问题定义

外部仓库或 agent 通过 chrome-agent workflow skill 执行爬取、探索、抓取等操作时，遇到管线异常、策略缺口、引擎故障等**应由 chrome-agent 仓库内部解决的问题**，当前行为是：

1. CLI 返回 `failure` + `next_action` 字段描述修复路径
2. SKILL.md 将结果透传给调用方 agent
3. 调用方 agent 看到 `failure` 后，缺乏强制停止的机械闸门，倾向于自行编写绕过的脚本或二次封装

这产生了 W-line 问题（工作流层）：外部护网脚本覆盖了管线应承担的能力，问题不在源头修复，导致同类问题反复出现。

**根本原因**：缺乏一个从"失败结果"到"chrome-agent 仓库必须修复"的机械化的桥接机制。`failure` + `next_action` 只是软性建议，不是闸门。

## 范围边界

**范围内：**
- CLI 在内部失败场景（管线/策略/引擎相关）自动生成 handoff.md 文档，写入 `outputs/handoffs/` 目录
- CLI 在生成 handoff 后，result 仍为 `failure`，但附加 `handoff_path` 字段
- SKILL.md 新增 Handoff Gate：当 CLI 返回包含 `handoff_path` 的结果时，SKILL.md 必须停止工作流路由，呈现 handoff 路径，提示用户切换到 chrome-agent 仓库修复
- handoff 文档结构定义：context、错误详情、run artifacts 路径、expected behavior、next steps
- 仅**内部失败**触发 handoff：管线脚本非零退出、策略缺失/不匹配、引擎 preflight 失败、策略 schema 违规
- **外部失败**不触发 handoff：目标网站 HTTP 4xx/5xx、URL 无效、CHROME_AGENT_REPO 未设置、网络超时

**范围外：**
- 运行时问题分类（P-line/S-line/W-line）——分类推迟到 chrome-agent 仓库离线分析阶段
- 绕过机制——暂不提供
- 已有 `reports/` 报告机制的修改
- 非 CLI 路由的工作流（如直接调用 python 脚本）——手动作业不在此 change 治理范围内
- 现有 spec 的非必要修改——仅修改 `global-workflow-skill`

## Capabilities

### New Capabilities
- `handoff-emission`: CLI 在内部分失败场景自动生成 handoff.md 文档，包含完整上下文、错误详情与 run artifacts 引用路径，写入 `outputs/handoffs/<run-tag>/handoff.md`
- `handoff-gate`: SKILL.md 中的 Handoff Gate 闸门——当 CLI 返回结果包含 `handoff_path` 字段时，skill 必须停止工作流，呈现 handoff 路径，并指示用户切换到 chrome-agent 仓库修复

### Modified Capabilities
- `global-workflow-skill`: 在结果封装章节中增加 handoff_path 处理；新增 "Handoff Gate" 章节定义闸门协议

## Capabilities 待确认项

- [x] 能力清单已与用户确认（方案讨论中已确认）

## Impact

- **代码变更**: `scripts/chrome-agent-cli.mjs` 新增 handoff 生成函数；`skills/chrome-agent/SKILL.md` 新增 Handoff Gate 章节
- **结果格式变更**: CLI JSON 结果新增 `handoff_path`、`handoff_summary` 字段。已有 `result` 枚举值不变（保持 `success` / `partial_success` / `failure`）
- **新增目录**: `outputs/handoffs/` 目录（.gitignore 应已覆盖，与 `outputs/` 同级）
- **向后兼容**: `handoff_path` 为新增可选字段，仅内部失败时出现。已有调用方忽略该字段不影响原有行为
- **破坏性变更**: 无

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页（新增）：`handoff-emission`、`handoff-gate`
  - 标准页（修改）：`global-workflow-skill`
  - 回写目标：`AGENTS.md`（handoff 工作流说明）、`skills/chrome-agent/SKILL.md`（Handoff Gate）
