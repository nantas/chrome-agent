# Verification

## 验证结论

2026-09-11，验证目标为 HEAD `d10858db1a63e701d1fcca61e455766e5fe96264` 加当前工作区的 `fix-mediawiki-extraction-integrity` 实现。离线核心实现与回归通过；站点样本为 3 通过、1 既有基线差异。未执行真实全站重抓或 my-wiki ingest，不能据此声明历史产物已经恢复或全站质量通过。

- `.venv/bin/python -m unittest discover -s tests -v`：170 passed。
- `node --test tests/*.test.mjs`：108 passed，0 skipped。
- `.venv/bin/python -m unittest discover -s scripts/pipeline/tests -v`：51 passed。
- 21 个变更/新增 Python 文件通过 Python 3.9 grammar AST 检查；没有新增依赖、TypeScript、CommonJS 或第三方测试框架。没有在真实 Python 3.9 解释器上跑全套测试，语法检查不替代运行时证据。
- `chrome-agent doctor --format json`：success；`chrome-agent doctor --check capabilities`：success。
- C10 runtime/skill 全局副本逐字匹配仓库源，installed-hash 等于上述 HEAD。CLI 本身由 runtime 路由到仓库，不是复制目标。
- `openspec validate fix-mediawiki-extraction-integrity --strict`：通过。主规范已按八份 delta 合并，change 保持活动状态。

## Spec-to-Implementation Coverage

下表规范路径均相对本 change 的 `specs/`。所有受影响模块已有相应行为测试，没有新增无测试的生产模块。

| Spec / requirement | 实现入口 | 证据与结论 |
| --- | --- | --- |
| convert：three-layer-interface、mirror-equivalence | `scripts/lib/extraction/converter.py::convert_page_full`，`scripts/pipeline/pipeline/phases/convert.py::_process_html_page` | `tests/test_convert_equivalence.py`：真实 CV4 字段 canary、匹配上下文、post-ops、配置冲突、泛型及 standalone 既有证明通过 |
| extract-kernel：convert-page-full、extract-infobox、enable/selector parity | `converter.py`、`infobox.py`、`preprocessor.py` | 同上：启用默认 selector、禁用无重复、字段值、base URL、表格 selector、handler、跨目录/redirect、相同文本不同 href 保留 |
| mediawiki-cache-integrity：exact identity、legacy read、acquisition admission | `scripts/pipeline/pipeline/cache.py`；`strategies/acquisition.py::requires_rendered` | `tests/pipeline/test_cache_integrity.py`、`test_acquisition_cache.py`：碰撞标题、Unicode/长标题、并发、v2优先、旧候选/损坏/身份拒绝、动态 hybrid 缺载荷、默认模式、来源通过 |
| fetch-phase-cache-fastpath：full/partial、fresh payload | `phases/fetch.py::run_fetch`、`pipeline/orchestrator.py` | `test_acquisition_cache.py`：全兼容无 executor/请求、混合只取缺口、re-fetch、新响应准入；`test_conversion_resume.py` 验证失败 title 传递与 fetch-only 非零 |
| pipeline-convert-phase：resume fingerprint、cache admission、mirror proof | `phases/convert.py::run_convert`、`orchestrator.py`、`phases/assemble.py` | `test_conversion_resume.py`：旧 hybrid/completion拒绝、内容/配置/目录/revision变化重转、时间戳忽略、禁用resume、写入失败、编排层保留指纹、强制重抓失败不能复用兼容旧cache；fake API→assembly恢复且失败页不入索引 |
| pipeline-converters：monotonic-wikitable-scanning、source-dir passthrough | `converters/wikitext_to_md.py`、`lib/extraction/infobox.py` | `test_wikitable_scanning.py`：隔离 HEAD 子进程复现挂死，当前文首/两表/单元格/嵌套/未闭合通过；equivalence + 旧 source-dir 测试覆盖两条提取路径 |
| cli：configurable-mediawiki-pipeline-timeout | `scripts/chrome-agent-cli.mjs`、`scripts/lib/mediawiki-crawl.mjs` | `tests/mediawiki-crawl.test.mjs`：真实参数入口+fake Python，600/3600秒预算、非法输入、两阶段预算、failure envelope、确认门通过 |
| strategy：stable-registry-publication-format | `scripts/explore/freeze.py` | `tests/test_strategy_lifecycle.py`：2/4空格、尾换行、顺序、原位更新、append、重复发布、rollback；真实 registry 未由本 change 重排 |

## Task-to-Evidence Coverage

