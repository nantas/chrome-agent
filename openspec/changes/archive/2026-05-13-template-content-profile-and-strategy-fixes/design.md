# Design

## Context

`pipeline-governance-and-variant` 和 `pipeline-fandom-compatibility` 两个 change 建立了 registry schema 约束、platform_variant 框架、并修复了 Fandom 管线兼容性。但模板层和 scaffold 生成流程未同步更新，导致 explore 自动生成的策略文件缺少 content_profile、capabilities 词汇不兼容、且 API 合并逻辑丢弃模板的声明性字段。本 change 在治理框架约束下修复这些断层。

## Goals / Non-Goals

**Goals:**
- 在 `orchestrate.py` 中实现 `derive_capabilities()` 公共函数（spec: `capabilities-derivation`）
- 为三个 MediaWiki 模板补全 content_profile 推荐值和 rate_limit.tier（spec: `site-strategy-template`）
- 重构 scaffold generator 的 API 合并为分层合并逻辑（spec: `strategy-scaffold-generation`）
- 修正 4 个现有站点策略文件的数据问题（spec: `site-strategy`）
- 同步 anti-crawl registry 和 site-strategy registry 索引

**Non-Goals:**
- 不实现交互式 content_profile 确认流程
- 不修改 pipeline 的 Phase A/B/C 核心执行逻辑
- 不修改 `_STRATEGY_REGISTRY` 的注册条目或策略类实现
- 不修改非 MediaWiki 模板（wordpress、static-site、custom）
- 不补充 rate-limit-api.md 中 Fandom 限速经验正文

## Decisions

### Decision 1: derive_capabilities 放在 orchestrate.py

**选择**：`derive_capabilities()` 作为公共函数放在 `orchestrate.py` 中，与 `STRATEGY_REGISTRY` 和 `build_pipeline()` 同级导出。

**理由**：
- `validate_api_config()` 也在 orchestrate.py 中，capabilities 推导是管线层面的关注
- scaffold generator 已有动态 import orchestrate.py 的模式（用于 content_profile ID 校验），无额外依赖成本
- 单一权威来源：`_STRATEGY_REGISTRY` → `required_capabilities` → `derive_capabilities()` → 策略文件的 `api.capabilities`

### Decision 2: capabilities 推导只读 discovery + content_acquisition

**选择**：只对 `discovery` 和 `content_acquisition` 两个维度读取 `required_capabilities` 并求并集，其他三个维度（link_resolver、template_processor、list_page_assembler）不参与推导。

**理由**：
- 策略类实现中只有这两个维度定义了非空 `required_capabilities`
- 其他三个维度的策略类返回空集，参与推导无意义
- 与 `validate_api_config()` 的校验逻辑一致（只检查 discovery + content_acquisition 的 required）

### Decision 3: 模板 capabilities 字段留空

**选择**：模板的 `api.capabilities` 设为空列表 `[]` 或删除该键，不手动维护。

**理由**：
- capabilities 与 content_profile 存在推导依赖关系，手动维护容易不同步
- `derive_capabilities()` 从 content_profile 动态生成，模板只需提供 content_profile
- 模板中保留 `capabilities: []` 可作为文档提示"此处由系统生成"，避免误解

### Decision 4: api_discovery 的 capabilities 保留但不传递

**选择**：`_probe_mediawiki()` 继续返回 `capabilities: ["read", "parse", "query"]`（用于 explore 输出的信息展示），scaffold generator 在合并时显式忽略此字段。

**理由**：
- siteinfo 的原始权限信息对用户理解站点能力仍有参考价值
- 修改 api_discovery 的返回值可能影响其他消费者
- 在合并逻辑中隔离更安全——明确表达"探测的 capabilities 不进策略文件"

### Decision 5: 合并逻辑中 siteinfo 元数据的处理

**选择**：api_config 中的 `site_name`、`lang`、`pages`、`articles` 不写入策略文件。

**理由**：
- 策略文件的 `api` 对象是 pipeline 的配置输入，不是站点的元数据存储
- 这些字段对 pipeline 执行无影响，只会增加维护负担（站点更新后元数据过时）
- 如果未来需要站点元数据，应走独立的数据结构

### Decision 6: 分层合并的具体实现

**选择**：在 scaffold generator 的 `generate()` 函数中，按以下顺序构建 `api` 对象：

```python
api = {}
# Layer 1: 模板声明性字段
template_api = template_data.get("api") or {}
for key in ("platform", "platform_variant", "content_profile", "rate_limit"):
    if key in template_api:
        api[key] = template_api[key]
# Layer 2: 探测事实性字段
if api_config:
    api["type"] = api_config.get("type", "mediawiki")
    api["base_url"] = api_config.get("base_url", "")
    api["version"] = api_config.get("version", "")
    # 不合并 capabilities, site_name, lang, pages, articles
# Layer 3: 动态推导
api["capabilities"] = derive_capabilities(api.get("content_profile", {}))
```

### Decision 7: BGG 引擎引用迁移到 cloakbrowser-fetch

**选择**：将 `boardgamegeek.com` 策略中的 `engine_preference.preferred` 从 `scrapling-stealthy-fetch` 更新为 `cloakbrowser-fetch`。

**理由**：
- `scrapling-stealthy-fetch` 状态为 `superseded`，`cloakbrowser-fetch` 是其官方替代引擎
- AGENTS.md 引擎注册表中明确标注了替代关系
- BGG 策略中 engine_preference 出现在两个页面定义中，需统一更新

### Decision 8: neonabyss tier 改为 strict

**选择**：将 `neonabyss.fandom.com` 的 `api.rate_limit.tier` 从 `"standard"` 改为 `"strict"`。

**理由**：
- `"standard"` 在 `rate-limit-api.md` 的 tier 定义中不存在
- Fandom 站点与 wiki.gg 站点同样使用 MediaWiki API，限速行为类似
- `"strict"` 已在 slaythespire.wiki.gg 上验证（1291/1298 页成功），是安全选择
- 如果未来需要更宽松的配置，可在 Fandom 站点上实测后新增 tier

## Risks / Migration

### Risk 1: derive_capabilities 与策略类实现耦合

**风险**：如果策略类的 `required_capabilities` 返回值发生变化，`derive_capabilities()` 的输出会跟着变，但已有的策略文件的 `capabilities` 字段不会自动更新。

**缓解**：
- `required_capabilities` 是策略类的稳定契约，变更频率极低
- 如果发生变更，pipeline 的 `validate_api_config()` 会自然拒绝旧的 capabilities（hard-fail），提示更新

### Risk 2: 模板 content_profile 推荐值可能不适合所有同类站点

**风险**：不是所有 Fandom 站点都需要 `fandom_infobox` 模板处理器，不是所有 wiki.gg 站点都需要 `hybrid_wikitext_plus_rendered`。

**缓解**：
- 模板值为推荐默认，用户在 review scaffold 时可修改
- 未来实现交互式确认流程时，用户可以显式选择策略 ID

### Risk 3: BGG 引擎迁移未实测

**风险**：将 BGG 的引擎引用从 `scrapling-stealthy-fetch` 改为 `cloakbrowser-fetch` 后，未经实际运行验证。

**缓解**：
- `cloakbrowser-fetch` 是 `scrapling-stealthy-fetch` 的官方替代，架构和 API 兼容
- BGG 的反爬机制是 bot detection（HTTP 403），cloakbrowser 的 stealth 能力覆盖此场景
- 如果实测发现问题，可回退或新增专门的策略
