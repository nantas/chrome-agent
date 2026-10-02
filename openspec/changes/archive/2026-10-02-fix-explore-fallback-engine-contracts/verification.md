# Verification

## 验证结论

2026-10-02，执行者 Codex。验证对象为本 change specs 和基于 b3092c3 的当前工作树；未创建提交，不将基线 SHA 当作已包含本次修改的 commit。

核心修复通过：Python 225/225、Node 132/132；doctor success，三个引擎版本均匹配；capabilities success。Python 3.9 语法、Node 语法、shell 语法和 git diff --check 通过。未新增实现模块，无新增能力注册项；未变更引擎版本清单。

真实标准 doctor→explore 已执行。前置 doctor 正确报告可选 CloakBrowser not_installed、partial_success、dispatch_allowed=true；随后预检安装清单中的 0.4.3。Scrapling 与 Obscura 正确拒绝挑战页；CloakBrowser 返回 HTTP 200、正常标题与正文。Explore 为 partial_success：未冻结策略，后续策略草稿与样本审查仍待完成，不称为完整生产抓取成功。

## Spec-to-Implementation Coverage

| Requirement | 实现 | 验证 |
| --- | --- | --- |
| obscura-stdout-acquisition | probe_chain.py::_capture_html / _run_obscura_fetch | 严格 argv 可执行 fixture、空/非零/陈旧文件/挑战页；真实 Obscura 成功执行并返回挑战 HTML |
| cloakbrowser-preflight-before-dispatch | probe_chain.py::_cloakbrowser_preflight、CLI runCloakbrowserFetch、cloakbrowser-cli.sh | 真实 shell + 临时 managed root + 受控 uv；Node 路径校验；真实原站点取得正文 |
| explore-attempt-evidence | probe_chain.py::probe、CLI runExplore | mixed chain 与 pending；真实 Python→CLI 内容失败及内部协议错误 handoff；真实运行 JSON |
| complete-per-engine-version-report | engine-version-check.sh | 真实脚本的缺失/超时/版本解析/导入故障，仍输出其他引擎记录 |
| doctor-validates-version-check-outcome | CLI runEngineVersionCheck | 缺脚本、启动/超时、空/坏 JSON、缺失/重复记录、退出码矛盾和合法非零报告 |
| explicit-optional-engine-readiness | CLI runDoctor | non-blocking optional / blocking required与未知 / healthy / freshness Gate；真实安装前后 doctor |

## Task-to-Evidence Coverage

证据目录：`outputs/fallback-contracts-validation/`。测试源码为稳定可重跑证据；outputs 是本次本地运行记录，不作为源码提交内容。

| Tasks | Evidence |
| --- | --- |
| 1.1–1.2 | binding 基线；version-before.stderr、cloak-before.txt、obscura-help.txt；tests 中各 requirement 对应行为 |
| 2.1–2.2 | test_engine_version_check.py；version-red.txt、version-more-red.txt、version-green.txt |
| 3.1–3.2 | engine-health.test.mjs；health-red.txt、health-green.txt |
| 4.1–4.2 | readiness-red.txt、readiness-green.txt；doctor-before-live.json、doctor-after-live.json |
| 5.1–5.3 | test_fallback_contracts.py；obscura-red.txt、obscura-green.txt、obscura-help.txt、obscura-local.json/.stderr；原站点 Obscura attempt |
| 6.1–6.2 | cloak-red.txt、cloak-green.txt、cloak-node-red.txt、cloak-node-green.txt；pin-red.txt、pin-green.txt；protocol-red.txt、protocol-green.txt |
| 7.1–7.2 | evidence-red.txt、evidence-cli-red.txt、evidence-green.txt、evidence-cli-final.txt；test_content_admission.py 既有恢复/挑战回归 |
| 8.1 | python-suite.txt（225）、node-suite.txt（132）；语法检查和 diff 检查 |
| 8.2 | doctor-after-live.json、capabilities.json；全局 runtime/skill 与源文件 cmp 一致，installed hash = 当前 HEAD |
| 8.3 | explore-live.json/.stderr、content-inspection.json；原站点运行目录见下 |
| 9.1–9.3 | 本文件与 writeback.md，四份 architecture 文档及永久规范 |

