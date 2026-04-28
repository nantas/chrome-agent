# Proposal

## 问题定义

Phase 1-3 完成了治理基础重建、5 个引擎契约冻结、策略库标准化。但引擎生态缺乏可扩展性治理：

1. **引擎注册分散**：5 个引擎的注册信息内联在 `engine-contracts/spec.md` 的多个表格中（注册表、选择映射、错误矩阵、smoke-check 清单）。新增一个引擎需要同时修改这些表格，没有独立的注册索引。

2. **无接入流程**：没有新引擎 artifact checklist、contract spec 模板、验证标准。添加新引擎（如 `scrapling-bulk-fetch`）只能手动参照 Phase 2 的既有模式，易遗漏步骤。

3. **优先级模型陈旧**：Phase 2 的 engine selection mapping 和 Phase 3 的 `engine_sequence.purpose`（primary/diagnostic）是扁平的角色标注，不具备多维评分能力。执行效率、稳定性、适配性应从引擎特性中定量表达，并支持站点策略和反爬策略的上下文调制。

4. **策略层耦合**：anti-crawl 的 `engine_sequence` 字段使用 `purpose`（primary/fallback/diagnostic）表达优先级，与新优先级模型冲突；site-strategy 不支持引擎偏好声明。

## 范围边界

**范围内：**
- 创建 `configs/engine-registry.json` 作为引擎注册索引（JSON 格式，机器可查询）
- 创建 `engine-registry` spec：定义注册格式、引擎特性评分（efficiency/stability/adaptability）、`composite_score` 与 `default_rank` 推导规则、引擎生命周期状态
- 创建 `extension-api` spec：定义新引擎接入的 artifact checklist、contract spec 模板、治理规则
- 创建 `scrapling-bulk-fetch-contract` spec：作为通过 extension-api 接入的示例引擎契约（input/output/error + smoke-check）
- **MODIFIED** `engine-contracts`：删除内联 engine 列表，引用 `configs/engine-registry.json`
- **MODIFIED** `anti-crawl-schema`：`engine_sequence` 字段废弃，替换为 `engine_priority`（`rank` 替代 `purpose`）
- **MODIFIED** `site-strategy-schema`：新增 optional `engine_preference` 字段
- 更新 AGENTS.md 中 engine-registry 状态为"已规范"，追加引擎扩展治理章节
- 创建决策记录 `docs/decisions/2026-04-28-engine-registry-design.md`
- 更新 `docs/governance-and-capability-plan.md` Phase 4 描述
- 迁移 5 个 anti-crawl 策略文件的 `engine_sequence` → `engine_priority`

**排他边界：**
- 不包含运行时引擎自动选择——只定义数据模型，选择算法由 agent 决策
- 不包含引擎编排层（调度、并发、重试策略）
- 不修改任何引擎实现
- 不新增除 `scrapling-bulk-fetch-contract` 以外的引擎契约

## Capabilities

### New Capabilities

- `engine-registry`: 引擎注册机制——注册格式（JSON）、特性评分维度（efficiency/stability/adaptability）、`composite_score` 加权公式（adaptability×0.50 + stability×0.30 + efficiency×0.20）、`default_rank` 推导规则（体现 Scrapling-first 原则）、引擎生命周期状态（draft/frozen/superseded）
- `extension-api`: 新引擎接入流程——artifact checklist（contract spec + registry entry + error matrix update + smoke-check）、contract spec 模板（含 input/output/error 三维占位）、接入治理规则（命名规范、验证要求、决策记录要求）
- `scrapling-bulk-fetch-contract`: Scrapling bulk-fetch 引擎契约——input/output/error 三维定义、batch URL 参数约定、session 复用规则、smoke-check scenario（example.com + httpbin.org）

### Modified Capabilities

- `engine-contracts`: 删除内联 engine 注册表和分析表，引用 `configs/engine-registry.json`；保留 cross-engine error scheme、engine selection mapping 和合同合规性标准
- `anti-crawl-schema`: 将 `engine_sequence` 字段替换为 `engine_priority`，新的 `rank` 字段（integer，1-based）替代旧的 `purpose` 字段（枚举：primary/fallback/diagnostic），`config` 和 `engine` 保持原样
- `site-strategy-schema`: 新增 optional 字段，`engine_preference` 对象 `preferred` （string，engine canonical ID）和可选 `reason`（string），可在文件级别或 `structure.pages[].engine_preference` 级别设置

## Capabilities 待确认项

- [x] 能力清单已与用户确认——explore mode 中讨论确认：Option B 解耦架构、加权优先级模型、scrapling-bulk-fetch 为示例引擎、engine_preference 纳入 site-strategy

## Impact

- **configs/** 新增 `engine-registry.json`（6 个 engines：5 个现有 + scrapling-bulk-fetch）
- **openspec/specs/** 新增 3 个 capability 目录（`engine-registry`、`extension-api`、`scrapling-bulk-fetch-contract`）
- **openspec/specs/** 修改 3 个既有 spec（`engine-contracts`、`anti-crawl-schema`、`site-strategy-schema`）
- **sites/anti-crawl/** 5 个策略文件 frontmatter 字段迁移（`engine_sequence` → `engine_priority`）
- **AGENTS.md** 能力框架表格 engine-registry 状态更新（"未实现" → "已规范"）；新增"引擎扩展治理"章节
- **docs/** 新增决策记录、更新总体规划 Phase 4 描述

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页: `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
- 已确认项目页: `20_项目/chrome-agent/chrome-agent.md`
- 已确认回写目标: 项目页面 + Writeback 记录页面，verification 完成后执行
