# Verification

## 验证结论

验证对象：`fix-conversion-structure-and-audit-fidelity` 当前未提交工作区，基于 `4c781e309571d8510bf575794a95d577830b9faa`；2026-10-03。共享 tooltip DOM、列表包装、配置标题配对、S6、S5 版本归因及 tracked batch 审计已实施。用户补充批准四项精确 label_aliases，已同步设计和 specs。

- Python 全量 287/287、Node 全量 152/152、站点样本 13/13 通过；capabilities doctor success；Python 3.9 语法与 diff 检查通过。
- 原始四页配置路径重放通过：Inn 94/94、Enemies 14 个分组恢复、Shambler 109 图、Fallen Templar Skills 独立；Kingdoms 3 个分组另由全量与自包含测试覆盖。
- 209 页 core 与本地化重放均无输入错误；S1 全部通过，图片与旧正式产物 multiset 209/209 相等；逐表网格 209/209 等价（忽略空白并先统一 collection 原有双括号链接包装，不更改数据/行列顺序）。所有结构断言通过。
- 全页可见词项仅 Death 的 ResistedStun→Resisted Stun、Flame 的 SPDwhile→SPD while 发生变化，符合原 DOM 边界；没有内容删除。
- 只更新经审查的 3 个 DD2 golden：Plague Doctor、Trinkets、Tokens。独立图片、链接目标集合、可见词项检查全部相等；差异为合法空白/图标链接与嵌套列表结构恢复。其余 10 个 golden 未改。
- 本 change 的验收通过不等于 collection 每项检查全绿。S5 仍有 Crypt Keeper 合并单元格图标去重后的 `or or` 归因边界；没有降低阈值或隐藏失败。S9 歧义和无来源适用条件显式 skip，详见下节。

## Spec-to-Implementation Coverage

| Requirement | 实现 | 证据 |
| --- | --- | --- |
| tooltip-normalization-preserves-dom | converter.merge_tooltip_links 使用 DOM 精确解包/链接合并，普通 span 保留；空标题不输出 | tests/test_conversion_structure.py；Fallen Templar 消融 |
| wrapped-list-items-preserved | preprocessor 结构严格减少的迭代，仅解包最近列表所属 li | tests/test_conversion_structure.py 深层包装/编号；tests/lib/test_list_item_wrappers.py；Shambler |
| configured-semantic-heading-pairs | heading_pairs + normalize_heading_pairs，精确别名、源 id 提升到 heading、可见 label 资产保留 | tests/test_heading_normalization.py（14/3、id 唯一、幂等、反例） |
| cleanup-workarounds-require-conversion-evidence | 三项操作退出 DD2 配置；实现/注册保留兼容；空 id/name 与媒体保留 | ablation.json；tests/test_conversion_structure.py |
| structural-fix-shared-entry-proof | 同一 fixture 经过原有真实镜像 | tests/test_convert_equivalence.py；tests/crawl-strategy-conversion.test.mjs |
| s6-table-data-row-classification | 按表块位置/单元格识别分隔行，短横线数据保留，来源使用保留范围 | tests/test_audit_fidelity.py；tests/test_table_section_integrity.py；Inn |
| s5-source-attributed-version-anomalies | 完整可见候选与源有限预算，code/URL 排除；表格单元格内声明的换行折叠独立处理 | tests/test_audit_fidelity.py；tests/test_self_check_source.py；Lair |
| s8-declared-heading-semantics | 原 HTML 的 heading 级别/数量与配对可见名称，双向缺失/重复校验；正确解析括号链接 | tests/test_heading_normalization.py；tests/test_self_check_integration.py |
| source-aware-offline-batch-audit | scripts/explore/batch_audit.py 接收 manifest，结构化来源、映射、输入错误/覆盖率与安全输出路径 | tests/test_batch_audit.py；core/localized 报告；临时 collection 仅适配调用 |
| semantic-heading-normalization-config | schema 校验字段/类型/CSS/别名；无配置不恢复隐藏内容 | tests/test_heading_normalization.py；strategy frontmatter |
| heading-config-registration-and-samples | capability normalizations/audits 注册、schema/策略一致 | capabilities.json；site-tests.log；sample-review/report.json |