| Tasks | 证据 |
| --- | --- |
| 1.1–1.2 | 保留用户原有 cache/table 修复意图，保留 growagarden strategy/registry 与无关 mobalytics；读取治理与关联规范；ADR0014明确输出命名交叉边界 |
| 2.1–2.4 | equivalence 按场景 RED/GREEN；独立字段 canary 防止两个入口同时丢字段；后续默认 selector/disabled、同名不同 pool 链接测试先失败再修复 |
| 2.5–2.8 | cache 公共入口 RED/GREEN；临时目录和并发测试；ADR0014 |
| 2.9–2.14 | acquisition/resume RED/GREEN；收尾真实 orchestrator 测试依次捕获指纹被覆盖、强制重抓失败被旧cache掩盖，修复后通过 |
| 2.15–2.16 | 受控 `git show d10858d` 提取旧函数，在 subprocess timeout 下复现；没有回滚用户工作区；多表和首单元格回归通过 |
| 2.17–2.18 | MediaWiki Node tests 与实际CLI入口参数测试，无真实长时间等待 |
| 2.19–2.20 | freeze lifecycle 临时 registry 字节和rollback证明 |
| 3.1 | `test_offline_fetch_convert_assemble_recovery` + `test_orchestrator_retains_fingerprints_and_reports_failed_refetch` |
| 3.2–3.4 | 上述170/108/51测试、语法检查、下述站点记录、C10/doctor；既有 capability 实现入口未新增文件，registry无需扩项 |
| 4.1–4.4 | 本文、writeback.md、七项文档目标及ADR，八份主规范同步，严格校验与doctor |

## 站点样本

各站均运行 `.venv/bin/python scripts/test_runner.py site-samples --domain DOMAIN`，均有一个可用样本，无 skip。

| Domain / sample | 结果 | 字段审核及归因 |
| --- | --- | --- |
| neonabyss.fandom.com / Items | 通过 | 现有 golden 未修改 |
| slaythespire.wiki.gg / Cards_List | 通过 | 现有 golden 未修改 |
| bindingofisaacrebirth.wiki.gg / Bloody Gust | 通过（审核后更新golden） | 七个字段名一致，正文逐字一致；ID 695/5.100.695、不同普通/Greed物品池目标均保留。仅接受共享renderer/handler导致的链接和字段渲染差异，修正缺scheme链接；未改策略 |
| growagarden.fandom.com / Crops | 失败：既有golden与策略不一致 | 使用相同工作区策略，当前输出与 HEAD d10858d 输出逐字一致（284314 bytes）。差异来自用户已有 tabber/cleanup 策略修改，非本change新增回归。保留golden，未机械接受diff；列表样本不能替代Apple实体infobox验收 |

## 关键证据入口

| 证据类型 | 证据路径/链接 | 对应 requirement/task |
| --- | --- | --- |
| 可复跑单元/集成 | `tests/test_convert_equivalence.py`、`tests/pipeline/test_*.py`、`tests/mediawiki-crawl.test.mjs`、`tests/test_strategy_lifecycle.py`、`tests/test_site_runner_strategy.py` | 核心八spec与3.1 |
| 兼容调用方 | `scripts/pipeline/tests/test_cat_dir_fallback_and_target_conflict.py`、`test_infobox_source_dir.py` | 更新旧mock/签名断言为当前行为契约 |
| 当次运行日志（临时，不是长期测试依赖） | `/tmp/chrome-agent-integrity-{python,node,legacy}.log`、`/tmp/chrome-agent-integrity-sample-<domain>.log` | 测试统计与站点差异 |
| doctor | `/tmp/chrome-agent-integrity-doctor.json`、`/tmp/chrome-agent-integrity-capabilities.json` | C10/C11 |
| 恢复与存储协议 | `docs/playbooks/mediawiki-extraction-recovery.md`、`docs/adr/0014-mediawiki-cache-identity.md` | 迁移边界与后续恢复 |

## 缺口与阻塞项

- 核心实现未发现未覆盖的本 change requirement。当前工作区尚未提交，未归档。
- Grow a Garden 站点样本仍有已归因基线差异；阻止宣称所有站点样本通过或全站恢复完成。后续站点策略/golden审核与真实实体验收保留为恢复工作，不覆盖用户既有修改。
- Python 3.9 仅做语法兼容检查；实际旧解释器运行未验证。
- 不以历史页数证明成功；HTML缺失必须重新获取。真实discovery、批量抓取、交付和下游ingest未执行。
