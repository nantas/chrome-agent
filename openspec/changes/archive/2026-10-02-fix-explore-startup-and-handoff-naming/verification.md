# Verification

## 验证结论

2026-10-02：本 change 两项缺陷修复通过增量场景验证，Python 全量 185/185、Node 第二轮全量 114/114、doctor 与能力注册检查均通过。依据 `specs/explore-workflow/spec.md` 和 `specs/governance/spec.md`。

根因分别为 main.py 缺少仓库根包搜索路径，以及 generateHandoff 错误地从 nowParts 获取 slug；现在入口自行建立路径，slug 从 target 归一化得到。无需用户配置 PYTHONPATH。

原始网站 Explore 仍返回 failure：已进入 scaffold 阶段后，遇到独立的 extraction_schema 不支持 strip_edit_sections/strip_toc 的错误。该错误不属于本次入口/命名修复范围，未修复网站策略或继续网站工作流。详情见 `evidence/original.json` 与新交接文件。

## Spec-to-Implementation Coverage

| Spec / requirement / scenario | 实现 | 测试与结论 |
| --- | --- | --- |
| explore-workflow / deep-discovery / direct-entry-without-pythonpath | scripts/explore/main.py 的启动路径初始化 | tests/test_explore_startup.py：真实子进程、repo/external cwd、无 PYTHONPATH，2 项通过 |
| explore-workflow / deep-discovery / strategy-gap-cli-startup | CLI 现有路由 → 真实 main.py | tests/explore-handoff.test.mjs：抵达 OFFLINE_PROBE_REACHED；原目标也实际抵达 scaffold，导入成功 |
| governance / handoff-storage-path / handoff-with-run-dir、target-derived-slug | scripts/chrome-agent-cli.mjs::generateHandoff | 精确 target slug、failure/JSON 路径、文件内容、runDir 和错误详情通过 |
| governance / handoff-storage-path / handoff-without-run-dir | 同一 generateHandoff | 预检失败仍写交接，outputs 仅含 handoffs，测试通过 |
| governance / handoff-storage-path / empty-normalized-slug | 同一 slugify(target) | 有效 Unicode URL 空 ASCII slug 回退 target，通过 |
| governance / handoff-storage-path / bounded-normalized-slug | 同一 slugify(target) | 大写/标点与超过 80 字符的 target，通过 |

deep-discovery 原有 chain-engine-probe/api-discovery/structure-mapping/protection-identification 行为块原样保留；本次未修改这些算法。离线 fixture 刻意在 probe 边界停止，因此不作为这些历史场景完整的端到端验证。原始真实请求也不代表完整探索成功。

## Task-to-Evidence Coverage

| Tasks | 证据 |
| --- | --- |
| 1.1–1.2 | 已读取 binding/proposal/specs/design、架构与治理/ADR；应用依赖可用，工作区既有 package-lock 改动保留 |
| 2.1–2.2 | evidence/regression.md 的真实入口 RED/GREEN；tests/test_explore_startup.py |
| 2.3 | 同上，真实 CLI → main.py → 可控网络边界 |
| 2.4–2.5 | evidence/regression.md 的 undefined RED、target slug GREEN；tests/explore-handoff.test.mjs |
| 2.6 | 同一 Node 测试 6/6；覆盖无 runDir、空 slug、归一化、长度 |
| 3.1 | evidence/python-tests.txt、node-tests.txt、node-tests-rerun.txt；首轮 venv 前置条件问题与第二轮结果均保留 |
| 3.2 | evidence/original.json；已解除原异常并记录新错误；停止网站工作流 |
| 3.3 | evidence/doctor.json、capabilities.json、regression.md 的 cmp/hash 同步证据 |
| 4.1–4.4 | 本文件、writeback.md、两个架构文档的修改与最终 strict validate 结果 |

## evidence_map

每项 `external_ref` 均为本仓 change 工作树，未创建 commit；`evidence_ref` 为当前 change 内可定位证据。

| scenario_key | evidence_ref | external_ref | verification_result |
| --- | --- | --- | --- |
| direct-entry-without-pythonpath | evidence/regression.md | working-tree:fix-explore-startup-and-handoff-naming | pass |
| strategy-gap-cli-startup | evidence/regression.md; evidence/original.json | working-tree:fix-explore-startup-and-handoff-naming | pass |
| handoff-with-run-dir | evidence/regression.md | working-tree:fix-explore-startup-and-handoff-naming | pass |
| handoff-without-run-dir | evidence/regression.md | working-tree:fix-explore-startup-and-handoff-naming | pass |
| target-derived-slug | evidence/original.json; evidence/regression.md | working-tree:fix-explore-startup-and-handoff-naming | pass |
| empty-normalized-slug | evidence/regression.md | working-tree:fix-explore-startup-and-handoff-naming | pass |
| bounded-normalized-slug | evidence/regression.md | working-tree:fix-explore-startup-and-handoff-naming | pass |

## 关键证据入口

| 证据类型 | 证据路径/链接 | 对应 requirement/task |
| --- | --- | --- |
| RED/GREEN 与同步摘要 | evidence/regression.md | 两个 requirement，2.x / 3.x |
| 全量回归 | evidence/python-tests.txt、evidence/node-tests-rerun.txt | 3.1 |
| 原始命令结果 | evidence/original.json | 3.2 |
| 新独立故障交接 | ../../../../outputs/handoffs/20261002T103634-explore-darkestdungeon-wiki-gg-wiki-darkest-dungeon-wiki-1/handoff.md | 3.2，新问题 |
| doctor / capabilities | evidence/doctor.json、evidence/capabilities.json | 3.3 |

## 缺口与阻塞项

- 当前两项修复无剩余实现/测试阻塞；J3：修改的两个模块均有真实调用方式测试，无新增 scripts 实现模块。
- 原网站 Explore 完成受独立 scaffold schema 错误阻塞，应另行诊断/建 change，不能据此宣称本次已完成网站抓取。
- 用户已授权归档；归档阶段按 delta 所列 merged spec 定位同步两个完整 requirement 块，并保留其它要求。