## Task-to-Evidence Coverage

| Tasks | 执行与证据 |
| --- | --- |
| 1.1–1.2 | before/ 保存原工作区；baseline-red.log 五项 RED、baseline-probes.log 现场对照。正式 fixture 全部自包含。 |
| 2.1–2.4 | 普通 span RED→DOM 修复 GREEN；五层包装 RED→无固定轮数 GREEN；合法 tooltip/different target 与子列表回归。 |
| 2.5–2.10 | schema 不接受字段 RED→校验 GREEN；标题输出 RED→配对 GREEN；错误层级误通过 RED→S8 GREEN；用户批准别名后增加别名 RED→GREEN。 |
| 2.11–2.14 | 短横线数据误删 RED→计数 GREEN；Config2fc RED→source note GREEN；括号 URL/图标链接解析补充 RED→GREEN。 |
| 2.15–2.16 | P-6 两项没有独立标题修复证据；空锚点删除 RED→保护 GREEN；16 次组合均保留 Skills，各页面 4/8 与无操作字节一致，其余仅 nowrap 展现空白差异，不是独立结构收益。 |
| 2.17–2.18 | 新 batch 模块缺失 RED→真实 CLI/API GREEN；缺 scope/URL、未映射本地链接、输出覆盖保护与原路径协议测试。 |
| 2.19–2.20 | 共享镜像扩充结构 canary；空 heading 导致 CV5 漂移 RED→不输出空标题 GREEN；主/iterate 与 crawl 真实回归通过。 |
| 3.1–3.2 | all-pages/ 保存输入/配置/hash；209 页 core 与独立 localized-work/pages；collection/table/link 对照与剩余缺口分类。未覆盖正式产物，未重新抓取。 |
| 3.3–3.4 | python-tests.log、node-tests.log、site-tests.log、capabilities.json；只有 golden 差异经独立检查后更新。未修改 C10 触发文件，不需要全局副本重装。 |
| 4.1–4.3 | 本文件、writeback.md 与 binding 所列本地文档/原 handoff 追加；不声称跨仓治理回写或归档完成。 |

## 关键证据入口

所有下列本地输出均为补充诊断，不是正式测试依赖。

| 证据类型 | 证据路径 | 对应任务 |
| --- | --- | --- |
| 初始快照/RED | outputs/debug-dd2-followup/before/；baseline-red.log | 1 |
| 消融 | outputs/debug-dd2-followup/ablation.json | 2.15–2.16 |
| 原现场收敛 | outputs/debug-dd2-followup/final-repro.json | 原始四页 |
| core 审计 | outputs/debug-dd2-followup/all-pages/manifest.json、audit.json、structure.json | 3.1 |
| 本地化重放审计 | outputs/debug-dd2-followup/localized-work/batch-audit-report.json | 3.1 |
| 内容/表格对照 | outputs/debug-dd2-followup/all-pages/collection-comparison.json、table-comparison.json | 3.2 |
| 链接定位 | outputs/debug-dd2-followup/localized-links.json | 3.2 |
| 样本基线评审 | outputs/debug-dd2-followup/sample-review/report.json 与逐页 .diff/.before/.after | 3.3 |
| 测试/能力 | outputs/debug-dd2-followup/python-tests.log、node-tests.log、site-tests.log、capabilities.json | 3.3–3.4 |

## 缺口与阻塞项

本次定义的实现任务无阻塞项；以下全量数据验证限制保留原始结果，不解释为 pass：

