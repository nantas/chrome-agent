# Design

## Context

当前 `scripts/mediawiki-api-extract` 是 1292 行的单体 Python 脚本，所有管线逻辑（API 调用、链接解析、模板展开、表格转换、输出组装）在同一个命名空间中相互调用。站点差异只能通过 Python 代码分支处理，没有策略抽象层。

上游改善方案文档（`chrome-agent-mediawiki-extraction-improvement-plan.md`）将总规划拆为两个 change：
- **Change 1（本 change）**：策略组合架构重构——提取策略接口 + 默认实现 + 管线注入，不新增行为
- **Change 2**：StS2 复杂站点策略集——新增策略实现，修复现有缺陷

本 change 的 specs 定义了两个 MODIFIED capability：
- `mediawiki-api-extraction`：新增 capabilities 受控词汇表、5 个策略接口契约、namespace 策略化、管线核心流程与挂载点描述
- `mediawiki-site-strategy`：新增 `api.content_profile` schema + capabilities 引用说明

## Goals / Non-Goals

**Goals:**

1. 将 1292 行单体脚本拆分为职责清晰的模块包（`scripts/mediawiki-api-extract/`）
2. 定义 5 个策略接口（Protocol classes）：DiscoveryStrategy、ContentAcquisitionStrategy、LinkResolver、TemplateProcessor、ListPageAssembler
3. 为每个策略接口提供默认实现，行为与重构前完全一致
4. 建立 pipeline 编排层（`pipeline.py`），负责策略组装与 capabilities 验证
5. 更新 `validate_api_config`，使用策略声明的 `required_capabilities` 替代硬编码集合
6. 将 capabilities 受控词汇表写入 spec
7. balatro 爬取输出与重构前逐文件一致

**Non-Goals:**

- 不修复任何现有缺陷（短名链接、括号正则、路径计算、DPL 表格、DRUID 图片）
- 不新增任何外部行为
- 不新增 StS2 策略实现（Change 2 范围）
- 不新增 L6 验证质量层
- 不新增引擎或 CLI 命令
- 不改动 Scrapling 管线或 crawl/routing 逻辑

## Decisions

### 1. 策略接口风格：Protocol classes

**选择理由**：类型安全、IDE 自动补全支持、与 mypy 静态检查兼容。相比 dict-based 插件注册，Protocol 提供了明确的契约签名。

**约束**：
- 每个 Protocol 只定义方法签名，默认实现通过独立类提供
- Protocol 不接受 `@abstractmethod`（那是 ABC 的用法），而是通过 `typing.Protocol` 的 structural subtyping

### 2. 模块拆分：扁平模块，不嵌套子包

```
scripts/mediawiki-api-extract/
├── __init__.py
├── __main__.py        # CLI entry + argument parsing
├── client.py          # ApiClient + probe_api_endpoint
├── strategies.py      # Strategy Protocols + default implementations + helpers
├── phase_a.py         # Phase A: page discovery
├── phase_b.py         # Phase B: content extraction
├── phase_c.py         # Phase C: output assembly
└── pipeline.py        # Pipeline composition + validation + orchestration
```

**选择理由**：5-7 个文件足够表达职责边界，不需要额外的子目录层级。CLI 入口变化：从 `python scripts/mediawiki-api-extract` 变为 `python -m scripts.mediawiki-api-extract`。

### 3. 策略挂载设计

每 Phase 的 `run_phase_*` 函数接受策略对象作为参数，不从全局状态读取：

```python
def run_phase_a(client, strategy_dict, discovery_strategy: DiscoveryStrategy) -> dict: ...
def run_phase_b(client, manifest, strategy_dict, content_strategy, link_resolver, template_processor) -> tuple: ...
def run_phase_c(output_dir, manifest, results, strategy_dict, list_page_assembler, link_resolver) -> dict: ...
```

Phase B 内 `convert_wikitext_to_markdown` 接受 `link_resolver` 和 `template_processor` 作为参数，由 `run_phase_b` 传入。

### 4. `convert_wikitext_to_markdown` 的位置

该函数保留在 `phase_b.py` 中（因其是 Phase B 的核心转换逻辑），但通过参数接受策略对象。不将其迁移到 `strategies.py`。

### 5. 表格转换的处理

`convert_wikitable_to_markdown` 及辅助函数保留为 `strategies.py` 中的模块级函数（非策略）。当前设计不将其抽象为独立策略接口，因为 MW 表格转换是纯机械操作，不因站点而异。

### 6. `validate_api_config` 重构

改为读取 `PipelineStrategies` 中各策略的 `required_capabilities` 属性，与其并集对比策略声明的 `api.capabilities`。签名变为：

```python
def validate_api_config(api_config: dict | None, strategies: PipelineStrategies) -> str | None:
```

当 `api_config` 为 None 时，返回 `"Strategy has no 'api' field"`（与现有行为一致）。

### 7. 全局变量 `SOURCE_DOMAIN` 消除

当前 `phase_b.py` 使用全局变量 `SOURCE_DOMAIN` 传递域名给 `convert_wiki_links`。重构后改为通过函数参数传递，由 `run_phase_b` 传入。

### 8. `content_profile` 可选性

策略文件的 `api.content_profile` 是可选的。`build_pipeline` 在缺少该字段时使用默认策略。这在 Change 1 中允许 balatro 策略不声明任何新字段仍能正常工作，同时为 Change 2 的 StS2 策略预留声明空间。

## Risks / Migration

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| **CLI 入口路径变化** | 现有 shell alias / scripts 调用 `scripts/mediawiki-api-extract` 会失效 | 提供兼容性 symlink；AGENTS.md 更新为 `python -m` 用法 |
| **回归测试依赖网络** | 基线生成需要 balatro API 可用 | 执行前检查；如果 API 不可用，保存已知好的基线快照 |
| **全局变量消除引入 bug** | `SOURCE_DOMAIN` 改为参数传递可能导致遗漏调用路径 | 仔细审查所有 `convert_wiki_links`、`convert_wikitable_to_markdown` 的调用链 |
| **策略接口定义太宽泛** | 后续新增策略时可能发现接口签名不够用 | 保持 Protocol 可扩展（使用 `**kwargs` 或宽松的类型签名）；Change 2 调整签名是可接受的 |
| **`import yaml` 位置** | 当前在 `main()` 中 lazy import，重构后需要在 `__main__.py` 的 `main()` 中保留 | 明确在 `__main__.main()` 中处理，不在模块顶层导入 |
