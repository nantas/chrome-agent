# Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-api-extraction-pipeline`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认 pipeline 需要 schema hard-fail 校验和 platform_variant 行为分支

## 规范真源声明

- 本文件是 `mediawiki-api-extraction-pipeline` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Pipeline 启动时策略 schema hard-fail 校验

The system SHALL 在 `run_pipeline()` 中启动阶段增加对策略文件 `content_profile` 的 schema 校验。

校验位置：在 `build_pipeline()` 调用之后、`validate_api_config()` 之前或结合。

校验逻辑：
1. 读取策略文件的 `api.content_profile` 字段
2. 遍历每个字段，检查其 value 是否在 `_STRATEGY_REGISTRY` 对应维度的 key 集合中
3. 所有 ID 有效 → 正常继续
4. 存在无效 ID → `log.error` + `return EXIT_STRATEGY_ERROR`
5. 未指定 `content_profile`（全默认）→ 跳过校验

#### Scenario: 校验通过

- **WHEN** 策略文件指定 `content_profile: { link_resolver: "exact_title_match" }`
- **AND** `"exact_title_match"` 在 `_STRATEGY_REGISTRY["link_resolver"]` 中存在
- **THEN** pipeline SHALL 正常进入后续阶段
- **AND** SHALL 不发出关于 strategy ID 的警告

#### Scenario: 校验拒绝

- **WHEN** 策略文件指定 `content_profile: { link_resolver: "short_name" }`
- **AND** `"short_name"` 在 `_STRATEGY_REGISTRY["link_resolver"]` 中不存在
- **THEN** pipeline SHALL 记录 `log.error("Strategy ID '%s' not registered in %s — available: %s", id, dimension, list(registry.keys()))`
- **AND** SHALL 返回 `EXIT_STRATEGY_ERROR`
- **AND** SHALL 不执行任何后续管线阶段

#### Scenario: 无 content_profile

- **WHEN** 策略文件未指定 `api.content_profile`
- **THEN** `build_pipeline()` SHALL 使用所有默认策略实现
- **AND** SHALL 不触发 content_profile 校验
- **AND** pipeline SHALL 正常启动

### Requirement: Pipeline platform_variant 行为分支

The system SHALL 在 pipeline 的以下阶段根据 `platform_variant` 值选择行为分支：

1. `run_pipeline()`：解析 `strategy.get("api", {}).get("platform_variant", "standard")` 并传递给下游阶段
2. `run_phase_a()`：Fandom variant 时增加页面存在性验证和翻译页过滤
3. `run_phase_b()` 中的 `process_single_page()`：Fandom variant 时错误处理分支
4. 后续 Phase B/C 的 HTML 清理：variant 指定的 cleanup 规则选择

当前 change 仅定义框架接口。具体的行为分支实现（如上所列）是**可选的**——实现只需要确保 `platform_variant` 字段能被 pipeline 读取和传递。

#### Scenario: Variant 传递

- **WHEN** `run_pipeline()` 执行
- **THEN** 它 SHALL 从策略文件的 `api.platform_variant` 读取版本值
- **AND** SHALL 作为参数传递给 `run_phase_a()` 和 `run_phase_b()`
- **AND** 当未指定时默认为 `"standard"`
- **AND** 当前至少 SHALL 记录 `log.info("Platform variant: %s", variant)` 以便追踪

#### Scenario: 新增 variant 时的分支扩展

- **WHEN** 一个新的 variant 值（如 `"fandom"`）需要在 pipeline 中支持
- **THEN** 开发者 SHALL 在对应的阶段函数中添加 `if variant == "fandom":` 分支
- **AND** SHALL 保持 `standard` 分支的当前行为不变
- **AND** SHALL 确保扩展的变体分支不影响非变体行为

### Requirement: Registry 暴露为可导入模块

The system SHOULD 将 `_STRATEGY_REGISTRY` 从 `orchestrate.py` 的模块级私有变量提升为可被外部模块（如 `bootstrap-strategy` 的 `strategy_scaffold_generator.py`）导入的公共 API。

最低要求：
- 通过 `from ..pipeline.orchestrate import STRATEGY_REGISTRY` 可导入
- 保持 `_STRATEGY_REGISTRY` 作为内部别名的兼容性

#### Scenario: 外部导入 registry

- **WHEN** `strategy_scaffold_generator.py` 需要校验生成的 content_profile ID
- **THEN** 它 SHALL 导入 `from ..pipeline.orchestrate import STRATEGY_REGISTRY`
- **AND** 遍历生成的 `content_profile` 字段，逐个 ID 检查存在性
- **AND** 存在未注册 ID 时停止写入
