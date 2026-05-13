# Tasks

## 1. derive_capabilities 公共函数

- [x] 1.1 在 `scripts/mediawiki-api-extract/pipeline/orchestrate.py` 中实现 `derive_capabilities(content_profile: dict) -> list[str]` 函数
  - Spec 覆盖: `capabilities-derivation/derive-capabilities-from-content-profile`
  - 实现: 对 `discovery` 和 `content_acquisition` 维度，从 content_profile 查找对应策略 ID，实例化策略类，读取 `required_capabilities`，求并集后返回排序列表
  - 未指定维度时使用 `DEFAULT_STRATEGIES` 的默认 ID
  - 无效 ID 抛出 `ValueError`（与 `build_pipeline()` 的 hard-fail 行为一致）
  - 验证: 单元测试覆盖三个 scenario（fandom profile、空 profile、hybrid profile）+ invalid ID 场景

- [x] 1.2 在 `orchestrate.py` 末尾导出 `derive_capabilities` 作为公共 API
  - Spec 覆盖: `capabilities-derivation/derive-capabilities-public-api`
  - 实现: 与 `STRATEGY_REGISTRY` 同级导出
  - 验证: `from orchestrate import derive_capabilities` 可正常调用

## 2. 模板 content_profile 和 rate_limit 补全

- [x] 2.1 更新 `sites/templates/mediawiki.yaml` — 添加 content_profile 默认值（与 DEFAULT_STRATEGIES 一致），移除或清空 capabilities
  - Spec 覆盖: `site-strategy-template/template-content-profile-recommendations` + `template-no-static-capabilities`
  - 实现: content_profile 各维度为 `allpages` / `wikitext_only` / `exact_title_match` / `simple_substitution` / `frontmatter_driven`
  - 验证: YAML frontmatter 结构正确，content_profile 各 ID 在 registry 中存在

- [x] 2.2 更新 `sites/templates/mediawiki-fandom.yaml` — 添加 content_profile 推荐值 + rate_limit.tier + 移除 capabilities
  - Spec 覆盖: `site-strategy-template/template-content-profile-recommendations` + `template-rate-limit-defaults` + `template-no-static-capabilities`
  - 实现: content_profile 为 `category_members` / `html_rendered` / `short_name_with_cross_namespace` / `fandom_infobox` / `hybrid_frontmatter_and_rendered`；rate_limit.tier 为 `"strict"`
  - 验证: YAML frontmatter 结构正确，content_profile 各 ID 在 registry 中存在

- [x] 2.3 更新 `sites/templates/mediawiki-wiki-gg.yaml` — 添加 content_profile 推荐值 + rate_limit.tier + 移除 capabilities
  - Spec 覆盖: 同 2.2
  - 实现: content_profile 为 `category_members` / `hybrid_wikitext_plus_rendered` / `short_name_with_cross_namespace` / `structured_with_lua_fallback` / `hybrid_frontmatter_and_rendered`；rate_limit.tier 为 `"strict"`
  - 验证: YAML frontmatter 结构正确，content_profile 各 ID 在 registry 中存在

## 3. scaffold generator 合并逻辑重构

- [x] 3.1 重构 `scripts/explore/strategy_scaffold_generator.py` 的 `generate()` 函数中 API 对象组装逻辑
  - Spec 覆盖: `strategy-scaffold-generation/layered-api-merge`
  - 实现: 将 `"api": api_config or template_data.get("api")` 替换为三层合并：
    - Layer 1: 从模板 api 复制 `platform`、`platform_variant`、`content_profile`、`rate_limit`
    - Layer 2: 从 api_config 复制 `type`、`base_url`、`version`（不复制 capabilities、site_name、lang、pages、articles）
    - Layer 3: 调用 `derive_capabilities()` 生成 capabilities
  - 验证: 模拟 api_config 存在/不存在/模板 api 为 null 三种场景的输出

- [x] 3.2 确保 scaffold generator 中已有的 content_profile ID 校验逻辑仍正常工作
  - Spec 覆盖: `capabilities-derivation/derive-capabilities-robustness`（间接）
  - 实现: content_profile ID 校验在 derive_capabilities 调用前仍执行（已有逻辑不变）
  - 验证: 使用无效 content_profile ID 调用 generate() 仍抛出 ValueError

## 4. 现有站点策略数据修复

- [x] 4.1 修正 `sites/strategies/neonabyss.fandom.com/strategy.md` 的 `api.rate_limit.tier` 从 `"standard"` 改为 `"strict"`
  - Spec 覆盖: `site-strategy/valid-tier-reference`
  - 验证: `"strict"` 在 `rate-limit-api.md` 的 `rate_limit_tiers` 中存在

- [x] 4.2 修正 `sites/anti-crawl/registry.json` 中 `rate-limit-api` 条目的 `sites` 列表，增加 `"neonabyss.fandom.com"`
  - Spec 覆盖: `site-strategy/anti-crawl-registry-site-coverage`
  - 验证: registry 中 rate-limit-api 的 sites 包含 fanbox.cc、slaythespire.wiki.gg、neonabyss.fandom.com

- [x] 4.3 更新 `sites/strategies/boardgamegeek.com/strategy.md` 的引擎引用从 `scrapling-stealthy-fetch` 改为 `cloakbrowser-fetch`
  - Spec 覆盖: `site-strategy/non-superseded-engine-preference`
  - 实现: 更新 strategy-level 和两个 page-level 的 engine_preference.preferred（共 3 处）
  - 验证: 所有 engine_preference 中无 superseded 引擎引用

- [x] 4.4 补充 `sites/strategies/slaythespire.wiki.gg/strategy.md` 的 `api.platform_variant: wiki-gg`
  - Spec 覆盖: `site-strategy/platform-variant-declaration`
  - 验证: frontmatter 中 `api.platform_variant` 为 `"wiki-gg"`

- [x] 4.5 同步 `sites/strategies/registry.json` 中受影响条目的元数据
  - Spec 覆盖: `site-strategy/strategy-registry-sync`
  - 实现: 检查 neonabyss（anti_crawl_refs 含 rate-limit-api）、BGG（无 engine 字段需更新）、slaythespire（description 可能需更新 variant 信息）
  - 验证: registry 中每个条目的字段与策略文件 frontmatter 一致

## 5. 端到端验证

- [x] 5.1 对所有 MediaWiki 站点策略运行 pipeline 校验模拟
  - 实现: 对每个 MediaWiki 策略文件调用 `build_pipeline()` + `validate_api_config()`，确认不触发 EXIT_STRATEGY_ERROR
  - 站点: balatrowiki.org、vampire.survivors.wiki、neonabyss.fandom.com、slaythespire.wiki.gg
  - 验证: 全部通过校验

- [x] 5.2 验证模板 content_profile ID 引用完整性
  - 实现: 对每个 MediaWiki 模板调用 `derive_capabilities()`，确认不抛异常
  - 验证: 三个模板均返回非空 capabilities 列表
