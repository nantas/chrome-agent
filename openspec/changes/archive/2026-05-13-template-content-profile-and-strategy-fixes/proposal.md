# Proposal

## 问题定义

管线修复与治理框架建立（`pipeline-governance-and-variant` + `pipeline-fandom-compatibility`）完成后，策略模板和 scaffold 生成流程暴露了三个层面的断层：

1. **模板缺少 content_profile 和 rate_limit 推荐值** — `mediawiki-fandom.yaml`、`mediawiki-wiki-gg.yaml`、`mediawiki.yaml` 三个模板的 `api` 对象中完全没有 `content_profile` 和 `rate_limit` 字段。explore 自动生成的策略文件不携带管线所需的策略 ID 配置，pipeline 回退到全部默认值，对 Fandom/wiki.gg 站点产出质量极差。

2. **scaffold generator 合并逻辑有 bug** — `strategy_scaffold_generator.py` 中 `"api": api_config or template_data.get("api")` 使用 `or` 操作符，当 API 探测返回非 None 结果时，模板的声明性字段（content_profile、platform_variant、rate_limit）被完全丢弃。

3. **capabilities 词汇表不兼容** — `api_discovery.py` 返回 MediaWiki siteinfo 的原始权限词汇 `["read", "parse", "query"]`，但 `validate_api_config()` 校验使用 pipeline 策略类定义的词汇 `["page_list", "category_lookup", "html_parse", ...]`。两套词汇完全不兼容，导致 explore 生成的策略文件无法通过 pipeline 校验。

此外，现有站点策略文件存在多个过时数据：
- `neonabyss.fandom.com` 的 `rate_limit.tier: "standard"` 在 rate-limit-api 的 tier 定义中不存在
- `sites/anti-crawl/registry.json` 中 rate-limit-api 条目的 `sites` 列表缺少 `neonabyss.fandom.com`
- `boardgamegeek.com` 的 `engine_preference.preferred` 引用已 superseded 的 `scrapling-stealthy-fetch`
- `slaythespire.wiki.gg` 缺少 `platform_variant: wiki-gg` 声明

## 范围边界

**范围内：**
- 为三个 MediaWiki 模板补全 `content_profile` 推荐值和 `rate_limit.tier` 默认值
- 重构 scaffold generator 的 API 合并逻辑：模板提供声明性字段（content_profile、platform_variant、rate_limit），探测提供事实性字段（base_url、version）
- 在 `orchestrate.py` 中新增 `derive_capabilities(content_profile)` 公共函数，从 content_profile ID 动态推导 capabilities
- scaffold generator 调用 `derive_capabilities()` 生成 capabilities，模板不再手动维护此字段
- 修正 `api_discovery.py` 的 MediaWiki 探测结果，不再将不兼容的 capabilities 传入策略文件
- 修复 `neonabyss.fandom.com` 策略文件的 tier 引用（`"standard"` → `"strict"`）
- 修复 `sites/anti-crawl/registry.json` 中 rate-limit-api 条目缺少 neonabyss 的问题
- 更新 `boardgamegeek.com` 策略的引擎引用（`scrapling-stealthy-fetch` → `cloakbrowser-fetch`）
- 补充 `slaythespire.wiki.gg` 策略的 `platform_variant: wiki-gg` 声明
- 同步更新 `sites/strategies/registry.json` 中受影响策略的元数据

**范围外：**
- 不修改 pipeline 的 Phase A/B/C 核心执行逻辑
- 不修改 `_STRATEGY_REGISTRY` 的注册条目或策略类实现
- 不实现交互式 content_profile 确认流程（留作后续增强）
- 不修改非 MediaWiki 类型的模板（wordpress、static-site、custom）
- 不修改 `api_discovery.py` 对非 MediaWiki API 的处理
- 不补充 rate-limit-api.md 中 Fandom 限速经验的正文记录（运行数据收集是独立任务）

## Capabilities

### New Capabilities
- `capabilities-derivation`: 从 content_profile ID 动态推导 pipeline 所需 capabilities 的公共函数，供 scaffold generator 和未来交互式确认流程使用

### Modified Capabilities
- `site-strategy-template`: 平台模板 schema 扩展——新增 content_profile 推荐值和 rate_limit.tier 默认值；模板不再包含 capabilities 字段（改为动态推导）
- `strategy-scaffold-generation`: scaffold 生成器合并逻辑重构——从 `or` 覆盖改为分层合并（模板声明性字段 + 探测事实性字段 + 动态推导 capabilities）
- `site-strategy`: 修正现有站点策略文件的数据问题（neonabyss tier、BGG 引擎、slaythespire variant、anti-crawl registry 缺失）

## Capabilities 待确认项

- [x] 能力清单已与用户确认（explore 模式中讨论确定方案后产出）

## Impact

| 受影响组件 | 影响类型 | 描述 |
|-----------|---------|------|
| `sites/templates/mediawiki.yaml` | 内容新增 | 补全 content_profile 默认值 |
| `sites/templates/mediawiki-fandom.yaml` | 内容新增 | 补全 content_profile 推荐值 + rate_limit.tier |
| `sites/templates/mediawiki-wiki-gg.yaml` | 内容新增 | 补全 content_profile 推荐值 + rate_limit.tier |
| `scripts/mediawiki-api-extract/pipeline/orchestrate.py` | 功能新增 | 新增 `derive_capabilities()` 公共函数 |
| `scripts/explore/strategy_scaffold_generator.py` | 行为变更 | API 合并逻辑重构 + capabilities 动态推导 |
| `scripts/explore/api_discovery.py` | 行为变更 | MediaWiki 探测结果不再包含 pipeline-incompatible capabilities |
| `sites/strategies/neonabyss.fandom.com/strategy.md` | 数据修正 | tier: "standard" → "strict" |
| `sites/strategies/boardgamegeek.com/strategy.md` | 数据修正 | engine_preference → cloakbrowser-fetch |
| `sites/strategies/slaythespire.wiki.gg/strategy.md` | 数据修正 | 补充 platform_variant: wiki-gg |
| `sites/anti-crawl/registry.json` | 索引修正 | rate-limit-api sites 增加 neonabyss |
| `sites/strategies/registry.json` | 索引同步 | 同步受影响策略的元数据变更 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `AGENTS.md`（治理约束同步）
  - `openspec/specs/agents-governance/spec.md`（spec 真源同步）
  - `sites/anti-crawl/registry.json`（索引修正）
  - `sites/strategies/registry.json`（索引同步）
