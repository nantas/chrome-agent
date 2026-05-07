# Proposal

## 问题定义

当前 `scripts/mediawiki-api-extract` 管线为 1292 行单体脚本，存在以下架构问题：

1. **隐含假设硬编码**：管线行为直接写死在代码中（如 `validate_api_config` 硬编码 `required = {"page_list", "wikitext_parse"}`），站点差异无法通过配置表达
2. **无法扩展**：现有架构不支持策略注入。为 StS2 等复杂站点新增行为（如 hybrid content acquisition、短名链接解析）需要修改核心管线代码，无法通过配置隔离
3. **Spec 规范缺失**：`mediawiki-api-extraction/spec.md` 缺少策略接口契约描述；`mediawiki-site-strategy/spec.md` 缺少 `api.content_profile` schema，导致管线可扩展性没有规范层面的保障
4. **验证逻辑僵化**：capabilities 验证使用硬编码集合而非策略声明的能力需求，与策略文件实际声明的内容不一致

这些问题共同导致：当前管线只能处理 balatro 这类"最简单 MediaWiki 场景"，无法在不修改核心代码的前提下适配 StS2 等复杂站点。要解决 StS2 的 13 个问题，必须先建立可扩展的策略组合架构。

## 范围边界

### 范围内（Change 1）

- **规范更新**：
  - `mediawiki-api-extraction/spec.md`：追加策略接口契约（5 个 Protocol 接口）、capabilities 受控词汇表、namespace 场景、管线核心流程与策略挂载点描述
  - `mediawiki-site-strategy/spec.md`：追加 `api.content_profile` schema（可选策略覆盖字段定义）
- **架构重构**：
  - 单体脚本 → 多文件包（`scripts/mediawiki-api-extract/`）
  - 提取 5 个策略接口（Protocol classes）：Discovery、ContentAcquisition、LinkResolver、TemplateProcessor、ListPageAssembler
  - 为每个接口提供默认实现，行为与当前代码完全一致
  - 管线编排层（`pipeline.py`）负责策略组装与 capabilities 验证
- **回归验证**：
  - balatro 爬取输出与重构前逐文件一致（`diff -r` 0 差异）

### 范围外（Change 1 不涉及）

- 不修复任何现有缺陷（短名链接、括号正则、路径计算、DPL 表格、DRUID 图片等）—— 这些问题在 Change 2 解决
- 不新增任何外部行为（不修改 balatro 输出内容）
- 不新增 StS2 专用策略实现
- 不新增任何引擎（如 `obscura-fetch`）
- 不新增 L6 验证质量层组件

## Capabilities

### New Capabilities

（无新增能力——本次变更不引入新能力，只重构现有能力）

### Modified Capabilities

- `mediawiki-api-extraction`: 扩展管线行为规范——新增策略接口契约（Discovery、ContentAcquisition、LinkResolver、TemplateProcessor、ListPageAssembler）、capabilities 受控词汇表、namespace 场景描述，以及管线核心流程与策略挂载点的边界定义
- `mediawiki-site-strategy`: 扩展站点策略 schema——新增 `api.content_profile` 字段，支持声明策略覆盖（`discovery_strategy`、`content_acquisition`、`link_resolver`、`template_processor`、`list_page_assembler`）

## Capabilities 待确认项

- [x] 能力清单已确认——本次只修改两个既有 capability，无新增

## Impact

| 组件 | 影响 | 风险 |
|------|------|------|
| `scripts/mediawiki-api-extract` | 单文件 → 多文件包，CLI 入口变为 `python -m scripts.mediawiki-api-extract` | 低——保持 `__main__.py` 兼容参数；可通过 symlink 或 alias 保持直接调用 |
| 已有策略文件 | balatro strategy 可选新增 `api.content_profile` 字段（非必须，默认行为全兼容） | 最低——可选声明，不声明不影响行为 |
| Spec 文件 | 两个 spec 文件追加内容 | 低——追加不影响已有场景 |
| 已有爬取输出 | 无影响——只变更提取逻辑，不修改输出语义 | 低——balatro 回归验证确保一致性 |
| 后处理脚本 | 无影响——输出格式不变 | 无 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `repo://chrome-agent/openspec/specs/mediawiki-api-extraction/spec.md` — MODIFIED
  - `repo://chrome-agent/openspec/specs/mediawiki-site-strategy/spec.md` — MODIFIED
  - `repo://chrome-agent/scripts/mediawiki-api-extract/` — RESTRUCTURED
  - `repo://chrome-agent/sites/strategies/balatrowiki.org/strategy.md` — MODIFIED（可选）
  - `repo://chrome-agent/AGENTS.md` — MODIFIED
  - 项目页面：`repo://my-wiki/docs/design/chrome-agent-mediawiki-extraction-improvement-plan.md`