## evidence_map

external_ref 对全部条目为 `repo://chrome-agent` 当前未提交工作树（基线 b3092c3），不冒充已发布构建。

| scenario_key | evidence_ref | verification_result |
| --- | --- | --- |
| normal-stdout | tests/test_fallback_contracts.py::test_obscura_supported_argv_and_stdout | pass |
| rejected-or-absent-output | tests/test_fallback_contracts.py::test_obscura_never_promotes_stale_output / test_obscura_challenge_is_rejected_and_stderr_separate | pass |
| installed-custom-root | tests/test_fallback_contracts.py::test_cloak_custom_root_preflight | pass |
| missing-engine-lazy-install | tests/test_fallback_contracts.py::test_cloak_missing_environment_is_lazily_installed | pass |
| failed-or-invalid-preflight | tests/test_fallback_contracts.py::test_cloak_invalid_preflight_never_runs_fetch；tests/engine-health.test.mjs | pass |
| mixed-failure-chain | tests/test_fallback_contracts.py::test_probe_persists_mixed_failure_stages_and_pending；tests/explore-handoff.test.mjs | pass |
| pending-is-not-executed | tests/test_fallback_contracts.py::test_probe_persists_mixed_failure_stages_and_pending | pass |
| recovery-preserves-admission | tests/test_content_admission.py::test_probe_defends_success_candidates_and_recovers；outputs/fallback-contracts-validation/explore-live.json | pass |
| one-executable-missing | tests/test_engine_version_check.py::test_missing_does_not_abort_other_engines | pass |
| inspection-error | tests/test_engine_version_check.py::test_timeout_is_distinct_from_missing / test_invalid_version_is_inspection_failure | pass |
| broken-checker | tests/engine-health.test.mjs | pass |
| valid-unhealthy-json | tests/engine-health.test.mjs | pass |
| optional-missing-only | outputs/fallback-contracts-validation/doctor-before-live.json | pass |
| required-or-unknown-failure | tests/engine-health.test.mjs | pass |
| healthy-complete-check | outputs/fallback-contracts-validation/doctor-after-live.json | pass |

## 关键证据入口

原站点运行：`outputs/20261002T144743-explore-darkestdungeon-wiki-gg-wiki-darkest-dungeon-wiki-1/`。

- discovery-result.json、probe-chain.json：完整尝试和 discovery 结论。
- probe_obscura_fetch.html.attempt.json：exit 0，但 admission=false/challenge_page。
- probe_cloakbrowser_fetch.html.attempt.json：exit 0、HTTP 200、admitted=true，标题 Darkest Dungeon Wiki 1 - Official Darkest Dungeon Wiki。
- content-inspection.json：正文 #mw-content-text 存在，可见文本 2775 字符。

## 缺口与范围说明

- 真实 Obscura 拒绝 localhost 私有地址；本地 HTTP 验证受其策略阻挡（blocked_reason_code=engine_private_address_policy），不是 stdout 成功证据。原站点运行补充了真实参数与 stdout 证据。
- site-samples 命令执行后报告 0 samples/skipped，不能作为策略质量通过证据；未新增/发布生产策略。标准 Explore 自动生成了未跟踪站点目录中的草稿，该目录不纳入本 change 的代码提交。
- 未运行人工浏览器 fallback，未接管用户 Chrome。未冻结策略、未执行 crawl。
- J3：修改的 Python/Node 模块均有对应回归，无新实现模块缺测试。旧 CloakBrowser envelope 测试更新预检 fixture，以继续验证真实响应准入。
- 本轮仅完成 apply 和回写，不自动归档或提交。
