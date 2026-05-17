# Design: Explore Architecture Gate

## Overview

Architecture Gate 是 explore 工作流中插入在 Phase 1 (Sample Self-Check) 和 Phase 4 (User Confirmation) 之间的独立校验阶段。它由一组可编程检查（schema validation）和一个人工审计清单（agent audit）组成。

## 工作流位置

```
Phase 0: Explore & Discovery (existing)
  ├── engine chain probe
  ├── API discovery
  ├── structure mapping
  ├── protection identification
  └── strategy scaffold generation

Phase 1: Sample Conversion & Self-Check (existing)
  ├── select samples (2-6 per content type)
  ├── fetch + convert using extraction_rules
  ├── run S1-S12 self-checks on ALL samples
  ├── auto-remediation (max 2 iterations)
  └── present self-check summary

Phase 2: Architecture Gate [NEW]
  ├── Check 1: Strategy → Pipeline schema validation
  ├── Check 2: Pipeline → Strategy audit
  └── output: gate_result {status, violations[]}

        ↓ (gate must pass before → Phase 4)

Phase 3: KI Lifecycle (NEW — see explore-ki-lifecycle)
  ├── classify KIs by owner domain
  ├── prioritize (P0-P3)
  ├── fix in priority order (max 3 iterations)
  └── full retest after each fix

Phase 4: User Confirmation & Freeze (existing)
  ├── present final samples + gate result + KI status
  ├── user validates quality
  ├── freeze strategy
  └── update registry
```

## Check 1: Strategy → Pipeline Schema Validation (程序化)

### 实现方式

在 `scripts/explore/` 下新增 `architecture_gate.py`，提供 `validate_strategy_to_pipeline(strategy_yaml: dict, pipeline_source: str) -> dict` 函数。

### 校验逻辑

对 strategy 的 `extraction` 块中每个顶层 key，验证 pipeline 代码中存在对应的消费模式：

| Strategy Key | Pipeline Consumer Pattern | 校验方法 |
|-------------|--------------------------|---------|
| `infobox` | `cfg.get("infobox")` or `infobox_cfg` | 检查 `extraction_rules.get("infobox")` 或等效读取 |
| `lazyload` | `cfg.get("lazyload")` | 同上 |
| `url_conversion` | `cfg.get("url_conversion")` | 同上 |
| `youtube_cleanup` | `cfg.get("youtube_cleanup")` | 同上 |
| `cleanup_selectors` | 遍历 `cfg.get("cleanup_selectors")` | 同上 |
| `image_filtering.skip_patterns` | 遍历 `cfg.get("image_filtering").get("skip_patterns")` | 同上 |
| `cleanup` (operations list) | `if "op" in cleanup:` | 检查枚举式消费 |
| `text_normalization` | `if "op" in normalization:` | 同上 |
| `infobox_field_handlers` | `if "handler" in handlers:` | 同上 |

### 死配置检测

```python
def detect_dead_config(strategy: dict, pipeline_path: str) -> list[str]:
    """Return list of strategy fields with no pipeline consumer."""
    with open(pipeline_path) as f:
        source = f.read()
    
    dead = []
    for key in strategy.get("extraction", {}):
        if key not in _ALWAYS_CONSUMED:
            # Check if pipeline source references this key
            pattern = rf'\.get\("{key}"\)|\["{key}"\]|cfg\[.?"{key}"\]'
            if not re.search(pattern, source):
                dead.append(key)
    return dead
```

## Check 2: Pipeline → Strategy Audit (Agent 执行)

### 审计清单

Agent 在每次 strategy/pipeline 修改后必须执行以下审计：

| # | 检查项 | 检测方法 | 违规示例 |
|---|-------|---------|---------|
| A | HTML 选择器硬编码 | `grep '".*"' scripts/explore/sample_converter.py \| grep -i 'class\|selector\|#\|\.'` | `"aside.portable-infobox"` — 应来自 `infobox.selector` |
| B | CSS 类名硬编码 | 同上，聚焦类选择器格式 | `"nav-box"`, `"nav-main"` — 应来自 `cleanup_selectors` |
| C | 站点域名硬编码 | `grep -r 'wiki\.gg\|fandom\.com\|bindingofisaac' scripts/explore/` | `"bindingofisaacrebirth.wiki.gg"` — 应来自 `image_handling.base_url` |
| D | 文件名模式硬编码 | `grep 'skip_patterns\|Icon_mini\|MainPage' scripts/explore/` | `"Icon_mini.png"` — 应来自 `image_filtering.skip_patterns` |
| E | 无条件执行站点操作 | 代码审查：YouTube/URL转换/lazyload 是否有 `if cfg["enabled"]` 守卫 | `re.sub(YouTube...)` 无守卫 — 应包裹在 `if yt_cfg["enabled"]:` 内 |

### 审计结果格式

```python
{
    "status": "pass" | "fail",
    "violations": [
        {
            "type": "hardcoded_selector" | "dead_config" | "unconditional_op",
            "detail": "具体描述",
            "location": "文件名:行号",
            "remediation": "应改为从 strategy.xxx 读取"
        }
    ]
}
```

## Gate 输出格式

```json
{
    "architecture_gate": {
        "status": "pass" | "fail",
        "strategy_to_pipeline": {
            "status": "pass" | "fail",
            "dead_config": ["field_name_1", ...]
        },
        "pipeline_to_strategy": {
            "status": "pass" | "fail", 
            "violations": [
                {"type": "hardcoded_selector", "detail": "...", "location": "..."}
            ]
        }
    }
}
```

## Agent 行为规则

1. Architecture Gate **MUST** pass before user confirmation phase
2. If Gate fails:
   - Agent **MUST** fix all violations before presenting to user
   - Violations fix **does NOT** count toward the 3-iteration limit (iterations are for quality issues, not architecture violations)
   - After fixing violations, agent **MUST** re-run full sample conversion + self-check
3. Gate result **MUST** be included in the final explore output presented to user
