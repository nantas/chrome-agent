# Writeback

## 回写摘要

- change：`fix-mediawiki-extraction-integrity`。
- 回写结论：本仓架构、CLI、领域上下文、恢复手册、ADR和八份主规范已同步；未修改外部页面、未归档。
- 关键结果：全页 infobox 编排、缓存身份/模式准入、转换指纹与失败传播、表格扫描、超时预算、freeze格式稳定性均实现。离线测试通过；Grow a Garden 旧golden差异仍单列，不声明全站恢复。

## Capability / Spec 增量摘要

| Capability | 变更类型 | 主 spec 文件 | 增量摘要 |
| --- | --- | --- | --- |
| convert | Modified | `openspec/specs/convert/spec.md` | 状态注入全页五步、独立字段canary与共享post-ops |
| extract-kernel | Modified | `openspec/specs/extract-kernel/spec.md` | 提取早于删除、启用/selector一致、URL/renderer上下文 |
| mediawiki-cache-integrity | New | `openspec/specs/mediawiki-cache-integrity/spec.md` | 精确title哈希存储、安全legacy读取、acquisition准入 |
| fetch-phase-cache-fastpath | Modified | `openspec/specs/fetch-phase-cache-fastpath/spec.md` | 兼容才跳过、新响应准入、失败重抓不能伪装cache命中 |
| pipeline-convert-phase | Modified | `openspec/specs/pipeline-convert-phase/spec.md` | 指纹resume、离线准入、失败结果隔离、自包含等价证明 |
| pipeline-converters | Modified | `openspec/specs/pipeline-converters/spec.md` | 表格cursor单调前进、两条infobox路径传source_dir |
| cli | Modified | `openspec/specs/cli/spec.md` | MediaWiki每子进程1–86400秒预算，默认600 |
| strategy | Modified | `openspec/specs/strategy/strategy-lifecycle.md` | 保留registry格式、顺序与rollback |

## 验证结论与证据入口

| 验证维度 | 结论 | 证据入口 |
| --- | --- | --- |
| Spec-to-Implementation | 八份spec均映射代码与测试；无新增无测试生产模块 | [verification.md](verification.md#spec-to-implementation-coverage) |
| Task-to-Evidence | 30项任务均有证据；站点基线问题单列 | [verification.md](verification.md#task-to-evidence-coverage) |
| 运行结果 | Python170、Node108、旧pipeline51通过；站点3通过1基线差异 | [verification.md](verification.md#站点样本) |
| 环境与治理 | C10副本/HEAD匹配、两项doctor成功、change严格校验通过 | verification.md 关键证据入口 |

## 回写目标与字段映射

| 目标页 | 同步区块 | 回写内容 |
| --- | --- | --- |
| `docs/architecture/00-target-architecture.md` | 共享入口表/镜像约束 | CV4注入状态后委托五步全页入口 |
| `docs/architecture/02-pipeline-flow.md` | Fetch、缓存机制 | v2身份、准入、指纹、失败title传播及恢复入口 |
| `docs/architecture/05-converter-architecture.md` | handler与全页编排 | BS4/source_dir、五步次序、post-ops一次 |
| `docs/architecture/04-cli-reference.md` | crawl参数表/预算说明 | timeout单位、范围、默认值、failure context |
| `CONTEXT.md` | 缓存与转换术语 | 缓存身份、准入、转换指纹、全页入口 |
| `CONTEXT-MAP.md` | 完整性边界 | acquisition→admission→resume→kernel→assembly |
| `docs/playbooks/mediawiki-extraction-recovery.md` | 新手册 | 新manifest审核、cache清点、重抓/离线分支、新目录、字段验收 |
| `docs/adr/0014-mediawiki-cache-identity.md` | 存储协议决策 | v2哈希/legacy权衡，与输出命名边界 |
| `openspec/specs/` 八份上述文件 | 行为主规范 | 按delta合并并纠正旧编排与外部fixture说明 |

## 回写执行结果

全部执行于 2026-09-11，由当前实施 agent 完成。

| 目标 | 执行结果 | 结果说明 |
| --- | --- | --- |
| 00-target-architecture | 成功 | 状态类入口与全页编排关系一致 |
| 02-pipeline-flow | 成功 | 移除只凭文件存在命中的旧描述 |
| 05-converter-architecture | 成功 | 移除四步和explore二次post-op过时描述 |
| 04-cli-reference | 成功 | crawl表及预算说明已写入 |
| CONTEXT / CONTEXT-MAP | 成功 | 新术语和依赖边界已写入 |
| recovery playbook | 成功 | 提供可审查操作路径；没有实际联网恢复 |
| ADR0014 | 成功 | 编号未占用；不接管obsidian-safe-filenames输出命名 |
| 八份主规范 | 成功 | 保留无关requirement；strategy使用已有生命周期文件，无第二真源 |
| 全局runtime/skill | 成功 | C10逐字匹配、installed-hash为d10858d完整HEAD；doctor成功 |
| 外部页面/其他仓库 | 跳过 | binding明确不在本change范围，无外部写入 |

## 回写前置条件

- [x] 已读取 `spec_standard_ref`（`docs/GOVERNANCE.md`）。
- [x] verification 已生成；无阻止本仓文档同步的缺口。站点golden差异阻止“全部站点通过”结论，已随验证状态如实回写。
- [x] 目标均在本仓存在且可编辑；新手册与ADR按binding创建。
- [x] capability/spec增量已核对，规范细化包含实现中发现的默认selector与失败重抓边界。

## 不回写的内容

不复制完整proposal/design/tasks到项目文档；不覆盖用户已有growagarden策略/registry、mobalytics或个人产品拆解。不执行全站重抓、my-wiki ingest、提交或归档。不将内部cache键迁移扩大成输出Markdown命名变更。

## 归档执行记录

2026-09-11，用户明确授权归档并提交。归档前发现主规范残留新旧同名 requirement，已按 delta 原位更新并去重；八份规范逐条比对一致，无重复。30/30 tasks 和全部 artifacts 完成，严格校验及 capability doctor 通过。保留 Grow a Garden 既有样本差异说明。本 change 归档至 `openspec/changes/archive/2026-09-11-fix-mediawiki-extraction-integrity/`。
