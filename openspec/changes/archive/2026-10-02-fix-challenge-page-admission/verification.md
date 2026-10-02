# Verification

## 验证结论

2026-10-02，执行人 Codex。验证目标为 HEAD `752a3872dd28ceef0420d825a5524d22ded40bf9` + 本 change 工作区修改；未提交、未归档。规范真源为本 change 的两份 delta specs。Python 213 tests、Node 121 tests 全部通过；doctor 9/9 与 capabilities 45/45 通过，OpenSpec strict validate、git diff --check、修改 Python 文件的 3.9 AST 语法检查和 Node syntax check 通过。

本轮完成正文准入闭环；原始 wiki.gg HTML 离线回放返回 admitted=false / challenge_page / cloudflare-managed / http_status=null。没有访问目标网站、绕过验证、发布站点策略或运行生产 crawl。不能据此宣称目标站点已能成功抓取。

## Spec-to-Implementation Coverage

| Requirement | 实现边界 | 验证 |
| --- | --- | --- |
| raw-html-admission | content_admission、probe、sample、CLI raw-first | zero-exit challenge / invalid output / selector tests |
| evidence-based-challenge-classification | shared classifier；protection_identifier 消费；CloakBrowser 标题误报修正 | normal content、403、normal cloak title |
| admission-evidence-contract | attempt admission/process_exit/http_status、CLI manifest、独立 raw evidence | unknown status、bridge status、stale output、diagnostic cache rejection |
| shared-consumer-admission | sample、CLI fetch/cache、MediaWiki cache/convert、CDP fetch/convert | sample、cross-path、standalone API、CDP、resume/assembly |
| deep-discovery | probe fallback + main early failure | recover/all blocked/main stop/entry tests |
| explore-preflight-failure | Node recognizes exit 0/2/3 structured outcomes | real entry failure、partial producer contract、existing internal handoff tests |

## Task-to-Evidence Coverage

| Tasks | Evidence / result |
| --- | --- |
| 1.1–1.3 | 读取治理与绑定文档；design 消费入口表、下方 evidence_map；脱敏 fixture tests/fixtures/challenge-wikigg.html。当前会话无 LSP 工具/skill，使用文本定位。 |
| 2.1–2.2 | 真实 adapter RED success→GREEN failure，未知状态保留 null。 |
| 2.3–2.6 | 正常文章误报与 probe 提前停止均观测 RED→GREEN；Cloak JSON 接口另有 RED KeyError→GREEN。 |
| 2.7–2.10 | main RED exit 0→GREEN exit 3；真实 CLI RED 丢 reason→GREEN 保留 content_unavailable；partial producer contract 附加测试直接 GREEN。 |
| 2.11–2.12 | sample RED ok=true→GREEN false；全部失败样本 self-check 补充测试 GREEN。 |
| 2.13–2.14 | selector RED 输出挑战 Markdown、无本地转换→GREEN 拒绝/同源本地转换；新 bridge status 测试直接 GREEN。 |
| 2.15–2.16 | cache/CDP RED 放行→GREEN；legacy JS cache RED 返回挑战→GREEN null；API standalone RED 不抛错→GREEN 拒绝；resume/assembly 补充测试 GREEN。 |
| 2.17–2.18 | 各边界上述 RED/GREEN 后增加正常跨路径等价，立即 GREEN（未另造一次等价失败）；registry + capabilities 45/45。 |
| 3.1–3.4 | 全量日志、原样本离线判定、语法和 strict validation；C10 runtime/skill 内容一致、installed-hash 等于验证 HEAD。 |
| 4.1–4.3 | 本文件与 writeback.md；7 个项目页已回写，永久规范按 requirement 合并，change 保留未归档。 |

额外实际 RED→GREEN：引擎退出 0 未写新文件时旧文件被误读；修复后不复用旧内容且 process_exit 仍为真实 0。crawl 目录扫描把失败诊断写入缓存的测试先 RED，改为 exact admitted path 后 GREEN。

## evidence_map[]

external_ref 为 `752a3872dd28ceef0420d825a5524d22ded40bf9+working-tree:fix-challenge-page-admission`；以下源码/测试证据均在本仓，运行日志在 outputs/debug/20261002-challenge-admission。既有 api-discovery/structure-mapping 的保留行为由代码对照检查，未再次访问真实 API。

