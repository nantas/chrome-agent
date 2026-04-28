# Proposal

## 问题定义

chrome-agent 项目在 Obsidian 项目页中已被重新定义为"跨仓库网页抓取服务"，但当前仓库仍停留在"浏览器工作台"的操作手册阶段。AGENTS.md（245 行）和 README.md（154 行）主要描述如何操作 Scrapling 和 fallback 工具，而非服务治理、能力契约和策略库。项目页与仓库之间存在显著落差。

项目需要一个总体规划文档来建立从当前状态到目标状态的完整路径，并在此规划指导下重写 README.md 以对齐项目身份。

## 范围边界

**范围内（本 change）：**
- 产出总体规划文档（全局项目上下文、能力全景图、阶段划分与边界）
- 重写 README.md 为仓库全景说明
- 不涉及任何能力实现

**范围外（后续 change 按阶段处理）：**
- AGENTS.md 治理重写（留到 Phase 1）
- 契约冻结、策略库标准化、引擎扩展治理等具体实现

## Capabilities

### New Capabilities
- `master-plan`: 产出跨阶段的总体规划文档，定义项目目标、能力全景、阶段边界与上下文
- `readme-rewrite`: 重写 README.md 与项目服务身份对齐

## Capabilities 待确认项

- [x] 能力清单已与用户确认

## Impact

**益处：**
- 规划文档为后续每个 Phase 的 change 提供上下文和边界锚点
- README 立即对齐项目服务身份

**影响到的既有文件：**
- README.md（重写）

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
  - `project_page_ref`: `20_项目/chrome-agent/chrome-agent.md`
  - `writeback_targets`: Obsidian 项目页 + Writeback 记录页
