# pipeline-strategy-schema Specification

## Purpose
TBD - created by archiving change pipeline-governance-and-variant. Update Purpose after archive.
## Requirements
### Requirement: 策略 ID 注册中心权威声明
The system SHALL declare `scripts/mediawiki-api-extract/pipeline/orchestrate.py` 中的 `_STRATEGY_REGISTRY` dict 作为 pipeline 策略 ID 的唯一权威来源。

每个 `content_profile` 维度（`discovery_strategy`, `content_acquisition`, `link_resolver`, `template_processor`, `list_page_assembler`）的合法值由 `_STRATEGY_REGISTRY` 中对应维度的 key 定义。

`_STRATEGY_REGISTRY` 的结构为三层嵌套 dict：
```
_STRATEGY_REGISTRY = {
    "<dimension>": {
        "<id>": <StrategyClass>,
        ...
    },
    ...
}
```

其中 `<dimension>` 对应 `content_profile` 的字段名，`<id>` 是该字段唯一可引用的合法值。

#### Scenario: Registry 作为引用完整性依据
- **WHEN** 任何策略文件的 `api.content_profile.*` 字段被修改
- **THEN** 该字段的 value SHALL 在 `_STRATEGY_REGISTRY` 对应 dimension 的 key 集合中存在
- **AND** 不存在时 SHALL 被视为引用完整性错误

### Requirement: 策略文件 ID 引用完整性校验
The system SHALL 在以下三条路径上对策略文件的 `content_profile` ID 引用执行完整性校验：

1. **Pipeline 启动时**（`run_pipeline()` → `build_pipeline()`）：未知 ID SHALL 导致 `log.error` + `return EXIT_STRATEGY_ERROR`，不得仅 warning 降级
2. **bootstrap-strategy 输出时**（`strategy_scaffold_generator.generate()`）：写入策略文件前 SHALL 校验所有 `content_profile` ID 在 registry 中存在；不通过 SHALL 停止写入并报告缺失 ID
3. **手动编辑策略文件后**（Agent 约束）：agent 编辑 `content_profile` 后 SHALL 先确认 registry 中存在对应 ID 再保存

#### Scenario: Pipeline 启动校验 hard-fail
- **WHEN** pipeline 启动时 `build_pipeline()` 检测到策略文件引用了一个未在 `_STRATEGY_REGISTRY` 中注册的 ID（如 `link_resolver: "short_name"`）
- **THEN** SHALL 记录 `log.error("Strategy ID '%s' not registered in %s", id, dimension)`
- **AND** SHALL 返回 `EXIT_STRATEGORY_ERROR` 退出码
- **AND** SHALL 不执行任何后续管线阶段

#### Scenario: Pipeline 降级已弃用
- **WHEN** strategy 引用的是已注册的有效 ID（如 `link_resolver: "exact_title_match"`）
- **THEN** SHALL 正常使用该策略实现
- **AND** SHALL 不触发错误或警告
- **AND** "未注册 ID 降级使用默认"的行为 SHALL 被废弃

#### Scenario: bootstrap-strategy 输出前校验
- **WHEN** `strategy_scaffold_generator.generate()` 准备写入生成的策略文件
- **THEN** SHALL 检查生成的 `content_profile` 中每个 ID 是否在 `_STRATEGY_REGISTRY` 中
- **AND** 存在未注册 ID 时 SHALL 停止写入，输出错误信息包含缺失的 ID 列表
- **AND** SHALL 不写入不完整的策略文件

### Requirement: 扩展协议
The system SHALL 定义策略扩展的严格顺序约束。

新增策略实现（策略类 + registry 注册 + 策略文件引用）的必须顺序：

```
Step 1: 实现 Strategy 类（继承或实现对应接口 Protocol）
Step 2: 注册到 _STRATEGY_REGISTRY 对应维度的 dict 中
Step 3: 在策略文件中引用已注册的 ID
```

严禁在 Step 2（注册）之前执行 Step 3（策略文件引用）。违反此顺序的策略文件引用 SHALL 被 pipeline 的启动校验拒绝。

#### Scenario: 合规扩展
- **WHEN** 需要新增一个 `FandomInfoboxTemplateProcessor`
- **THEN** 开发者 SHALL 先实现 `FandomInfoboxTemplateProcessor` 类
- **AND** 再在 `_STRATEGY_REGISTRY["template_processor"]` 中注册 `"fandom_infobox": FandomInfoboxTemplateProcessor`
- **AND** 然后在策略文件中引用 `template_processor: "fandom_infobox"`
- **AND** pipeline SHALL 正常通过启动校验

#### Scenario: 违规扩展被拒绝
- **WHEN** 策略文件引用了 `template_processor: "fandom_infobox"` 但 `_STRATEGY_REGISTRY` 中无此 ID
- **THEN** pipeline 启动校验 SHALL 失败并返回 `EXIT_STRATEGY_ERROR`
- **AND** 错误信息 SHALL 明确指出 `fandom_infobox` 未注册

### Requirement: Registry 变更约束
The system SHALL 定义 `_STRATEGY_REGISTRY` 的删除和重命名的约束规则。

删除或重命名 registry 中的 ID 前 SHALL：
1. 扫描所有 `sites/strategies/*/strategy.md` 确认无策略文件引用该 ID
2. 更新任何引用该 ID 的策略文件
3. 同步更新 `sites/templates/` 中的模板文件（如模板包含该 ID）

新增 registry ID 无此约束（新增是向后兼容的）。

#### Scenario: 安全删除
- **WHEN** 从 `_STRATEGY_REGISTRY["link_resolver"]` 中删除 `"exact_title_match"`
- **THEN** 开发者 SHALL 先 grep 所有策略文件确认无人引用
- **AND** SHALL 更新任何引用该 ID 的策略文件
- **AND** 删除后 pipeline SHALL 能正常启动

#### Scenario: 安全新增
- **WHEN** 向 `_STRATEGY_REGISTRY["content_acquisition"]` 新增 `"hybrid_wikitext_plus_rendered"`
- **THEN** 无需扫描策略文件
- **AND** 新增 ID SHALL 立即可在策略文件中引用
