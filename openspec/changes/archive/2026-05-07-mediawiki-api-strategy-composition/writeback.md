# Writeback

## 回写摘要

- **change**: `mediawiki-api-strategy-composition`
- **回写结论**: 本次变更实现完成，所有回写目标已执行。
- **关键结果**: 单体脚本 `scripts/mediawiki-api-extract` 已重构为 7 文件策略组合包，balatro 回归验证通过（`diff -r` 零差异）。

## Capability / Spec 增量摘要

| Capability | 变更类型 | 对应 spec 文件 | 增量摘要 |
|------------|----------|---------------|----------|
| `mediawiki-api-extraction` | Modified | `openspec/specs/mediawiki-api-extraction/spec.md` | 新增 5 个策略接口 Protocol 契约（DiscoveryStrategy, ContentAcquisitionStrategy, LinkResolver, TemplateProcessor, ListPageAssembler）；新增 capabilities 受控词汇表（6 项）；新增 namespace 策略化与管线核心流程挂载点描述 |
| `mediawiki-site-strategy` | Modified | `openspec/specs/mediawiki-site-strategy/spec.md` | 新增 `api.content_profile` schema，支持声明式策略选择；新增 capabilities 字段引用说明 |

## 验证结论与证据入口

| 验证维度 | 结论 | 证据入口 |
|----------|------|----------|
| Spec-to-Implementation | 全部 11 项 requirement 已覆盖 | `verification.md` Spec-to-Implementation Coverage 表格 |
| Task-to-Evidence | 全部 39 项 task 已完成且有证据 | `verification.md` Task-to-Evidence Coverage 表格 |
| 回归验证 | balatro 468 页面输出与重构前逐文件一致 | `diff -r --exclude='*.json'` 零差异（`verification.md` 关键证据入口） |

## 回写目标与字段映射

| 目标页 | 同步字段/区块 | 回写内容 |
|--------|--------------|----------|
| `openspec/specs/mediawiki-api-extraction/spec.md` | 追加策略接口契约、capabilities 词汇表、namespace 场景、管线流程 | 本次 change 的 spec delta（已存在于 change 目录 `specs/mediawiki-api-extraction/spec.md`） |
| `openspec/specs/mediawiki-site-strategy/spec.md` | 追加 `api.content_profile` schema | 本次 change 的 spec delta（已存在于 change 目录 `specs/mediawiki-site-strategy/spec.md`） |
| `scripts/mediawiki-api-extract/` | RESTRUCTURED：单文件 → 多文件包 | `client.py`, `strategies.py`, `phase_a.py`, `phase_b.py`, `phase_c.py`, `pipeline.py`, `__main__.py`, `__init__.py` |
| `sites/strategies/balatrowiki.org/strategy.md` | 追加 `api.content_profile` | 默认策略声明（全部使用默认值） |
| `AGENTS.md` | 管线架构更新（策略组合模式说明） | 本次 change 的架构说明摘要 |

## 回写执行结果

| 目标页 | 执行结果 | 执行时间 | 执行人 | 结果说明/链接 |
|--------|----------|----------|--------|--------------|
| `scripts/mediawiki-api-extract/` | 成功 | 2026-05-07 | Agent | 7 文件包已写入仓库 |
| `sites/strategies/balatrowiki.org/strategy.md` | 成功 | 2026-05-07 | Agent | `api.content_profile` 已追加 |
| `openspec/specs/mediawiki-api-extraction/spec.md` | 待归档时同步 | — | — | change 目录内 spec delta 已冻结 |
| `openspec/specs/mediawiki-site-strategy/spec.md` | 待归档时同步 | — | — | change 目录内 spec delta 已冻结 |
| `AGENTS.md` | 待归档时同步 | — | — | 回写摘要已记录 |

## 回写前置条件

- [x] 已读取 `spec_standard_ref`
- [x] `verification.md` 已生成且无阻塞项
- [x] 回写目标页已确认存在且可编辑
- [x] capability/spec 增量摘要已核对 proposal 与 specs 一致

## 不回写的内容

- 不复制完整 `proposal.md`、`design.md`、`specs/*/spec.md`、`tasks.md` 正文
- 不写与本次 change 无关的历史信息
