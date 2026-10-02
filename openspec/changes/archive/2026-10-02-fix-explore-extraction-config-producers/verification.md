# Verification

## 验证结论

2026-10-02，执行人 Codex。change `fix-explore-extraction-config-producers` 的四个 requirement / 十二个 scenario 通过本地验证，可进入归档。OpenSpec strict validate 与 git diff --check 均通过。执行基线 HEAD `777d5b1e2520b0a630f26b19a10759b1149f4538` + 当前未提交工作区；以上为实施验证基线；2026-10-02 用户随后授权归档并提交，本次归档不改变已验证代码。

验证真源为 `specs/explore-scaffold/spec.md`，SHA256: `ddd9c11309f4164a7f84db60ea7bbda8e23faad69c514df500cb77872a56df0b`。全量 Python 198 passed；Node 114 passed；doctor 与 capabilities 均 success。三个修改代码模块均有对应测试，无新增能力实现模块，无共享库/runtime/CLI/skill 修改；C10/C11 同步不适用。模板不是站点策略，无站点策略发布；原有 package-lock.json 改动保留。

## Spec-to-Implementation Coverage

| Requirement | 实现 | 验证 |
| --- | --- | --- |
| template-content | sites/templates/mediawiki.yaml、mediawiki-wiki-gg.yaml；既有 generate schema admission 保留 | registry 遍历 generic/wiki.gg/Fandom 真实生成与共享 preprocess_html |
| auto-remediation-extended | scripts/explore/self_check.py plan_remediation 与兼容 auto_remediate；main.py 规划报告接线 | 全部 FIXABLE_ISSUES、深拷贝、批量排序去重、完整/缺失/非法证据、真实 wrapper/table/space/lazyload 消费者 |
| ki-lifecycle-consumption | unresolved 携带原 issue/fixable_type；main 保留 self-check failure | 原 detail/status/身份未更改，失败 Gate 仍返回 exit 2，不冻结 |
| feedback-extraction-admission-before-write | scripts/explore/iterate.py 规划候选、既有/候选 MediaWiki schema 校验、报告与 frontmatter 回写 | 非法字节不变/convert 0 次、真实预处理、BODY 和身份字段保留、image 部分支持与 static 边界 |

## Task-to-Evidence Coverage

| 任务 | 证据与结果 |
| --- | --- |
| 1.1–1.2 | 已核对 binding/design/spec 与必读文档、调用者 main/iterate；旧两个模板 offline-repro 报 unsupported operation；规划器放既有 self_check 模块，无新能力 |
| 2.1–2.4 | generic RED 旧 strip_edit_sections/strip_toc 拒绝 → generic GREEN；wiki.gg 同样 RED → registry 全集 3 平台 GREEN，正文与 selectors/image rules 保留 |
| 2.5–2.7 | 首个 base64 缺证据用例 RED AttributeError: plan_remediation 缺失 → GREEN；扩展全部 issue、真实 lazyload/其他消费者与兼容测试通过。完整证据 lazyload 用例加入后直接 GREEN，未单独观察该分支 RED |
| 2.8–2.9 | iterate RED：旧规则消费者 ValueError、非法规则仍写入/转换、image 虚构操作 → GREEN；反馈准入/边界用例通过；外部 iterate --help RED scripts 包缺失 → 根路径初始化后 GREEN |
| 2.10–2.11 | main RED：unsupported-only 与 unchanged 均转换3次 → GREEN 分别1/2次；两次有效更新仍最多转换3次；原 failure 与 Gate 保留；已配置 remedy 无变化的失败诊断 RED（unresolved 空）→ caller 保留原 issue 与无进一步修复原因 GREEN |
| 3.1–3.2 | Python198/Node114；原 offline repro 2 tests GREEN；临时 fixture 清理，无生产注册表修改 |
| 3.3 | 仓库外 cwd=/tmp、移除 PYTHONPATH，通过 doctor 后运行原 URL；返回 partial_success，已越过 schema 崩溃 |
| 3.4 | doctor/capabilities success；无 C10 tracked 文件与新增能力文件 |
| 4.1–4.4 | 本文件 evidence_map；writeback.md 对应三页结果；严格校验与 tasks 收口 |

## evidence_map[]

external_ref 对全部本仓测试为 `HEAD:777d5b1e + working-tree:fix-explore-extraction-config-producers`。证据文件可直接运行，测试日志在本地忽略目录，跨机器以 tracked 测试复现为准。

