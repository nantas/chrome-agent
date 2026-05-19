# Pipeline Domain: Registry — Merged Spec

## Source Attribution

| Source Spec | Type |
|------------|------|
| `pipeline-registry` | frozen |
| `pipeline-strategy-schema` | frozen |
| `platform-variant-framework` | frozen |
| `capabilities-derivation` | frozen |
| `pipeline-phase-naming` | frozen |

Paths have been updated to reflect the current directory structure.

---

# Pipeline Registry Specification

## Purpose

Defines the strategy registry as the single source of truth for pipeline strategy IDs, strategy schema validation, platform variant behavior branching, capabilities derivation, and phase file naming conventions.

---

## Requirements

### Requirement: strategy-registry-module

系统 SHALL 将 `_STRATEGY_REGISTRY`、`DEFAULT_STRATEGIES`、`_PROFILE_KEY_MAP`、`PipelineStrategies` dataclass 放在独立模块 `pipeline/registry.py` 中，作为策略注册表的唯一权威来源。

#### Scenario: registry-module-contents
- **WHEN** `pipeline/registry.py` 被创建
- **THEN** 文件包含 `PipelineStrategies` dataclass、`DEFAULT_STRATEGIES` dict、`_STRATEGY_REGISTRY` dict、`_PROFILE_KEY_MAP` dict、公共别名 `STRATEGY_REGISTRY` 和 `PROFILE_KEY_MAP`
- **AND** 文件行数 ≤ 160 行

### Requirement: build-pipeline-factory

系统 SHALL 将 `build_pipeline(strategy, domain)` 函数放在 `pipeline/registry.py`，行为与 `orchestrate.py` 中的实现完全一致。

#### Scenario: build-pipeline-delegation
- **WHEN** 调用 `registry.build_pipeline(strategy, domain)`
- **THEN** 返回 `PipelineStrategies` 实例，无效策略 ID 仍触发 `ValueError`

### Requirement: derive-capabilities-function

系统 SHALL 将 `derive_capabilities(content_profile)` 函数放在 `pipeline/registry.py`。

#### Scenario: derive-capabilities-move
- **WHEN** 调用 `registry.derive_capabilities(content_profile)`
- **THEN** 返回排序后的能力列表

### Requirement: strategy-registry-public-api

系统 SHALL 通过 `pipeline/pipeline/__init__.py` 重新导出 `STRATEGY_REGISTRY`、`PROFILE_KEY_MAP`、`build_pipeline`、`derive_capabilities`、`PipelineStrategies`。

#### Scenario: public-re-exports
- **WHEN** 外部代码通过 `from scripts.pipeline.pipeline import STRATEGY_REGISTRY` 导入
- **THEN** 成功获取与重构前相同的注册表对象

### Requirement: 策略 ID 注册中心权威声明

`pipeline/registry.py` 中的 `_STRATEGY_REGISTRY` dict 是 pipeline 策略 ID 的唯一权威来源。每个 `content_profile` 维度（`discovery_strategy`, `content_acquisition`, `link_resolver`, `template_processor`, `list_page_assembler`）的合法值由对应维度的 key 定义。

#### Scenario: Registry 作为引用完整性依据
- **WHEN** 任何策略文件的 `api.content_profile.*` 字段被修改
- **THEN** 该字段的 value SHALL 在 `_STRATEGY_REGISTRY` 对应 dimension 的 key 集合中存在

### Requirement: 策略文件 ID 引用完整性校验

系统 SHALL 在以下路径上执行完整性校验：
1. Pipeline 启动时（`run_pipeline()` → `build_pipeline()`）：未知 ID → `EXIT_STRATEGY_ERROR`
2. bootstrap-strategy 输出时：写入前校验所有 ID
3. 手动编辑策略文件后：Agent SHALL 先确认 registry 中存在对应 ID

#### Scenario: Pipeline 启动校验 hard-fail
- **WHEN** `build_pipeline()` 检测到未注册 ID
- **THEN** SHALL 记录 `log.error` 并返回 `EXIT_STRATEGY_ERROR`

#### Scenario: bootstrap-strategy 输出前校验
- **WHEN** `strategy_scaffold_generator.generate()` 准备写入
- **THEN** SHALL 检查所有 ID 存在，有未注册 ID 时停止写入

### Requirement: 扩展协议

新增策略实现的必须顺序：
1. 实现 Strategy 类
2. 注册到 `_STRATEGY_REGISTRY` 对应维度的 dict
3. 在策略文件中引用已注册的 ID

严禁在 Step 2 之前执行 Step 3。

#### Scenario: 合规扩展
- **WHEN** 新增 `FandomInfoboxTemplateProcessor`
- **THEN** 先实现类 → 注册 → 再引用

