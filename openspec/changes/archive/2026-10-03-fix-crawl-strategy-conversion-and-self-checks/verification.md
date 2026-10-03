# Verification

## 验证结论

2026-10-03，Codex，验证对象为工作区实现（基于 HEAD `389e49fbbd6b769ec8b7aecb4453af34b93cfb71`，未提交）。P-1～P-4 实现通过；不宣称已部署、已归档或执行了新采集。

- Python unittest 全量：265 tests，OK。
- Node 全量：152 tests，pass 152，fail 0。
- darkestdungeon.wiki.gg site-samples：13/13，通过；本 change 没有改写 golden。
- repo CLI 与全局 launcher 的 `doctor --check capabilities --format json`：success。
- 六份 DD2 HTML 经真实 crawl 函数→真实 Python bridge 离线重放，6/6 成功，与相同规则的共享内核字节一致；表格、S1 图片 multiset、S8 章节检查通过。正文与基线一致时链接也由字节等价保证。
- handoff 规则重放：六份正文与 staging 旧基线完全一致（仅剥离明确的标题/来源四行包装和末尾换行）。
- 当前规则重放：其他流程新增四项 cleanup，三份正文与旧基线格式不同，但与当前共享内核完全一致；保留原始 diff，不覆盖外部改动。
- S1/S5 六页均 pass；S9 五页 pass，Carrion Eater 为明确 skip（body/navigation overlap）。没有自检 fail；skip 不等于完整验证。
- Python 3.9 AST 语法检查、Node 语法检查、git diff --check 通过；没有遗留 DEBUG instrumentation。C10 runtime/skill 同步完成，installed-hash 等于上述 HEAD。

## Spec-to-Implementation Coverage

| Spec / Requirement | 实现 | 可重复验证 |
| --- | --- | --- |
| convert / crawl-strategy-html-shared-conversion | CLI convertCrawlHtml + lib/crawl_conversion.py + crawl_scrapling/sitemap HTML 复用 | tests/crawl-strategy-conversion.test.mjs：普通、sitemap、cache、prefetched、empty rules、API 分支 |
| convert / crawl-strategy-conversion-fails-closed | bridge 临时输出发布；准确 URL 结果；成功集合构造 artifacts/merge | 同测试：坏规则、缺依赖、缺预取、A/C 成功 B 失败、stale、全失败、challenge |
| convert / crawl-mirror-equivalence-proof | 真实 bridge→convert_page_full，外层链接/merge 保留 | 同测试：嵌套表、cleanup、infobox/post-op canary；六页真实重放 |
| fetch-strategy-selector / 四条 MODIFIED requirements | matched crawl 转共享规则，独立 fetch/helper 保留 | tests/fetch-strategy-selector.test.mjs + crawl-strategy-conversion.test.mjs |
| explore-workflow / self-check-source-context | self_check.build_source_context；sample_converter input_scope；main/iterate 传当前规则 | tests/test_self_check_source.py + tests/test_self_check_integration.py |
| explore-workflow / s1-intended-image-retention | 独立来源 region、Counter 图片身份、lazyload/过滤 | test_self_check_source：缺图、等量换图、重复图、infobox 重叠、括号 URL、fragment/full、错误 selector |
| explore-workflow / s9-source-based-navigation-leakage | 来源导航序列与 body 对应关系；歧义 skip | test_self_check_source：合法 Items、真实登录导航、body 冲突、缺来源 |
| explore-workflow / s5-source-attributed-repetition | 可见文本、图片边界、来源 occurrence budget、notes | test_self_check_source：来源笔误、新增/多一次重复、代码/URL/块边界、其他异常不被 note 隐藏 |
| explore-workflow / self-check-summary-and-remediation-compatibility | summarize notes/skipped_checks；main/iterate 集成 | test_self_check_integration + 既有 test_explore_main_remediation/iterate 全量回归 |

## Task-to-Evidence Coverage

