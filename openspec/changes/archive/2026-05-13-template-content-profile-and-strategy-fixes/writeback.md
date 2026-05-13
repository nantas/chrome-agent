# Writeback

## 回写摘要

- change: `template-content-profile-and-strategy-fixes`
- 回写结论: 待实施完成后执行
- 关键结果: 新增 capabilities 推导函数、模板补全 content_profile/rate_limit、scaffold 合并逻辑重构、4 个站点策略数据修复、2 个 registry 索引同步

## Capability / Spec 增量摘要

| Capability | 变更类型 | 对应 spec 文件 | 增量摘要 |
| --- | --- | --- | --- |
| `capabilities-derivation` | New | `specs/capabilities-derivation/spec.md` | 从 content_profile ID 动态推导 pipeline 所需 capabilities 的公共函数 |
| `site-strategy-template` | Modified | `specs/site-strategy-template/spec.md` | 模板新增 content_profile 推荐值、rate_limit.tier 默认值、移除静态 capabilities |
| `strategy-scaffold-generation` | Modified | `specs/strategy-scaffold-generation/spec.md` | API 合并从 or 覆盖改为三层合并（模板声明 + 探测事实 + 动态推导 capabilities） |
| `site-strategy` | Modified | `specs/site-strategy/spec.md` | 站点策略数据修复：neonabyss tier、BGG 引擎、slaythespire variant、registry 索引 |

## 验证结论与证据入口

| 验证维度 | 结论 | 证据入口 |
| --- | --- | --- |
| Spec-to-Implementation | 待实施验证 | `verification.md` 中预定义了 4 个 capability 共 12 个 requirement 的覆盖映射 |
| Task-to-Evidence | 待实施验证 | `verification.md` 中预定义了 14 个 task 的验证命令和预期结果 |

## 回写目标与字段映射

| 目标页 | 同步字段/区块 | 回写内容 |
| --- | --- | --- |
| `AGENTS.md` §Pipeline Strategy Schema 治理 | capabilities 推导说明 | 新增 `derive_capabilities()` 函数的引用说明，明确 capabilities 由 content_profile 动态推导而非手动维护 |
| `AGENTS.md` §引擎注册概览 | BGG 引擎引用 | boardgamegeek.com 的适用场景说明无变化，但引擎名从 superseded 改为 cloakbrowser-fetch 的上下文可更新 |
| `openspec/specs/agents-governance/spec.md` | 同步 AGENTS.md 治理约束 | 同步 capabilities 推导函数的治理约束 |
| `sites/anti-crawl/registry.json` | rate-limit-api.sites | 增加 "neonabyss.fandom.com" |
| `sites/strategies/registry.json` | 受影响策略条目 | 同步 neonabyss（anti_crawl_refs）、BGG（无 engine 字段需更新）、slaythespire（description 更新） |

## 回写执行结果

| 目标页 | 执行结果（成功/失败/跳过） | 执行时间 | 执行人 | 结果说明/链接 |
| --- | --- | --- | --- | --- |
| `AGENTS.md` | 待执行 | - | - | - |
| `openspec/specs/agents-governance/spec.md` | 待执行 | - | - | - |
| `sites/anti-crawl/registry.json` | 待执行 | - | - | - |
| `sites/strategies/registry.json` | 待执行 | - | - | - |

## 回写前置条件

- [ ] 已读取 `spec_standard_ref`（`openspec/specs/agents-governance/spec.md`）
- [ ] `verification.md` 已生成且无阻塞项
- [ ] 回写目标页已确认存在且可编辑
- [ ] capability/spec 增量摘要已核对 proposal 与 specs 一致

## 不回写的内容

- 不复制完整 `proposal.md`、`design.md`、`specs/*/spec.md`、`tasks.md` 正文
- 不写与本次 change 无关的历史信息
- 不在 AGENTS.md 中记录 BGG 引擎迁移的细节（引擎注册概览为汇总表，无站点级细节）
- 不在 rate-limit-api.md 中补充 Fandom 限速经验正文（范围外）
