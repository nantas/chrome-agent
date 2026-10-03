# Verification

## 验证结论

2026-10-03，执行者 Codex。验证对象为工作区 `fix-gzip-sitemap-discovery` 实现，基于 HEAD `9cc4500f2a3d6dff84bc0bf8a72a3462e6ba883e` 的未提交修改。新增 `tests/sitemap-discovery-files.test.mjs`，没有新增能力实现模块；J3 对应测试完备检查通过。

- 相关回归：58/58 通过（新文件 10、现有 sitemap 39、explore handoff 9）。
- Node 全量：`node --test tests/*.test.mjs`，142/142 通过。
- Python 全量：`.venv/bin/python -m unittest discover -s tests -v`，232/232 通过。
- doctor：success、dispatch_allowed=true；capabilities：success。
- 历史文件使用生产 `readSitemapContent` → parser → resolver 离线重放：957、99，去重 1056，errors=[]。
- 真实 CLI 在线验收：success，discovery-only=true，confirmation_bypassed=false，1055 pages、warnings=[]、failure_rate=0；未运行 extraction。
- `git diff --check` 通过。工作区原有 Python/策略/table change 未由本变更修改；测试结果包括其当前状态。

## Spec-to-Implementation Coverage

规范入口：`specs/sitemap-driven-crawl/spec.md`。

| Requirement | 实现 | 验证 |
| --- | --- | --- |
| sitemap-discovery-fetch-and-parse | readSitemapContent；顶层/子文件共用字节解码；parser 保持不变 | 新文件测试 1–3；原 sitemap 测试；在线 CLI |
| sitemap-index-partial-failure-resilience | resolveSitemapIndex 优先保留显式失败原因，仍兼容 HTTP 错误；既有部分失败汇总 | 新文件测试 6–7；原 resolver 404/部分失败用例 |
| sitemap-decompression-failure-diagnostics | helper 捕获 zlib 错误；顶层 sitemap_decompress_error；子项 decompress_error | 新文件测试 4–7 |
| sitemap-handoff-existing-evidence | discovery 收集实际响应；internalFailure 传 artifacts；generateHandoff 检查存在性并去重 | 新文件测试 8–10；explore-handoff 回归 |

### evidence_map

`external_ref` 均为上述 HEAD + 本 change 工作区实现；`evidence_ref` 为当前仓可定位文件。下表覆盖本次新增/变更场景；沿用的普通 XML、HTTP、嵌套索引等行为由原 sitemap 测试继续回归。

| scenario_key | evidence_ref | external_ref | verification_result |
| --- | --- | --- | --- |
| gzip-top-level-urlset | tests/sitemap-discovery-files.test.mjs（discovery reads gzip top-level） | 9cc4500f + working tree | pass |
| gzip-index-and-mixed-children | tests/sitemap-discovery-files.test.mjs（gzip index merges mixed） | 9cc4500f + working tree | pass |
| encoding-determined-by-bytes | tests/sitemap-discovery-files.test.mjs（gzip index merges mixed） | 9cc4500f + working tree | pass |
| corrupt-gzip-partial-failure | tests/sitemap-discovery-files.test.mjs（one corrupt gzip child） | 9cc4500f + working tree | pass |
| all-children-corrupt-gzip | tests/sitemap-discovery-files.test.mjs（all corrupt children） | 9cc4500f + working tree | pass |
| corrupt-top-level-gzip | tests/sitemap-discovery-files.test.mjs（corrupt top-level gzip） | 9cc4500f + working tree | pass |
| decoded-content-is-not-xml | tests/sitemap-discovery-files.test.mjs（decoded non-XML；all corrupt children） | 9cc4500f + working tree | pass |
| all-sub-sitemaps-failed-with-raw-files | tests/sitemap-discovery-files.test.mjs（failure handoff links raw） | 9cc4500f + working tree | pass |
| network-failure-before-file-created | tests/sitemap-discovery-files.test.mjs（network failure does not link） | 9cc4500f + working tree | pass |
| existing-manifest-and-logs-retained | tests/sitemap-discovery-files.test.mjs（legacy handoff callers） | 9cc4500f + working tree | pass |

## Task-to-Evidence Coverage

| Tasks | 证据与结果 |
| --- | --- |
| 1.1–1.2 | 按 binding/spec/design 建立 VM 编排 seam：真实生产函数、fs、zlib、parser、manifest/summary 与 handoff，只替换 curl 网络边界；临时 fixture 自动清理 |
| 2.1–2.2 | RED 返回 failure 而非 success；子文件接入解码后 GREEN |
| 2.3–2.4 | RED 顶层 gzip 返回 failure；接入相同 helper 后 GREEN；混合编码、后缀反例、过滤去重通过 |
| 2.5–2.6 | RED zlib unexpected end of file 未捕获；映射错误后 GREEN；解压后的 HTML 仍为 parse_error |
| 2.7–2.8 | RED 损坏子文件的 undefined content 导致 parser 异常；传播结构化原因后 GREEN；全失败契约通过 |
| 2.9–2.10 | RED `_sitemap.xml must be linked`；接通 artifacts 与存在性检查后 GREEN；旧调用者和失效文件回归通过 |
| 3.1–3.2 | 58 项相关测试日志；原始捕获文件离线重放数字与诊断一致 |
| 3.3 | runtime/skill 与仓库源比较一致后执行 Case 6 同步；installed-hash 为 HEAD；全局 doctor 成功 |
| 3.4 | 在线输出目录 `outputs/dd1-gzip-sitemap-verification-20261003/`；1055 条过滤后 URL |
| 3.5 | Node 142/Python 232 通过；doctor 与 capabilities 日志；diff 检查 |
| 4.1–4.3 | 本文、writeback.md、两份架构文档及永久 spec 同步记录；2026-10-03 用户要求归档后整理提交，已完成归档 |

## 关键证据入口

| 证据类型 | 证据路径/链接 | 对应 requirement/task |
| --- | --- | --- |
| 稳定回归源码 | `tests/sitemap-discovery-files.test.mjs` | 四个 requirement |
| 相关/全量测试 | `outputs/gzip-sitemap-change-evidence/gzip-sitemap-targeted.log`、`gzip-sitemap-node-all.log`、`gzip-sitemap-python-all.log`（同目录） | 3.1、3.5 |
| 环境/能力 | `outputs/gzip-sitemap-change-evidence/gzip-sitemap-doctor.json`、`gzip-sitemap-capabilities.json`（同目录） | 3.3、3.5 |
| 在线 CLI 结果 | `outputs/gzip-sitemap-change-evidence/gzip-sitemap-live.log` | 3.4 |
| 页面清单/摘要 | `outputs/dd1-gzip-sitemap-verification-20261003/page_manifest.json`、`discovery_summary.json`（同目录） | 3.4 |
| 原始事故响应 | `outputs/dd1-full-discovery/_sitemap.xml`、`_sitemap_sub_0.xml`、`_sitemap_sub_1.xml`（同目录） | 3.2 |

## 缺口与阻塞项

本修复无阻塞。outputs 为本机可清理证据，稳定回归不依赖这些文件。1056 是捕获文件过滤前基线，1055 是本次实时策略过滤后数量；不承诺这些 URL 都属于 DD1，也未验证正文提取质量。

本 change 为 repo-local 执行，binding 仅要求当前仓文档回写；已读取外部标准供证据格式参考，不声称完成 OrbitOS 外部项目治理回写。实现验证时尚未提交；2026-10-03 已按用户要求归档，随后整理为独立提交。