| scenario_key | evidence_ref | external_ref | verification_result |
| --- | --- | --- | --- |
| captured-challenge-with-successful-process | tests/test_content_admission.py::test_probe_rejects_zero_exit_challenge | HEAD+working-tree（见上） | pass |
| invalid-output | tests/test_content_admission.py::test_normal_content_and_output_errors + test_zero_exit_without_new_output_does_not_reuse_old_file | HEAD+working-tree（见上） | pass |
| normal-article-and-widget | tests/test_content_admission.py::test_normal_content_and_output_errors + test_cloak_normal_title_is_not_rejected | HEAD+working-tree（见上） | pass |
| unknown-http-forbidden | tests/content-admission-fetch.test.mjs::bridge preserves observed HTTP errors | HEAD+working-tree（见上） | pass |
| unknown-status | tests/test_explore_probe_chain.py::test_full_success_dict | HEAD+working-tree（见上） | pass |
| rejected-artifact | tests/crawl_scrapling.test.mjs::failed page diagnostic HTML cannot be written to production cache | HEAD+working-tree（见上） | pass |
| rejected-sample | tests/test_content_admission.py::test_rejected_sample_does_not_convert + tests/test_explore_main_remediation.py::test_failed_samples_do_not_pass_empty_self_check | HEAD+working-tree（见上） | pass |
| selector-cannot-hide-challenge | tests/content-admission-fetch.test.mjs::fetch rejects challenge before selector | HEAD+working-tree（见上） | pass |
| cached-challenge-resume | tests/pipeline/test_conversion_resume.py::test_challenge_cannot_resume_or_enter_assembly + tests/content-admission-fetch.test.mjs::legacy Scrapling cache rejects challenges | HEAD+working-tree（见上） | pass |
| normal-cross-path-equivalence | tests/test_content_admission.py::test_normal_cross_path_equivalence + tests/content-admission-fetch.test.mjs::normal HTML is converted locally | HEAD+working-tree（见上） | pass |
| chain-engine-probe | tests/test_content_admission.py::test_all_engines_blocked_remain_failure | HEAD+working-tree（见上） | pass |
| api-discovery | scripts/explore/main.py Phase 2 (existing branch retained; no-admitted-content test proves it is gated) | HEAD+working-tree（见上） | pass |
| structure-mapping | scripts/explore/main.py Phase 3 (existing branch retained; main stopping test proves rejected input cannot reach it) | HEAD+working-tree（见上） | pass |
| protection-identification | tests/test_content_admission.py::test_normal_content_and_output_errors + original-admission.json | HEAD+working-tree（见上） | pass |
| direct-entry-without-pythonpath | tests/test_explore_startup.py | HEAD+working-tree（见上） | pass |
| strategy-gap-cli-startup | tests/explore-handoff.test.mjs::real strategy-gap CLI starts the real Explore entry | HEAD+working-tree（见上） | pass |
| challenge-fallback-recovery | tests/test_content_admission.py::test_probe_defends_success_candidates_and_recovers | HEAD+working-tree（见上） | pass |
| no-admitted-content | tests/test_content_admission.py::test_main_stops_without_admitted_content | HEAD+working-tree（见上） | pass |
| python-deps-missing | tests/explore-handoff.test.mjs::handoff before a run directory exists | HEAD+working-tree（见上） | pass |
| deep-discovery-execution-failure | tests/explore-handoff.test.mjs::handoff with run directory | HEAD+working-tree（见上） | pass |
| structured-content-failure | tests/explore-handoff.test.mjs::content failure survives real Python to CLI boundary | HEAD+working-tree（见上） | pass |
| structured-partial-outcome | tests/explore-handoff.test.mjs::recognized partial outcome retains exit-2 workflow semantics | HEAD+working-tree（见上） | pass |

## 关键证据入口

| 证据类型 | 证据路径 | 命令/用途 |
| --- | --- | --- |
| Python 全量 | outputs/debug/20261002-challenge-admission/python-tests.log | .venv/bin/python -m unittest discover -s tests -v |
| Node 全量 | outputs/debug/20261002-challenge-admission/node-tests.log | node --test tests/*.test.mjs |
| runtime | outputs/debug/20261002-challenge-admission/doctor.json | chrome-agent doctor --format json |
| registry | outputs/debug/20261002-challenge-admission/capabilities.json | chrome-agent doctor --check capabilities --format json |
| 原页复现 | outputs/debug/20261002-challenge-admission/original-admission.json | .venv/bin/python -m scripts.lib.content_admission outputs/20261002T132259-explore-darkestdungeon-wiki-gg-wiki-darkest-dungeon-wiki-1/probe_scrapling_get.html |

## 缺口与阻塞项

无本范围实施阻塞。判定只覆盖已知挑战结构/页面提示，不能证明所有网站或未来模板均可识别；不检测任意正文质量和登录墙。没有运行真实 Cloudflare 通关、真实浏览器集成或站点 site-samples（没有修改站点策略）。Python 3.9 验证为语法解析，测试运行解释器为应用层 Python 3.11。partial CLI 用例隔离 producer 验证协议，failure 用例走真实 main，二者证据边界不同。

所有新增/修改业务模块均有本轮对应行为测试；不存在无测试的新能力模块。保留原 package-lock.json 和未跟踪站点草稿。未创建 commit；日志属于忽略目录，跨机器应重跑 tracked tests。未执行 change 归档。

## 规范版本与同步校验

- specs/explore/spec.md SHA256: `577ef285aa9667f8ea30258d60f7ac0dbd47a08a4f67ccc1e81b902d8f0fc4fc`。
- specs/fetch-content-admission/spec.md SHA256: `e2a72688b20d962d25900a60527156810305e70f76cfbcac48f8262fc3728ec3`。
- 永久 Explore 两个变更块与 delta 逐块一致，其他 requirement 与 HEAD 逐块一致。新增永久准入规范与 delta requirement 正文一致。

## 归档记录

2026-10-02，Codex 按用户授权归档并准备提交。7/7 artifacts、28/28 tasks 完成；delta requirement 与永久规范逐块一致；归档前 capabilities 45/45 通过。复用实施结束的 Python 213 / Node 121 全量验证；归档仅移动 artifacts、更新证据引用及本记录，未修改实现。保留 .openspec.yaml，未包含原 package-lock.json 改动与未跟踪站点草稿。
