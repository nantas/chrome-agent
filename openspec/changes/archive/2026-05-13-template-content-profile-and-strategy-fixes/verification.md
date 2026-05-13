# Verification

## 验证结论

验证待实施完成后填写。以下为预定义的验证映射框架。

## Spec-to-Implementation Coverage

### capabilities-derivation

| Requirement | 对应 Task | 验证方式 |
|------------|----------|---------|
| derive-capabilities-from-content-profile | 1.1 | 调用 derive_capabilities 传入 fandom/hybrid/空 profile，断言返回值 |
| derive-capabilities-public-api | 1.2 | `import derive_capabilities` 不报错 |
| derive-capabilities-robustness | 1.1 | 传入无效 ID，断言 ValueError |

### site-strategy-template

| Requirement | 对应 Task | 验证方式 |
|------------|----------|---------|
| template-content-profile-recommendations | 2.1, 2.2, 2.3 | 解析模板 YAML，断言 content_profile 各字段值与 registry 匹配 |
| template-rate-limit-defaults | 2.2, 2.3 | 断言 fandom/wiki-gg 模板 rate_limit.tier 为 "strict"，标准模板无此字段 |
| template-no-static-capabilities | 2.1, 2.2, 2.3 | 断言模板 api 中无 capabilities 键或值为空 |

### strategy-scaffold-generation

| Requirement | 对应 Task | 验证方式 |
|------------|----------|---------|
| layered-api-merge | 3.1 | 模拟 api_config + 模板数据，断言 scaffold 的 api 对象包含三层合并结果 |
| api-discovery-capabilities-isolation | 3.1 | 断言 scaffold 的 api.capabilities 不含 ["read","parse","query"] |
| scaffold-generates-derived-capabilities | 3.1 | 对 fandom/默认模板生成的 scaffold 调用 derive_capabilities 验证 |

### site-strategy

| Requirement | 对应 Task | 验证方式 |
|------------|----------|---------|
| valid-tier-reference | 4.1 | 解析 neonabyss 策略文件，断言 tier="strict"，确认在 rate-limit-api tiers 中存在 |
| anti-crawl-registry-site-coverage | 4.2 | 解析 anti-crawl registry.json，断言 rate-limit-api.sites 含 neonabyss |
| non-superseded-engine-preference | 4.3 | 解析 BGG 策略文件，断言无 scrapling-stealthy-fetch 引用 |
| platform-variant-declaration | 4.4 | 解析 slaythespire 策略文件，断言 platform_variant="wiki-gg" |
| strategy-registry-sync | 4.5 | 对比 registry.json 与策略文件 frontmatter 的一致性 |

## Task-to-Evidence Coverage

| Task | 验证命令/方法 | 预期结果 |
|------|-------------|---------|
| 1.1 | `python3 -c "from orchestrate import derive_capabilities; print(derive_capabilities({...}))"` | fandom: ["category_lookup","html_parse","page_list"]；空: ["category_lookup","page_list","wikitext_parse"] |
| 1.2 | `python3 -c "from orchestrate import derive_capabilities"` | 无 ImportError |
| 2.1-2.3 | `python3 -c "import yaml; yaml.safe_load(open('sites/templates/mediawiki-fandom.yaml').read().split('---',2)[1])"` | frontmatter 含 content_profile 和 rate_limit |
| 3.1 | 检查 scaffold generator 源码 | 无 `api_config or template_data.get("api")` 模式 |
| 4.1 | `grep -c 'tier: strict' sites/strategies/neonabyss.fandom.com/strategy.md` | 返回 1 |
| 4.2 | `python3 -c "import json; r=json.load(open('sites/anti-crawl/registry.json')); print('neonabyss.fandom.com' in [s for e in r['entries'] if e['id']=='rate-limit-api' for s in e['sites']])"` | 返回 True |
| 4.3 | `grep -c 'scrapling-stealthy-fetch' sites/strategies/boardgamegeek.com/strategy.md` | 返回 0 |
| 4.4 | `python3 -c "import yaml; fm=yaml.safe_load(open('sites/strategies/slaythespire.wiki.gg/strategy.md').read().split('---',2)[1]); print(fm['api'].get('platform_variant'))"` | 返回 "wiki-gg" |
| 4.5 | 对比 registry.json 各条目与策略文件 frontmatter | 一致 |
| 5.1 | 对每个 MediaWiki 策略调用 build_pipeline + validate_api_config | 全部不报错 |
| 5.2 | 对每个模板调用 derive_capabilities | 返回非空列表 |

## 关键证据入口

| 证据类型 | 证据路径/链接 | 对应 requirement/task |
| --- | --- | --- |
| derive_capabilities 函数实现 | `scripts/mediawiki-api-extract/pipeline/orchestrate.py` | capabilities-derivation 全部 / Task 1.1-1.2 |
| 模板 YAML diff | `sites/templates/mediawiki*.yaml` | site-strategy-template 全部 / Task 2.1-2.3 |
| scaffold generator diff | `scripts/explore/strategy_scaffold_generator.py` | strategy-scaffold-generation 全部 / Task 3.1-3.2 |
| 策略文件 diff | `sites/strategies/neonabyss.fandom.com/strategy.md` 等 | site-strategy 数据修复 / Task 4.1-4.5 |
| 端到端验证脚本输出 | 实施时记录 | Task 5.1-5.2 |

## 缺口与阻塞项

- 无已知缺口。所有 spec requirements 均有对应 task 和验证方式。
- Task 4.3（BGG 引擎迁移）未实测验证，design 中已记录风险和缓解措施。
