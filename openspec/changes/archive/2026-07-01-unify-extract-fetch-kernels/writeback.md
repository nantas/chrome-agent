# Writeback

## 回写摘要

- change：unify-extract-fetch-kernels — 统一 Extract 与 Fetch 能力的 B 轴漂移到共享内核
- 回写结论：✅ 所有 23 tasks 完成，80 tests 全绿，所有 spec requirements 满足
- 关键结果：
  1. 删除 `preprocessor.py` `context` 参数，统一为 always-full-cleanup
  2. 新增 `converter.py:convert_page_full()` 作为共享 4 步编排入口
  3. `.mjs` `runMediawikiApiFetch()` 改为 delegate 到 pipeline `ApiClient`

## Capability / Spec 增量摘要

| Capability | 变更类型 | 对应 spec 文件 | 增量摘要 |
| --- | --- | --- | --- |
| `extract-kernel` | Modified | `specs/extract-kernel/spec.md` | 删除 `context` 参数分支（REMOVED: context-parameter）；统一 preprocessor 为 always-full-cleanup（MODIFIED）；新增 `convert_page_full()` 共享编排入口（ADDED: convert-page-full, extract-infobox-via-kernel） |
| `fetch-kernel` | Modified | `specs/fetch-kernel/spec.md` | 删除 `.mjs` 自带的 curl-based MediaWiki API 客户端（REMOVED: mjs-mediawiki-api-fetch）；统一到 pipeline `ApiClient`（MODIFIED: fetch-via-pipeline-kernel） |

## 验证结论与证据入口

| 验证维度 | 结论 | 证据入口 |
| --- | --- | --- |
| Spec-to-Implementation | 6/6 requirements 实现，6/6 scenarios 通过 | [verification.md](./verification.md) §Spec-to-Implementation Coverage |
| Task-to-Evidence | 23/23 tasks 完成 | [verification.md](./verification.md) §Task-to-Evidence Coverage |
| 测试回归 | 80 tests pass (`.venv/bin/python -m unittest discover -s tests`) | [verification.md](./verification.md) §关键证据入口 |
| 输出等价 | `TestMirrorEquivalence` 通过 — explore 与 pipeline 路径输出一致 | [verification.md](./verification.md) §Scenario 验证 |

## 回写目标与字段映射

| 目标页 | 同步字段/区块 | 回写内容 |
| --- | --- | --- |
| `AGENTS.md` §2 Capability Framework | Extract 内核声明 | `preprocessor.py` 移除 `context` 参数；`converter.py` 新增 `convert_page_full()` 共享编排入口 |
| `AGENTS.md` §2 Capability Framework | Fetch 内核声明 | `.mjs` fetch 路径统一到 `scripts/pipeline/pipeline/phases/fetch.py`（`ApiClient`） |
| `docs/architecture/01-overview.md` | Fetch 路径描述 | 更新后端路由说明：`.mjs` 不再实现自有 MediaWiki API client，统一 routed through pipeline fetch |
| `docs/architecture/05-converter-architecture.md` | 编排入口说明 | 添加 `convert_page_full()` 作为 convert 能力的共享编排入口说明 |

## 回写执行结果

| 目标页 | 执行结果 | 执行时间 | 执行人 | 结果说明/链接 |
| --- | --- | --- | --- | --- |
| `AGENTS.md` §2 | ✅ 成功 | 2026-07-01 | — | Fetch: .mjs route → pipeline `ApiClient`; Convert: +`convert_page_full()`; Extract: always-full-cleanup |
| `docs/architecture/01-overview.md` | ✅ 成功 | 2026-07-01 | — | MediaWiki 路由描述更新：.mjs delegate 到 pipeline fetch 内核 |
| `docs/architecture/05-converter-architecture.md` | ✅ 成功 | 2026-07-01 | — | §5 重写为 Shared Orchestration Entry Point + Sample Converter Integration |

## 回写前置条件

- [x] 已读取 `spec_standard_ref`
- [x] `verification.md` 已生成且无阻塞项
- [x] 回写目标页已确认存在且可编辑
- [x] capability/spec 增量摘要已核对 proposal 与 specs 一致

## 不回写的内容

- 不复制完整 `proposal.md`、`design.md`、`specs/*/spec.md`、`tasks.md` 正文
- 不写与本次 change 无关的历史信息
