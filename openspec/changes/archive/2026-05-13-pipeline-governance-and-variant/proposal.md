# Proposal

## 问题定义

Neon Abyss Fandom Wiki crawl 暴露了 pipeline 管线设计中的 7 个问题（P1-P7），其中 3 个深层原因指向治理工作流缺陷：

1. **策略文件可引用不存在的 registry ID** — `content_profile.link_resolver: "short_name"` 在 `_STRATEGY_REGISTRY` 中无对应条目，但 pipeline 仅 warning + 降级，不阻止执行
2. **change design 中平台假设无追踪机制** — `html-rendered-wiki-crawl` design 在 wiki.gg 上验证，未记录对 Fandom 的兼容假设，导致跨 platform 执行时出现 missingtitle、Phase A 不过滤、HTML 清理规则不匹配等问题
3. **策略 ID 的扩展顺序颠倒** — 策略文件先引用未实现的 ID（`fandom_infobox`），再考虑实现对应类，而非先注册后引用

这三个缺陷的共同根因：**策略文件与 pipeline 之间缺乏 schema 契约层**。策略文件作为 pipeline 的消费者，没有遵守"ID 必须已注册"的约束。

此外，MediaWiki 平台的变体（Fandom、wiki.gg、标准 MediaWiki）在 API 行为、HTML 结构、错误语义、内容组织上存在显著差异，当前 pipeline 将其视为同质化平台。

## 范围边界

**范围内：**
- 建立 `_STRATEGY_REGISTRY` 作为策略 schema 的权威来源
- 定义 pipeline 启动时对策略文件的 schema 校验（硬性失败，非 warning 降级）
- 定义 AGENTS.md 中的治理约束（扩展协议、注册约束、引用完整性）
- 引入 `platform_variant` 概念，对 MediaWiki 进行子类型化
- 提供 platform_variant 的行为抽象框架（不要求在本 change 中实现所有 variant 行为）
- 更新站点模板以支持 variant 声明

**范围外：**
- 本 change 不实现 `FandomInfoboxTemplateProcessor` 等具体策略类（留给管线修复 change）
- 本 change 不修复现有策略文件的 ID 引用问题（留给管线修复 change）
- 本 change 不涉及 Pipeline 的 checkpoint/resume 机制
- 本 change 不改变 `_STRATEGY_REGISTRY` 的运行时结构（仅增加治理约束）
- 不耦合 openspec 工作流程——治理约束直接写入 AGENTS.md

## Capabilities

### New Capabilities
- `pipeline-strategy-schema`: 策略 ID 注册中心的 Schema 契约层定义，包括权威来源声明、引用完整性校验规则、扩展协议
- `platform-variant-framework`: MediaWiki 平台变体（Fandom、wiki.gg、标准 MediaWiki）的行为差异建模框架，包括 variant 声明、行为分支接口

### Modified Capabilities
- `site-strategy`: 策略文件 schema 扩展——新增 `content_profile` ID 引用完整性约束、可选 `platform_variant` 声明字段；策略文件创建/编辑流程必须经过 schema 校验
- `agents-governance`: AGENTS.md 新增 Pipeline Strategy Schema 治理章节，定义 registry 权威、扩展协议、引用校验、变更约束等规则
- `mediawiki-api-extraction-pipeline`: Pipeline 启动时必须对策略文件执行 schema hard-fail 校验；Pipeline 各阶段根据 `platform_variant` 值选择行为分支

## Capabilities 待确认项

- [x] 能力清单已与用户确认（在 explore 模式中经过讨论、用户确定了方向 A + AGENTS.md 约束的方案）

## Impact

| 受影响组件 | 影响类型 | 描述 |
|-----------|---------|------|
| `AGENTS.md` | 新增内容 | 新增 Pipeline Strategy Schema 治理章节 |
| `scripts/mediawiki-api-extract/pipeline/orchestrate.py` | 行为变更 | `build_pipeline()` 中未知 ID 从 warning 改为 hard-fail；增加 platform_variant 分支逻辑 |
| `scripts/explore/strategy_scaffold_generator.py` | 行为变更 | bootstrap 输出策略文件前必须校验 content_profile ID 的有效性 |
| `sites/templates/*.yaml` | Schema 扩展 | 模板可选包含 content_profile 和 platform_variant 字段 |
| `sites/strategies/*/strategy.md` | 后效约束 | 创建/编辑策略文件必须遵守 ID 引用完整性规则 |
| `openspec/specs/agents-governance/spec.md` | 同步更新 | AGENTS.md 治理约束变更后同步更新其 spec 真源 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `AGENTS.md`（治理约束目的地）
  - `scripts/mediawiki-api-extract/pipeline/orchestrate.py`（`_STRATEGY_REGISTRY`）
  - `sites/templates/`（模板）
  - `scripts/explore/strategy_scaffold_generator.py`（bootstrap 输出）
  - `openspec/specs/agents-governance/spec.md`（spec 真源同步）
