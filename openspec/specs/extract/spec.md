# Specification: extract

## Capability 对齐

- Capability: `extract`
- 4 维坐标: `(capability=extract, execution_path=shared, strategy_variant=config_driven, input_format=html)`
- 共享内核: `scripts/lib/extraction/`
  - `preprocessor.py` — 统一 6 步 HTML 预处理（无 context 分支）
  - `infobox.py` — 统一 infobox 提取（BS4 + selectolax 双后端）
  - `converter.py:convert_page_full()` — 4 步编排入口

## 架构声明

```
Extract 能力
├── kernel: lib/extraction/
│   ├── preprocess_html() — 始终全量 6 步
│   ├── extract_infobox() — 双 parser 后端
│   ├── convert_page_full() — 编排: infobox → preprocess → convert → prepend
│   └── 无 context 分支，all paths share same logic
├── variants (站点特定，策略配置驱动):
│   ├── card_stats: scripts/pipeline/converters/card_stats.py
│   └── link_fixer: scripts/pipeline/converters/link_fixer.py
└── 等价证明: tests/pipeline/test_convert_cleanup_consistency.py
```

## 已有行为规范

| 规范 | 内容 |
|------|------|
| `openspec/specs/unified-infobox-extraction/spec.md` | Infobox 提取双后端 + handler dispatch |
| `openspec/specs/unified-html-preprocessing/spec.md` | 6 步预处理管线 |

## ADDED Requirements

### Requirement: preprocessor-no-context-branch

`preprocess_html(html, config)` SHALL always execute the full 6-step cleanup pipeline. The function SHALL NOT accept a `context` parameter or branch between "explore" and "pipeline" execution.

#### Scenario: full-cleanup-always-executed
- **WHEN** any caller invokes `preprocess_html(html, config)`
- **THEN** all 6 cleanup steps SHALL execute
- **AND** output SHALL be identical regardless of execution path

### Requirement: shared-orchestration-entry

`converter.convert_page_full(html, extraction_rules)` SHALL serve as the single shared orchestration entry point for the full extraction pipeline. Explore and pipeline paths SHALL delegate to this function.

#### Scenario: explore-delegates-to-kernel
- **WHEN** `sample_converter.py` applies extraction rules
- **THEN** it SHALL call `convert_page_full()` from the shared kernel
- **AND** SHALL NOT contain its own orchestrator logic