1. **Crypt Keeper / S5**：colspan 展开会保留重复标签但只保留一次图标，副本中的 `or` 因失去图标间隔被识别成重复。源表与 209 页逐格对照证明数据未丢失；该合并单元格投影归因不在本次版本标识修复范围。core/localized 均返回 failed_pages=1、overall_pass=false，CLI exit 2。
2. **core 覆盖率**：S1 209 pass；S5 208 pass/1 fail；S6 156 pass/53 skip（无数据表）；S8 193 pass/16 skip（无意图标题）；S9 148 pass/61 skip（正文导航重叠）。S3/S12 无 infobox 依据而 skip，S10 205 无视频 skip/4 pass。complete_validation=false。
3. **local mapping**：本地化报告 S2/S11 166 pass/43 skip；73 个未提供来源映射的目标被明确记录，主要跨 DD1。S9 112 pass/97 skip 包含映射缺口及重叠歧义。缺口不被误判成干净导航验证。
4. **anchor 限制**：12,769 条集内相对链接的文件目标均存在；79 条跨 DD1 链接未复核。622 个 fragment 没有与生成标题的精确文本匹配，包含既有 collection 脚本未转换的本页锚点、引用脚注、下划线形式及页面级/最近标题回退。本次保留配对标题源 ID 并更新现场 heading map，未扩展为通用锚点重写器；没有宣称这些链接精确定位已全部通过。
5. 209 页视频元数据边界触发次数为 0；core 重放用拒绝网络的替身，不验证远程服务。未重新抓取，未发布重生成 collection。
6. 三项旧 workaround 的实现和能力注册仍保留，避免破坏其他调用者；仅撤出 DD2 配置。P-6 不再作为“markdownify 状态机缺陷已证明”的结论。

## evidence_map

- scenario_key: convert/ordinary-span-before-block
  evidence_ref: tests/test_conversion_structure.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: convert/nested-tooltip-and-links
  evidence_ref: tests/test_conversion_structure.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: convert/distinct-link-targets
  evidence_ref: tests/test_conversion_structure.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: convert/wrapped-reward-list
  evidence_ref: tests/test_conversion_structure.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: convert/deep-wrappers-and-nested-numbering
  evidence_ref: tests/test_conversion_structure.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: convert/enemies-group-headings
  evidence_ref: tests/test_heading_normalization.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: convert/mismatched-or-unconfigured-pair
  evidence_ref: tests/test_heading_normalization.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: convert/repeat-normalization
  evidence_ref: tests/test_conversion_structure.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: convert/fallen-templar-ablation
  evidence_ref: outputs/debug-dd2-followup/ablation.json
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: convert/anchor-and-media-safety
  evidence_ref: tests/test_conversion_structure.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: convert/mirror-and-loss-canaries
  evidence_ref: tests/test_convert_equivalence.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: explore-workflow/inn-hyphen-data-rows
  evidence_ref: tests/test_audit_fidelity.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: explore-workflow/delimiter-position-and-loss
  evidence_ref: tests/test_audit_fidelity.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: explore-workflow/lair-source-identifier
  evidence_ref: tests/test_audit_fidelity.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: explore-workflow/new-spacing-anomaly
  evidence_ref: tests/test_audit_fidelity.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: explore-workflow/source-note-and-independent-failure
  evidence_ref: tests/test_audit_fidelity.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: explore-workflow/paired-groups-retained
  evidence_ref: tests/test_heading_normalization.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: explore-workflow/bold-is-not-heading
  evidence_ref: tests/test_heading_normalization.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: explore-workflow/full-collection-context
  evidence_ref: tests/test_batch_audit.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: explore-workflow/reproducible-embedded-batch
  evidence_ref: tests/test_batch_audit.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: explore-workflow/missing-source-or-page-mapping
  evidence_ref: tests/test_batch_audit.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: strategy-schema/valid-dd2-pair-rule
  evidence_ref: tests/test_heading_normalization.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: strategy-schema/absent-and-invalid-rules
  evidence_ref: tests/test_heading_normalization.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: strategy-schema/configuration-through-all-entry-points
  evidence_ref: tests/test_heading_normalization.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: strategy-schema/sample-update-with-evidence
  evidence_ref: outputs/debug-dd2-followup/sample-review/report.json
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
- scenario_key: strategy-schema/explicitly-aliased-label
  evidence_ref: tests/test_heading_normalization.py
  external_ref: 4c781e309571d8510bf575794a95d577830b9faa + working tree
  verification_result: pass