| scenario_key | evidence_ref | external_ref | verification_result |
| --- | --- | --- | --- |
| template-yaml-frontmatter | `tests/test_explore_template_contract.py` (assert_template) | HEAD:777d5b1e + working-tree | pass |
| registered-mediawiki-templates-are-admissible | `tests/test_explore_template_contract.py` (test_registered_mediawiki_templates) | HEAD:777d5b1e + working-tree | pass |
| edit-and-toc-cleanup-preserves-body | `tests/test_explore_template_contract.py` (test_generic_template / test_wiki_gg_template) | HEAD:777d5b1e + working-tree | pass |
| implemented-fixes-produce-valid-rules | `tests/test_explore_remediation_plan.py` (test_all_issue_types_and_deterministic_batch / test_supported_actions_reach_consumers) | HEAD:777d5b1e + working-tree | pass |
| lazyload-with-complete-evidence | `tests/test_explore_remediation_plan.py` (test_lazyload_consumer_existing_and_explicit_evidence) | HEAD:777d5b1e + working-tree | pass |
| unsupported-or-under-specified-remediation | `tests/test_explore_remediation_plan.py` (test_missing_lazyload_evidence / test_all_issue_types_and_deterministic_batch) | HEAD:777d5b1e + working-tree | pass |
| retry-only-on-admitted-change | `tests/test_explore_main_remediation.py` (全部三个主循环用例) | HEAD:777d5b1e + working-tree | pass |
| unresolved-remediation-retains-failure | `tests/test_explore_main_remediation.py` (test_unsupported_only_no_retry_and_retains_identity) | HEAD:777d5b1e + working-tree | pass |
| supported-feedback-round-trip | `tests/test_explore_iterate.py` (test_edit_toc_real_consumer_roundtrip) | HEAD:777d5b1e + working-tree | pass |
| invalid-candidate-preserves-file | `tests/test_explore_iterate.py` (test_invalid_existing_config_preserves_bytes / test_invalid_candidate_preserves_bytes) | HEAD:777d5b1e + working-tree | pass |
| missing-lazyload-evidence-preserves-valid-actions | `tests/test_explore_iterate.py` (test_image_partial_and_static_boundary) | HEAD:777d5b1e + working-tree | pass |
| non-mediawiki-boundary-preserved | `tests/test_explore_iterate.py` (test_image_partial_and_static_boundary) | HEAD:777d5b1e + working-tree | pass |

## 关键证据入口

- Python：`python3 -m unittest discover -s tests -v` → `outputs/debug/20261002-extraction-config-validation/python-tests.log`。
- Node：`node --test tests/*.test.mjs` → `outputs/debug/20261002-extraction-config-validation/node-tests.log`。
- 原始离线环：`python3 outputs/debug/20261002-scaffold-schema/repro.py -v` → `outputs/debug/20261002-extraction-config-validation/offline-repro.log`。正式覆盖见 template contract tests。
- 预检：`outputs/debug/20261002-extraction-config-validation/doctor.json` 与 `capabilities.json`，result=success、checks 全部 ok。
- 原 URL：`outputs/debug/20261002-extraction-config-validation/explore.json`；原 probe：`outputs/20261002T121221-explore-darkestdungeon-wiki-gg-wiki-darkest-dungeon-wiki/probe_scrapling_get.html`。
- 本地生成草稿留档：`outputs/debug/20261002-extraction-config-validation/strategy-draft.md`；从临时验证产生的 sites 路径迁移至证据目录，未发布/冻结/注册。

## 缺口与阻塞项

本 change 无实施阻塞。原 URL 的返回为 partial_success：MediaWiki API 探测成功，草稿生成成功，但 HTML 标题为 “Just a second...” 且含 Cloudflare 挑战标记，未提供 samples，因此未运行实际网站 S1–S12 或正文提取。不能宣称网站抓取成功；挑战页被引擎标为 success、平台 variant/profile 推导属独立后续问题。本轮未扩展该范围、未绕过 Gate 或启动 crawl。

未实现的七个无消费者 issue 修复继续 unresolved；base64 缺证据亦 unresolved。旧 auto_remediate 字典接口无法返回诊断，需报告的现有 main/iterate 已迁移到 planner。非 MediaWiki 继续既有边界。


## 归档检查

2026-10-02，schema `orbitos-change-v1` 全部七个 artifact done，tasks 21/21。归档前再次运行 `chrome-agent doctor --check capabilities --format json`：success，44/44 checks ok（本地 `/tmp/chrome-agent-archive-capabilities.json`）。复用实施结束时 Python198/Node114 结果，归档只合并规范及更新文档引用，代码未再修改。

冻结规范合并目标：`openspec/specs/explore/explore-scaffold.md`，三个 MODIFIED 与一个 ADDED requirement。独立 `openspec/specs/explore-scaffold/spec.md` 保留，未创建平行真源。归档位置 `openspec/changes/archive/2026-10-02-fix-explore-extraction-config-producers/`，保留 .openspec.yaml。

合并验证：四个 delta requirement 正文逐块匹配；未涉及 requirement 逐块与 HEAD 比较保留；独立样本推荐文件与 HEAD 字节相同。change strict validate 通过。`openspec validate explore --type spec --strict` 无法直接校验历史聚合文件布局（explore/spec.md 不存在），使用上述逐块检查验证实际 merged spec，未改变原规范目录组织。
