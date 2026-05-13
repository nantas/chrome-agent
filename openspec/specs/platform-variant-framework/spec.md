# platform-variant-framework Specification

## Purpose
TBD - created by archiving change pipeline-governance-and-variant. Update Purpose after archive.
## Requirements
### Requirement: platform_variant 声明字段
The system SHALL 在策略文件的 `api` 对象中增加可选字段 `platform_variant`，用于声明 MediaWiki 平台的子类型。

`platform_variant` 为 enum 类型，当前受控词汇表：

| 值 | 描述 |
|------|-------------|
| `fandom` | Fandom-hosted MediaWiki（使用 `static.wikia.nocookie.net` CDN、`item-table-*` 类、ns=0 含翻译页面等） |
| `wiki-gg` | wiki.gg-hosted MediaWiki（使用 DRUID infobox、自定义命名空间等） |
| `standard` | 标准 MediaWiki（默认值，无特殊平台特征） |

`api.platform_variant` SHALL 是可选的。当未指定时，默认值为 `standard`。

#### Scenario: variant 声明示例
- **WHEN** 策略文件声明 `api.platform: mediawiki` 且 `api.platform_variant: fandom`
- **THEN** pipeline SHALL 识别此 sites 为 Fandom 变体
- **AND** 应用 Fandom 变体的行为分支（见后续 requirement）

#### Scenario: variant 默认值
- **WHEN** 策略文件声明 `api.platform: mediawiki` 但未指定 `api.platform_variant`
- **THEN** pipeline SHALL 使用 `standard` 作为默认值
- **AND** 行为 SHALL 与当前 pipeline 一致（无变体特定逻辑）

#### Scenario: variant 与 template 映射
- **WHEN** bootstrap-strategy 选择模板 `mediawiki-fandom.yaml`
- **THEN** 生成的策略文件 SHALL 自动包含 `api.platform_variant: fandom`
- **AND** 模板 registry.json 中的 `platform` 字段值 `mediawiki-fandom` SHALL 映射为 `api.platform_variant: fandom`
- **AND** `mediawiki-wiki-gg.yaml` 模板同理映射为 `wiki-gg`

### Requirement: Variant 行为分支接口
The system SHALL 在 pipeline 的 `run_pipeline()` 及 `build_pipeline()` 中根据 `platform_variant` 值选择行为分支。

行为分支点包括（当前 change 仅定义框架，具体行为实现留给后续管线修复 change）：

1. **Phase A 发现过滤**：Fandom variant 需要额外的页面存在性验证和翻译页排除
2. **Phase B 错误处理**：Fandom variant 需要处理 `missingtitle` 而非视为不可恢复错误
3. **Phase C HTML 清理规则**：不同的 variant 可能需要不同的 cleanup selectors（Fandom 的 `item-table-*` vs wiki.gg 的 `.druid-infobox`）

#### Scenario: Phase A variant 分支
- **WHEN** `run_phase_a()` 执行且 `platform_variant == "fandom"`
- **THEN** pipeline SHALL 在 `allpages` 发现后增加批量页面存在性验证（`action=query&prop=info`）
- **AND** SHALL 过滤掉标题以 `_tr` 结尾的页面
- **AND** SHALL 非 Fandom variant 时保持当前行为

#### Scenario: Phase B variant 分支
- **WHEN** `process_single_page()` 执行且 `platform_variant == "fandom"`
- **THEN** pipeline SHALL 捕获 `PageNotFoundError` 并返回 `status: "skipped"` 而非 `status: "error"`
- **AND** SHALL 非 Fandom variant 时保持当前错误处理行为

#### Scenario: Phase C variant 分支
- **WHEN** `_process_html_page()` 执行且 `platform_variant == "fandom"`
- **THEN** pipeline SHALL 应用 Fandom 专有的 HTML 清理规则（`item-table-*`、`ambox` 等）
- **AND** SHALL 非 Fandom variant 时保持当前清理行为

### Requirement: Variant 注册扩展
The system SHALL 支持通过 `_STRATEGY_REGISTRY` 类型的扩展机制增加新的 `platform_variant` 值。

新增 variant 值需要：
1. 在本 spec 的受控词汇表中注册新的 variant ID
2. 定义该 variant 的行为分支条件
3. 更新 `sites/templates/registry.json` 模板映射
4. 在 pipeline 代码中增加对应 variant 的行为分支

#### Scenario: 新增 wiki-gg variant
- **WHEN** `wiki-gg` 作为 variant 值被注册
- **THEN** `api.platform_variant: "wiki-gg"` SHALL 被 pipeline 识别
- **AND** Phase C 的 HTML 清理规则 SHALL 应用 `.druid-infobox` 过滤和 DRUID 卡牌统计提取
- **AND** wiki.gg 的策略模板 SHALL 自动包含 `platform_variant: wiki-gg`
