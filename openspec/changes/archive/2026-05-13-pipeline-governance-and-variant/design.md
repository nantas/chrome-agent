# Design

## Context

Neon Abyss Fandom Wiki crawl 暴露了 7 个问题（P1-P7），其中 3 个根因指向开发治理工作流缺陷：

1. **策略文件可引用不存在的 registry ID** — `content_profile.link_resolver: "short_name"` 在 `_STRATEGY_REGISTRY` 中无对应条目，但 pipeline 仅 warning + 降级
2. **change 之间无跨平台假设追踪** — `html-rendered-wiki-crawl` 在 wiki.gg 上验证，未记录对 Fandom 的兼容假设
3. **扩展顺序颠倒** — 策略文件先引用未实现的 ID，后考虑注册实现

Specs 定义了三个层面的治理方案：
- `pipeline-strategy-schema`：注册中心契约层，包括 ID 引用完整性校验、扩展协议、变更约束
- `platform-variant-framework`：MediaWiki 平台变体（Fandom、wiki.gg、standard）的行为分支框架
- 三个 modified specs：site-strategy（策略文件 schema 扩展）、agents-governance（AGENTS.md 新增章节）、mediawiki-api-extraction-pipeline（启动校验 + 变体传递）

本 design 定义技术实现方案和变更位置。

## Goals / Non-Goals

**Goals:**
- 在 `build_pipeline()` 中增加 content_profile ID 的 hard-fail 校验（spec: `pipeline-strategy-schema`）
- 将 `_STRATEGY_REGISTRY` 暴露为可导入的公共 API（spec: `mediawiki-api-extraction-pipeline`）
- 在 `strategy_scaffold_generator.generate()` 中增加 registry 校验（spec: `pipeline-strategy-schema`）
- 在 `run_pipeline()` 中增加 `platform_variant` 解析与传递（spec: `platform-variant-framework`）
- 更新 AGENTS.md 新增 Pipeline Strategy Schema 治理章节（spec: `agents-governance`）
- 更新 `site-strategy-schema` 主 spec 同步新增字段和约束（spec: `site-strategy`）

**Non-Goals:**
- 不实现 Fandom 变体的具体行为分支（missingtitle 处理、Phase A 过滤、HTML 清理）— 留给后续管线修复 change
- 不修改 `_STRATEGY_REGISTRY` 的数据结构（保持三层 dict）
- 不新增或移除 registry 中的 ID（仅增加治理约束）
- 不耦合 openspec 工作流程（治理约束直接写入 AGENTS.md）
- 不修改 Pipeline 的 Phase A/B/C 核心执行逻辑

## Decisions

### Decision 1: Registry 校验位置

**选择**：在 `build_pipeline()` 函数中增加 schema 校验，在 `validate_api_config()` 之前执行。

**理由**：
- `build_pipeline()` 已负责从 content_profile ID 解析到策略类实例
- 在此函数中增加校验，就可以在类构造失败前就检测到无效 ID
- 与现有的 `validate_api_config()` 自然衔接

**实现**：
```python
def build_pipeline(strategy: dict, domain: str = "") -> PipelineStrategies:
    content_profile = strategy.get("api", {}).get("content_profile", {})
    
    # Schema validation: check all content_profile IDs against registry
    for field, (default_id, _) in DEFAULT_STRATEGIES.items():
        profile_key = _get_profile_key(field)
        requested_id = content_profile.get(profile_key, default_id) if profile_key else default_id
        if profile_key and profile_key in content_profile:
            registry = _STRATEGY_REGISTRY.get(field, {})
            if requested_id not in registry:
                raise ValueError(
                    f"Strategy ID '{requested_id}' not registered in '{field}'. "
                    f"Available: {list(registry.keys())}"
                )
    
    # ... existing strategy resolution logic
```

`run_pipeline()` 捕获 `ValueError` 并返回 `EXIT_STRATEGY_ERROR`。

### Decision 2: Registry 导出为公共 API

**选择**：在 `orchestrate.py` 模块级别定义一个公共的 `STRATEGY_REGISTRY` 变量引用私有的 `_STRATEGY_REGISTRY`。

**理由**：
- 保持私有命名 `_STRATEGY_REGISTRY` 作为内部约定
- 通过别名 `STRATEGY_REGISTRY` 向后兼容导出

**实现**：
```python
# Module-level private (internal usage)
_STRATEGY_REGISTRY = { ... }

# Public API for external consumers (bootstrap-strategy, validation)
STRATEGY_REGISTRY = _STRATEGY_REGISTRY
```

### Decision 3: bootstrap-strategy 校验入口

**选择**：在 `strategy_scaffold_generator.generate()` 中导入 `STRATEGY_REGISTRY`，在生成 content_profile 后校验所有 ID。

**理由**：
- `strategy_scaffold_generator.py` 是 bootstrap 策略文件的唯一输出点
- 在此处校验确保任何模板生成的 content_profile 都会经过验证
- 模板文件本身可以安全地引用 registry 中存在的 ID