| Tasks | 证据 |
| --- | --- |
| 1.1–1.2 | 本 change 三份 specs/design；嵌入式 tests fixture 不依赖网络、outputs 或全局抓取引擎 |
| 2.1–2.2 | 首次 RED：engines acquire HTML only；GREEN：真实 bridge core 等价 |
| 2.3–2.4 | cache RED：不应预检抓取引擎；ordinary RED：不应重复 pool 获取；sitemap RED：2 次获取而非 1；均已 GREEN |
| 2.5–2.6 | RED：B 的 stale artifact 仍被列出；GREEN：精确失败集合、merge 排除；额外 cache maxPages RED→GREEN |
| 2.7–2.8 | RED：来源接口缺失；GREEN：S1 retention 正反例；非法 selector/legacy scope 再次 RED→GREEN |
| 2.9–2.10 | RED：合法三行 Items 误报；GREEN：来源导航判定 |
| 2.11–2.12 | RED：来源 notes 缺失；GREEN：重复来源预算；图片边界额外 RED→GREEN |
| 2.13–2.14 | RED：真实 iterate S1 Expected 2/found 1；GREEN：main/iterate 一致且零错误 remediation |
| 3.1–3.4 | 下列完整命令和结果、双规则 DD2 重放、能力 doctor、全局 hash 检查 |
| 4.1–4.3 | 本 verification + writeback.md 的六个本地文档回写记录；归档 checklist 留待 archive 动作 |

## 关键证据入口

| 证据类型 | 证据路径/链接 | 对应 requirement/task |
| --- | --- | --- |
| 正式 Node 回归 | tests/crawl-strategy-conversion.test.mjs、tests/fetch-strategy-selector.test.mjs | P-1 / 2.1–2.6 |
| 正式 Python 回归 | tests/test_self_check_source.py、tests/test_self_check_integration.py、tests/test_table_section_integrity.py | P-2～P-4 / 2.7–2.14 |
| 全量测试日志（本机） | outputs/debug-dd2-diagnosis/python-tests.log、node-tests.log、site-tests.log | 3.1、3.3 |
| 现场重放（本机） | outputs/debug-dd2-diagnosis/replay.mjs、replay-verification.json、replayed/result.json、replayed-handoff/result.json | 3.2 |
| 固定规则（本机） | outputs/debug-dd2-diagnosis/replayed/extraction.json、replayed-handoff/extraction.json | 区分镜像漂移与外部配置变化 |
| 能力检查（本机） | outputs/debug-dd2-diagnosis/capabilities.json、global-capabilities.json | 3.4 |

运行命令：

```bash
.venv/bin/python -m unittest discover -s tests -v
node --test tests/*.test.mjs
.venv/bin/python scripts/test_runner.py site-samples --domain darkestdungeon.wiki.gg
node scripts/chrome-agent-cli.mjs doctor --check capabilities --format json
chrome-agent doctor --check capabilities --format json
node outputs/debug-dd2-diagnosis/replay.mjs
node outputs/debug-dd2-diagnosis/replay.mjs outputs/debug-dd2-diagnosis/handoff-extraction.json
```

## 缺口与阻塞项

无阻塞实施收口项。现场证据留在明确的 debug 目录，正式回归使用自包含 fixture。没有重新访问网站，验证范围是缓存 HTML 到产出/自检的真实路径。

Carrion Eater S9 证据歧义明确 skip，符合 spec 的不伪造来源归因要求。S9 是来源序列证据检查，不是所有可能导航泄漏的完备证明；缺少来源的 legacy run_checks 对 S1/S9 或重复归因显式 skip，已有低层 fragment-only S1 函数保持可用。

本工作区另有 preprocessor、站点策略、registry 和样本变更；这些不是本 change 实现，未覆盖或回退。当前站点验收依赖当前工作区共享内核；handoff 规则快照提供独立旧基线证明。

C10 不需要刷新 pipeline conversion revision：本 change 未修改共享转换算法，只新增 crawl 镜像。外部表格 change 保持原样。尚未执行归档或永久 spec 合并。

## evidence_map[]

