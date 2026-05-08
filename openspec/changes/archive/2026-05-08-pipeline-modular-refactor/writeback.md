# Writeback

## 回写摘要

- change：`pipeline-modular-refactor` — 将 mediawiki-api-extract 管线拆分为 converters / strategies / pipeline 三层子包，新增独立操作入口和 CLI 子命令
- 回写结论：待实施（在 `/opsx-apply` 完成后更新）
- 关键结果：
  - 新增 3 个 capability：`standalone-extraction`、`incremental-reprocess`、`unified-link-fixer`
  - 修改 2 个 capability：`pipeline-converters`、`pipeline-cli-entry`
  - 修复 `__main__.py` 独立运行和 `chrome-agent-cli.mjs` 调用方式
  - 全量管线输出不变（smoke test 验证）

## Capability / Spec 增量摘要

| Capability | 变更类型 | 对应 spec 文件 | 增量摘要 |
| --- | --- | --- | --- |
| `standalone-extraction` | New | `specs/standalone-extraction/spec.md` | 独立单页面 fetch+convert，支持 HTML/wikitext 模式，提供 `fetch_and_convert` 和 `reconvert_file` 函数及 CLI `fetch` 子命令 |
| `incremental-reprocess` | New | `specs/incremental-reprocess/spec.md` | 增量补救指定页面，跳过 Phase A discovery，复用已有 manifest，提供 `reprocess_pages` 函数及 CLI `reprocess` 子命令 |
| `unified-link-fixer` | New | `specs/unified-link-fixer/spec.md` | 统一链接修复（/wiki/ → .md、双重后缀、fragment 保留、query 剥离），提供 `fix_links_in_dir` 函数及 CLI `fix-links` 子命令 |
| `pipeline-converters` | Modified | `specs/pipeline-converters/spec.md` | 转换器从 strategies.py 拆到 converters/ 子包；策略类按角色拆到 strategies/ 子包；管线编排拆到 pipeline/ 子包；保持向后兼容 re-export 和全量管线输出不变 |
| `pipeline-cli-entry` | Modified | `specs/pipeline-cli-entry/spec.md` | 修复 __main__.py sys.path 使目录脚本方式可用；新增 CLI 子命令路由（pipeline/fetch/reprocess/fix-links/reconvert）；修复 chrome-agent-cli.mjs 调用方式 |

## 验证结论与证据入口

| 验证维度 | 结论 | 证据入口 |
| --- | --- | --- |
| Spec-to-Implementation | 19 个 requirement 全部映射到 task，覆盖率 100% | `verification.md` Spec-to-Implementation Coverage 表 |
| Task-to-Evidence | 32 个 task 全部有预期证据和收集方式 | `verification.md` Task-to-Evidence Coverage 表 |
| 全量管线回归 | 待实施 — 使用 slaythespire.wiki.gg 5 个页面 smoke test | `/tmp/smoke-test/` 输出目录 |
| CLI 子命令端到端 | 待实施 — fetch/reprocess/fix-links 三个子命令 | bash 执行记录 |

## 回写目标与字段映射

| 目标页 | 同步字段/区块 | 回写内容 |
| --- | --- | --- |
| `AGENTS.md` Section 8 引擎概览表 | mediawiki-api-extract 引擎描述 | 更新说明：管线支持独立模块使用和 CLI 子命令 |
| `README.md` | 能力描述 | 新增：独立操作能力（单页面 fetch、增量 reprocess、链接修复） |
| `docs/playbooks/scrapling-fetchers.md` | fetcher 选型参考 | 新增 mediawiki-api-extract CLI 子命令用法参考（如适用） |

## 回写执行结果

| 目标页 | 执行结果 | 执行时间 | 执行人 | 结果说明 |
| --- | --- | --- | --- | --- |
| `AGENTS.md` | 待执行 | — | — | 实施完成后更新 |
| `README.md` | 待执行 | — | — | 实施完成后更新 |
| `docs/playbooks/scrapling-fetchers.md` | 待评估 | — | — | 仅当 fetcher 选型逻辑受影响时更新 |

## 回写前置条件

- [ ] 已读取 `spec_standard_ref`（`openspec/specs/agents-governance/spec.md`、`openspec/specs/capability-contracts/spec.md`、`openspec/specs/engine-registry/spec.md`）
- [ ] `verification.md` 已生成且无阻塞项
- [ ] 回写目标页已确认存在且可编辑
- [ ] capability/spec 增量摘要已核对 proposal 与 specs 一致

## 不回写的内容

- 不复制完整 `proposal.md`、`design.md`、`specs/*/spec.md`、`tasks.md` 正文
- 不写与本次 change 无关的历史信息
- 不更新 `configs/engine-registry.json`（引擎条目不变）
