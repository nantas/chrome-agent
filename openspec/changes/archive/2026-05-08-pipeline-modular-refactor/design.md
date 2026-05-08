# Design

## Context

`scripts/mediawiki-api-extract/` 当前是 8 个文件的扁平包，其中 `strategies.py` 占 85KB / 2172 行，包含策略接口、6 个策略实现、`HtmlToMarkdownConverter`、`convert_wikitext_to_markdown`、`extract_card_stats`、`split_card_list_pages`、验证函数及多个辅助函数。所有模块通过相对导入互相依赖，无法从包外独立使用任何转换器。

本次变更的目标是将这个单体包拆分为三层子包（converters / strategies / pipeline），修复 CLI 入口，新增独立操作入口和 CLI 子命令，同时保持全量管线输出不变。

## Goals / Non-Goals

**Goals:**
- 转换器可被外部脚本直接 import，无需管线上下文
- 支持单页面 fetch/convert、增量 reprocess、链接修复三种独立操作
- 修复 `__main__.py` 和 `chrome-agent-cli.mjs` 的调用方式
- 全量管线输出不变（逐字节一致）

**Non-Goals:**
- 不改变 MediaWiki API 调用协议或返回格式
- 不新增引擎注册条目
- 不重构 `client.py` 的重试逻辑或 `phase_a.py` 的 discovery 逻辑
- 不改动 `configs/engine-registry.json`

## Decisions

### D1: converters/ 子包零管线依赖

**决策**：`converters/` 下的模块不得 import `client`、`pipeline`、`phase_*`。

**理由**：核心诉求是独立使用。`HtmlToMarkdownConverter` 本身只依赖 `selectolax`（可选）和 `re`，不应引入 API 客户端依赖。`convert_wikitext_to_markdown` 接受策略实例作为参数注入，不直接导入策略类。

**实现**：
- `converters/html_to_markdown.py`：从 `strategies.py` 搬出 `HtmlToMarkdownConverter` 及其私有方法
- `converters/wikitext_to_md.py`：搬出 `convert_wikitext_to_markdown`、`convert_wikitable_to_markdown`、`_parse_wikitable_block`、`_split_table_cells`、`_clean_table_cell`、`_split_templates`、`_replace_dpl_template`
- `converters/card_stats.py`：搬出 `extract_card_stats`、`split_card_list_pages`
- `converters/__init__.py`：re-export 所有公开类和函数

### D2: strategies/ 按角色拆分

**决策**：5 个策略角色各自独立文件。

**映射**：
| 文件 | 类 |
|------|-----|
| `strategies/discovery.py` | `AllPagesDiscoveryStrategy`, `CategoryMembersDiscoveryStrategy` |
| `strategies/acquisition.py` | `WikitextOnlyAcquisitionStrategy`, `HybridAcquisitionStrategy`, `HtmlRenderedAcquisitionStrategy` |
| `strategies/link_resolver.py` | `ExactTitleLinkResolver`, `ShortNameLinkResolver` |
| `strategies/template.py` | `SimpleSubstitutionTemplateProcessor`, `StructuredTemplateProcessor` |
| `strategies/list_assembler.py` | `FrontmatterDrivenListPageAssembler`, `HybridListPageAssembler` |

`strategies/__init__.py` 做 re-export，保持 `from .strategies import X` 兼容。Protocol 定义放在 `strategies/__init__.py`。

### D3: pipeline/ 子包提取编排逻辑

**决策**：`pipeline.py` 拆分为 `pipeline/orchestrate.py`（`run_pipeline`、`build_pipeline`、`parse_strategy`）、`pipeline/rate_limit.py`（`RateLimitConfig`、`resolve_rate_limit_config`）和 `pipeline/__init__.py`（re-export）。

**理由**：`pipeline.py` 约 430 行，混合了策略工厂、速率限制配置和管线编排。拆分后各文件 < 200 行，职责更清晰。

### D4: standalone.py 独立操作入口

**决策**：新增 `standalone.py`，提供 `fetch_and_convert`、`reconvert_file`、`reprocess_pages` 三个顶层函数。

**依赖**：可 import `client`（需要 `ApiClient` 做网络请求）、`converters`（做转换）、`pipeline/orchestrate`（用 `parse_strategy` 解析策略配置）。不可 import `phase_*`（直接复用 converters 而非走 phase 流程）。

### D5: CLI 子命令路由

**决策**：新增 `cli.py`，使用 `argparse` 子命令路由。`__main__.py` 简化为调用 `cli.main()`。

**子命令**：
- `pipeline`（默认）：全量管线，复用现有 `run_pipeline`
- `fetch`：单页面获取
- `reprocess`：增量补救
- `fix-links`：链接修复
- `reconvert`：单文件重转换

**向后兼容**：无子命令时（位置参数为 URL）默认走 `pipeline`，保持现有调用方式不变。

### D6: __main__.py sys.path 修复

**决策**：在 `__main__.py` 顶部增加 `sys.path` 修复，使 `python3 scripts/mediawiki-api-extract` 等价于 `python3 -m scripts.mediawiki_api_extract`。

```python
if __name__ == "__main__" and __package__ is None:
    _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _parent not in sys.path:
        sys.path.insert(0, _parent)
    __package__ = "scripts.mediawiki_api_extract"
```

### D7: chrome-agent-cli.mjs 调用方式修正

**决策**：将 `spawnSync` 的参数从 `[目录路径, url, ...]` 改为 `["-m", "scripts.mediawiki_api_extract", url, ...]`。

**注意**：使用下划线 `mediawiki_api_extract`（Python import 路径），而非连字符 `mediawiki-api-extract`（目录名）。

## Risks / Migration

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 拆分时 import 链断裂 | 管线无法运行 | 先创建 `strategies.py` 兼容 shim（全部 re-export），验证管线正常运行后再删除 shim |
| `phase_b.py` / `phase_c.py` 的 import 路径变更 | 导入失败 | 通过 `strategies/__init__.py` re-export 保持 `from .strategies import X` 兼容 |
| `convert_wikitext_to_markdown` 签名复杂（8 参数） | 新便捷函数难以封装 | 保持原签名不变，`standalone.py` 中用默认策略封装便捷版本 |
| `chrome-agent-cli.mjs` 修改影响 Scrapling fallback | CLI 路由全断 | 修改仅影响 MediaWiki API 分支，Scrapling 路径不受影响；修改后对已知站点做端到端验证 |
| 缺少自动化测试 | 重构引入回归 | 每个 task 完成后用 slaythespire.wiki.gg 的有限页面做 smoke test（3-5 个页面） |

### 迁移策略

1. **阶段一（兼容期）**：创建新目录结构，旧 `strategies.py` 保留为 re-export shim，全量管线输出验证通过
2. **阶段二（新增功能）**：添加 `standalone.py`、`cli.py` 子命令、`unified_link_fixer`
3. **阶段三（清理）**：删除 `strategies.py` shim，更新所有 import 路径为最终形式
4. **阶段四（回归验证）**：对已知站点执行全量管线 + 新子命令，对比输出一致性