| scenario_key | evidence_ref | external_ref | verification_result |
| --- | --- | --- | --- |
| cloakbrowser-strategy-body | tests/crawl-strategy-conversion.test.mjs | working-tree@389e49f | pass |
| selector-is-not-full-extraction | tests/crawl-strategy-conversion.test.mjs | working-tree@389e49f | pass |
| all-html-entry-paths | tests/crawl-strategy-conversion.test.mjs | working-tree@389e49f | pass |
| absent-or-invalid-extraction | tests/crawl-strategy-conversion.test.mjs | working-tree@389e49f | pass |
| no-strategy-compatibility | tests/crawl-strategy-conversion.test.mjs | working-tree@389e49f | pass |
| bridge-failure-with-stale-output | tests/crawl-strategy-conversion.test.mjs | working-tree@389e49f | pass |
| prefetched-conversion-failure | tests/crawl-strategy-conversion.test.mjs | working-tree@389e49f | pass |
| interleaved-cache-results | tests/crawl-strategy-conversion.test.mjs | working-tree@389e49f | pass |
| nested-table-and-cleanup-canary | tests/crawl-strategy-conversion.test.mjs | working-tree@389e49f | pass |
| wrapper-aware-dd2-replay | tests/crawl-strategy-conversion.test.mjs | working-tree@389e49f | pass |
| full-page-versus-api-fragment | tests/test_self_check_source.py + tests/test_self_check_integration.py | working-tree@389e49f | pass |
| missing-content-selector-match | tests/test_self_check_source.py + tests/test_self_check_integration.py | working-tree@389e49f | pass |
| main-iterate-agreement | tests/test_self_check_source.py + tests/test_self_check_integration.py | working-tree@389e49f | pass |
| skin-images-excluded | tests/test_self_check_source.py + tests/test_self_check_integration.py | working-tree@389e49f | pass |
| retained-image-loss | tests/test_self_check_source.py + tests/test_self_check_integration.py | working-tree@389e49f | pass |
| intentional-filter-and-lazyload | tests/test_self_check_source.py + tests/test_self_check_integration.py | working-tree@389e49f | pass |
| legitimate-related-items | tests/test_self_check_source.py + tests/test_self_check_integration.py | working-tree@389e49f | pass |
| actual-skin-navigation | tests/test_self_check_source.py + tests/test_self_check_integration.py | working-tree@389e49f | pass |
| body-navigation-label-collision | tests/test_self_check_source.py + tests/test_self_check_integration.py | working-tree@389e49f | pass |
| faithful-source-typo | tests/test_self_check_source.py + tests/test_self_check_integration.py | working-tree@389e49f | pass |
| converter-introduced-repetition | tests/test_self_check_source.py + tests/test_self_check_integration.py | working-tree@389e49f | pass |
| extra-occurrence-not-exempted | tests/test_self_check_source.py + tests/test_self_check_integration.py | working-tree@389e49f | pass |
| source-note-with-other-anomaly | tests/test_self_check_source.py + tests/test_self_check_integration.py | working-tree@389e49f | pass |
| source-note-does-not-trigger-repair | tests/test_self_check_source.py + tests/test_self_check_integration.py | working-tree@389e49f | pass |
| evidence-unavailable | tests/test_self_check_source.py + tests/test_self_check_integration.py | working-tree@389e49f | pass |
| fetch-with-strategy-content-selector | tests/crawl-strategy-conversion.test.mjs + tests/fetch-strategy-selector.test.mjs | working-tree@389e49f | pass |
| crawl-with-strategy-content-selector | tests/crawl-strategy-conversion.test.mjs + tests/fetch-strategy-selector.test.mjs | working-tree@389e49f | pass |
| selector-source-is-strategy-not-hardcoded | tests/crawl-strategy-conversion.test.mjs + tests/fetch-strategy-selector.test.mjs | working-tree@389e49f | pass |
| fetch-strategy-without-content-selector | tests/crawl-strategy-conversion.test.mjs + tests/fetch-strategy-selector.test.mjs | working-tree@389e49f | pass |
| fetch-no-strategy-match | tests/crawl-strategy-conversion.test.mjs + tests/fetch-strategy-selector.test.mjs | working-tree@389e49f | pass |
| crawl-matched-without-selector | tests/crawl-strategy-conversion.test.mjs + tests/fetch-strategy-selector.test.mjs | working-tree@389e49f | pass |
| helper-encapsulates-selector-decision | tests/crawl-strategy-conversion.test.mjs + tests/fetch-strategy-selector.test.mjs | working-tree@389e49f | pass |
| helper-preserves-mediawiki-api-path | tests/crawl-strategy-conversion.test.mjs + tests/fetch-strategy-selector.test.mjs | working-tree@389e49f | pass |
| cloakbrowser-acquires-only | tests/crawl-strategy-conversion.test.mjs + tests/fetch-strategy-selector.test.mjs | working-tree@389e49f | pass |
| selector-with-special-characters | tests/crawl-strategy-conversion.test.mjs + tests/fetch-strategy-selector.test.mjs | working-tree@389e49f | pass |

## 归档与提交隔离验证（2026-10-03）

从暂存区 `git write-tree` 导出独立目录，不包含并行流程的 preprocessor、cleanup 注册、站点策略或本地样本改动：Node 全量 152/152，Python 全量 251/251 通过。Python 首轮出现历史提交不可见与 1 秒版本检查超时；补充只读 Git 对象访问并串行重跑后全量通过。工作区此前 265 项包含未纳入本次提交的 14 项预处理器测试。三份合并后的永久规范均通过 strict 校验，归档前 capabilities doctor 通过。
