# Proposal

## 问题定义

chrome-agent 已通过前置 `governance-and-capability-rebuild` change 确定了"跨仓库网页抓取服务"身份，并产出了总体规划文档和 README 重写。但仓库的治理层仍然空白：

1. **AGENTS.md 未对齐服务身份**：现有 245 行内容为操作手册（Scrapling 怎么用、fallback 什么时候触发），缺少服务身份声明、契约框架、治理政策和目录结构规范。按总体规划要求，AGENTS.md 应是纯治理文档，操作细节应下沉到 `docs/playbooks/`。
2. **能力契约未建立**：仓库 5 个引擎（Scrapling get、fetch、stealthy-fetch、chrome-devtools-mcp、chrome-cdp）的输入/输出/错误无统一规范。在引擎契约冻结（Phase 2）之前，需要先建立契约元模型（通用 schema、必填字段、命名与存放规则）。
3. **治理 spec 缺失**：`openspec/specs/` 中尚无反映仓库治理规则（AGENTS.md 结构、路由规范、目录治理、决策记录机制）的行为规范。

## 范围边界

**范围内（本 change）：**
- 重写 AGENTS.md 为纯治理文档（服务身份、契约框架、治理政策、目录规范）
- 将现有 AGENTS.md 中的操作流程内容提取到 `docs/playbooks/` 作为独立操作手册
- 创建 `agents-governance` spec：定义 AGENTS.md 结构、治理规则、路由策略、报告规范、目录治理、决策记录治理
- 创建 `capability-contracts` spec：定义契约元模型（通用 contract schema、命名规则、存放路径 `openspec/specs/<engine-id>-contract/`）
- 标记 `scrapling-first-browser-workflow` spec 为 superseded（其规范内容被 `agents-governance` 吸收）

**范围外（留到后续 Phase）：**
- 具体引擎的契约内容填充（Phase 2）
- 策略库标准化（Phase 3）
- 引擎扩展机制（Phase 4）
- 安装链与输出生命周期（Phase 5）

## Capabilities

### New Capabilities
- `agents-governance`: 定义仓库治理层的行为规范——AGENTS.md 结构与强制内容、服务身份声明、工作流路由规则、引擎选择策略、报告产出规范、目录结构治理、决策记录治理
- `capability-contracts`: 定义引擎能力契约的通用元模型——contract 的三维结构（input / output / error）、必填字段与语义约定、命名与存放规则、版本管理约定；不包含具体引擎的契约值

### Modified Capabilities
- `scrapling-first-browser-workflow`: 标记为 superseded，其操作流程与路由规则被 `agents-governance` 吸收。原 spec 保留为历史记录，新增 `superseded_by: agents-governance` 声明

## Capabilities 待确认项

- [x] 能力清单已与用户确认（对话中确认：agents-governance 覆盖 7 个治理维度、capability-contracts 限元模型、混合命名方式）

## Impact

**益处：**
- AGENTS.md 明确仓库治理身份，为后续 Phase 提供稳定的治理锚点
- 契约元模型为 Phase 2 的引擎契约冻结提供统一的 schema 和存放规范
- 操作细节从 AGENTS.md 移出后，playbooks 成为独立的操作知识库

**影响到的既有文件：**
- `AGENTS.md` — 完全重写为纯治理文档（现有操作流程内容提取到 playbooks）
- `openspec/specs/agents-governance/spec.md` — 新建
- `openspec/specs/capability-contracts/spec.md` — 新建
- `openspec/specs/scrapling-first-browser-workflow/spec.md` — 追加 superseded 声明
- `docs/playbooks/` — 新增独立操作手册
- `docs/governance-and-capability-plan.md` — Phase 1 描述可能需要微调以反映实际交付物

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
  - `project_page_ref`: `20_项目/chrome-agent/chrome-agent.md`
  - `writeback_targets`: Obsidian 项目页 + Writeback 记录页