### Requirement: Registry 变更约束

删除或重命名 registry 中的 ID 前 SHALL：
1. 扫描所有 `sites/strategies/*/strategy.md` 确认无引用
2. 更新引用该 ID 的策略文件
3. 同步更新 `sites/templates/` 模板

新增 ID 无此约束。

### Requirement: homepage-exclude-categories-field

策略文件 `api.homepage` 配置块 SHALL 支持可选字段 `exclude_categories: list[str]`。缺失或空列表时不过滤。该字段仅影响 homepage-driven discovery，不影响 allpages discovery。

### Requirement: exclude-categories-backward-compatible

新增 `api.homepage.exclude_categories` 字段 SHALL 不破坏已有策略文件的解析和运行。

### Requirement: exclude-categories-not-applicable-to-allpages

`api.homepage.exclude_categories` 字段 SHALL 仅影响 homepage-driven discovery（原 Phase 0）。allpages discovery（原 Phase A）SHALL 不读取此字段。

### Requirement: platform_variant 声明字段

策略文件的 `api` 对象中可选声明 `platform_variant` 字段。受控词汇表：

| 值 | 描述 |
|------|------|
| `fandom` | Fandom-hosted MediaWiki |
| `wiki-gg` | wiki.gg-hosted MediaWiki |
| `standard` | 标准 MediaWiki（默认值） |

未指定时默认为 `standard`。

#### Scenario: variant 默认值
- **WHEN** 策略文件未指定 `api.platform_variant`
- **THEN** pipeline SHALL 使用 `standard`，行为与当前一致

### Requirement: Variant 行为分支接口

系统 SHALL 在 pipeline 中根据 `platform_variant` 值选择行为分支：
1. discovery 阶段：Fandom variant 增加页面存在性验证和翻译页排除
2. fetch/convert 阶段：Fandom variant 捕获 `PageNotFoundError` 返回 `status: "skipped"`
3. assemble 阶段：不同 variant 应用不同的 HTML 清理规则

### Requirement: Variant 注册扩展

新增 variant 值需要：注册新 ID → 定义行为分支条件 → 更新模板映射 → 在代码中增加分支。

### Requirement: derive-capabilities-from-content-profile

系统 SHALL 提供公共函数 `derive_capabilities(content_profile: dict) -> list[str]`，根据 content_profile 中声明的策略 ID 推导出 pipeline 所需的 capabilities 列表。

推导逻辑：对 `discovery` 和 `content_acquisition` 两个维度实例化对应策略类，读取 `required_capabilities` 属性，取并集，返回排序列表。

#### Scenario: derive-from-fandom-content-profile
- **WHEN** content_profile 包含 Fandom 特定策略 ID
- **THEN** 返回 `["category_lookup", "html_parse", "page_list"]`

#### Scenario: derive-from-default-empty-profile
- **WHEN** content_profile 为空 dict
- **THEN** 使用 DEFAULT_STRATEGIES，返回 `["category_lookup", "page_list", "wikitext_parse"]`

### Requirement: derive-capabilities-public-api

`derive_capabilities` 函数 SHALL 通过 `registry.py` 导出为公共 API，供 `strategy_scaffold_generator.py` 和其他外部消费者使用。

### Requirement: derive-capabilities-robustness

当 content_profile 引用不在 `_STRATEGY_REGISTRY` 中的策略 ID 时，`derive_capabilities` SHALL 抛出 `ValueError`。

### Requirement: phase-file-naming-alignment

Phase 文件 SHALL 按实际功能命名：`discovery_homepage.py`、`discovery_allpages.py`、`fetch.py`、`convert.py`、`assemble.py`。

#### Scenario: phase-file-discovery
- **WHEN** 开发者浏览 `pipeline/pipeline/phases/` 目录
- **THEN** 文件名直接反映功能

### Requirement: phase-b-function-consolidation

`phase_b.py` 中的活跃函数 SHALL 被内化到对应的 phases 文件中，消除跨文件反向导入。

#### Scenario: fetch-single-page-colocation
- **WHEN** `phases/fetch.py` 需要调用 `fetch_single_page`
- **THEN** 函数定义在同一文件中

### Requirement: dead-code-removal

`phase_b.py` 中无外部调用方的函数 SHALL 被删除。`scripts/pipeline/phase_{a,b,c}.py` 顶层文件零外部引用时 SHALL 被删除。

### Requirement: RENAMED phase files

以下 phase 文件命名映射 SHALL 生效：
- `phase_0` → `discovery_homepage`（在文件引用/路径中）
- `phase_a` → `discovery_allpages`
- `phase_b` → `fetch` + `convert`
- `phase_c` → `assemble`

注意：`run_phase_0()`、`run_phase_a()` 等函数名在 prose 中保持原样不变。