**实现**：
```python
from ..pipeline.orchestrate import STRATEGY_REGISTRY  # after repo_root resolution

# After building scaffold, before writing:
profile = scaffold.get("api", {}).get("content_profile", {})
for field_key, id_value in profile.items():
    # Map profile key to registry dimension
    dimension = _PROFILE_KEY_MAP_REVERSE.get(field_key)
    if dimension and dimension in STRATEGY_REGISTRY:
        if id_value not in STRATEGY_REGISTRY[dimension]:
            raise ValueError(
                f"Cannot scaffold strategy: content_profile.{field_key}='{id_value}' "
                f"not registered in '{dimension}'. Available: {list(STRATEGY_REGISTRY[dimension].keys())}"
            )
```

注意：`strategy_scaffold_generator.py` 当前生成的策略文件不含 `content_profile` 字段（模板未包含），所以校验在当前状态下不会触发失败。但 future-proof 部署：当模板开始包含 content_profile 时，校验自动生效。

### Decision 4: platform_variant 传递

**选择**：在 `run_pipeline()` 的 "Probe API endpoint" 阶段之后解析 `platform_variant`，并以参数或 `strategy` dict 注入方式传递给 `run_phase_a()` 和 `run_phase_b()`。

**理由**：
- 这是信息流的中枢点，variant 值需要被所有阶段用到
- 通过参数传递比 global/context 变量更明晰

**实现**：
```python
# After strategy parsing and before phases:
platform_variant = strategy.get("api", {}).get("platform_variant", "standard")
log.info("Platform variant: %s", platform_variant)

# Pass to phase functions:
manifest = run_phase_a(client, strategy, origin, strategies.discovery, platform_variant)
results, stats = run_phase_b(
    client, manifest, strategy, rate_limit_config, domain,
    strategies.content_acquisition, strategies.link_resolver,
    strategies.template_processor, platform_variant
)
```

Phase A 和 Phase B 的函数签名增加可选的 `platform_variant` 参数。当前阶段仅接受参数、记录日志，不实现行为分支。

### Decision 5: AGENTS.md 治理文本嵌入

**选择**：在 AGENTS.md 的 Section 7（策略库治理）之后新增一个子章节 `### Pipeline Strategy Schema 治理`。

**理由**：
- 策略库治理（Section 7）已涵盖策略文件的管理规则
- Pipeline Strategy Schema 治理是策略文件 schema 层面的约束扩展
- 作为子章节保持两层间的逻辑关联性

**内容结构**：
```markdown
### Pipeline Strategy Schema 治理

#### 权威来源
`scripts/mediawiki-api-extract/pipeline/orchestrate.py` 中的 `_STRATEGY_REGISTRY` 是策略 ID 的唯一权威来源。

（详细约束见 pipeline-strategy-schema spec）

#### 策略文件约束
（约束内容）

#### 扩展协议
（协议内容）

#### 当前注册 ID 清单
| 维度 | 合法 ID |
|------|---------|
| discovery | allpages, category_members |
| content_acquisition | wikitext_only, hybrid_wikitext_plus_rendered, html_rendered |
| ... | ... |

#### Registry 变更约束
（变更约束）
```

### Decision 6: site-strategy-schema 主 spec 同步

**选择**：在 `openspec/specs/site-strategy-schema/spec.md` 中增加 `platform_variant` 字段定义和 `content_profile` 引用约束。

**理由**：
- `site-strategy-schema` 是策略文件 schema 的真源 spec
- 所有新增的字段和约束都需要同步到主 spec

## Risks / Migration

### Risk 1: Hard-fail 可能阻塞现有策略文件的 crawl

**风险**：如果已有策略文件引用了未注册的 ID，在升级 pipeline 后所有 crawl 调用会立即失败，包括那些之前可以"降级运行"的策略。

**缓解**：
- 本 change 的范围调查现有策略文件（neonabyss.fandom.com）的 content_profile 引用情况
- 本 change 仅在实现校验前清理或更新受影响策略的 content_profile
- 管线修复 change 中补全缺失的 registry ID 或修正策略文件引用

### Risk 2: STRATEGY_REGISTRY 公共导出引入耦合

**风险**：将 registry 从模块私有变为公共 API 后，外部代码可能依赖其内部结构，限制后续的重构自由度。

**缓解**：
- 导出的 `STRATEGY_REGISTRY` SHALL 为只读引用
- `strategy_scaffold_generator.py` SHALL 不做结构假定（仅遍历 key）
- 未来 registry 的数据类型变更需审计所有导入者

### Risk 3: platform_variant 的默认值影响现有策略

**风险**：现有策略文件没有 `platform_variant` 字段，默认 `standard`。这不会改变当前行为，但可能会让未来 pipeeline 对 Fandom 策略应用了 `standard` 变体的行为。

**缓解**：
- 排查现有策略文件，对 Fandom 站点的策略文件（如 `neonabyss.fandom.com`）手动增加 `platform_variant: fandom`
- 这属于管线修复 change 的范围，非本 change
