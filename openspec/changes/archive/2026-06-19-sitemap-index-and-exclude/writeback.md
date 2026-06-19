# Writeback

## 回写摘要

- change：`sitemap-index-and-exclude`
- 回写结论：所有回写目标已执行完成（6/6）
- 关键结果：sitemap index 解析 + `discovery.exclude_patterns` 两项增量能力已落地到 4 个架构文档 + skill + 站点策略；PostHog 从"完全不可用"变为"discovery 可用"（14,576 → 1,725 页）

## Capability / Spec 增量摘要

| Capability | 变更类型 | 对应 spec 文件 | 增量摘要 |
| --- | --- | --- | --- |
| `sitemap-driven-crawl` | Modified | `openspec/changes/sitemap-index-and-exclude/specs/sitemap-driven-crawl/spec.md` | 3 ADDED requirements（sitemap-index-resolve-and-merge / sitemap-index-partial-failure-resilience / sitemap-exclude-patterns-filtering）+ 4 MODIFIED requirements（strategy-discovery-block-schema / sitemap-discovery-fetch-and-parse / sitemap-url-filtering-by-page-pattern / sitemap-index-handoff） |

## 验证结论与证据入口

| 验证维度 | 结论 | 证据入口 |
| --- | --- | --- |
| Spec-to-Implementation | ✅ 全覆盖（3 ADDED + 4 MODIFIED requirements 均有代码 + 测试 + Live 证据） | `verification.md` § Spec-to-Implementation Coverage |
| Task-to-Evidence | ✅ 16/16 tasks（T1-T11 全部完成，T6/T9 在 session 内验证为已完成） | `verification.md` § Task-to-Evidence Coverage |
| 单元测试 | ✅ 33/33（sitemap）+ 44/44（全量 `tests/*.test.mjs`） | `node --test tests/sitemap-driven-crawl.test.mjs` |
| Live E2E (T7) | ✅ discovery：1,725 页 / 0 references / success / failure_rate=0 | `outputs/20260618T133639-crawl-posthog-com-docs/page_manifest.json` |
| Live E2E (T8) | ✅ 5/5 converted / success（⚠️ 抽取质量 out-of-scope） | `outputs/20260618T133706-crawl-posthog-com-docs/` |

## 回写目标与字段映射

| 目标页 | 同步字段/区块 | 回写内容 |
| --- | --- | --- |
| `docs/architecture/03-strategy-schema.md` | `discovery` 字段表 + 示例 + 数据流摘要 | 新增 `exclude_patterns` 行；`sitemap_url` 行注明支持 index；YAML 示例加 `exclude_patterns`；新增"Sitemap index 解析"+"过滤执行顺序"两段；数据流摘要加 index 迭代 + include/exclude 两阶段 |
| `docs/architecture/02-pipeline-flow.md` | 概述段"Sitemap 发现路径" | 解析步骤扩展为"支持 `<sitemapindex>` 子 sitemap 迭代 + Set 去重 + 部分失败韧性"；URL 过滤拆分为 `page_pattern` include → `exclude_patterns` 排除 |
| `docs/architecture/06-engine-selection.md` | Selection Rules § 规则 2 | 补充 sitemap index 透明解析（不改变引擎选择）+ `exclude_patterns` 仅收窄 scope 不影响引擎选择 |
| `skills/chrome-agent/SKILL.md` | Stage 2 Presentation（discovery_method=sitemap 分支） | 移除"sitemap index is not yet supported"；改为"supported：子 sitemap fetch+merge+dedup，部分失败 non-blocking"；新增 `exclude_patterns` 字段说明 |
| `~/.agents/skills/chrome-agent/SKILL.md` | 全文同步 | 与 repo skill 完全一致（`cp` + `diff` 验证 IDENTICAL） |
| `sites/strategies/posthog.com/strategy.md` | 新建（change 产物） | frontmatter：`discovery.method: sitemap` + `sitemap_url`（index）+ `exclude_patterns: ["exact:/docs/references/**"]`；Gatsby 4.25.9 技术栈；discovery shape 表 |
| `sites/strategies/registry.json` | `entries[]` | 新增 `posthog.com` 条目（line 241） |

## 回写执行结果

| 目标页 | 执行结果 | 执行时间 | 执行人 | 结果说明/链接 |
| --- | --- | --- | --- | --- |
| `docs/architecture/03-strategy-schema.md` | ✅ 成功 | 2026-06-18 | chrome-agent maintainer | `discovery` 字段表 +2 行（exclude_patterns / sitemap_url 改写），+2 段说明，YAML 示例 +2 行，数据流摘要改写（line 259-280） |
| `docs/architecture/02-pipeline-flow.md` | ✅ 成功 | 2026-06-18 | chrome-agent maintainer | 概述段"Sitemap 发现路径"扩展（line 9） |
| `docs/architecture/06-engine-selection.md` | ✅ 成功 | 2026-06-18 | chrome-agent maintainer | Selection Rules 规则 2 补充 index 解析 + exclude_patterns 说明（line 90） |
| `skills/chrome-agent/SKILL.md` | ✅ 成功 | 2026-06-18 | chrome-agent maintainer | line 216-217：移除 "not yet supported"，改为 supported + exclude_patterns 说明 |
| `~/.agents/skills/chrome-agent/SKILL.md` | ✅ 成功（同步） | 2026-06-18 | chrome-agent maintainer | `cp` repo→global；`diff` 确认 IDENTICAL |
| `sites/strategies/posthog.com/strategy.md` | ✅ 成功（T6 产物） | 2026-06-18 | chrome-agent maintainer | change 内直接创建（非回写，是产物） |
| `sites/strategies/registry.json` | ✅ 成功（T6 产物） | 2026-06-18 | chrome-agent maintainer | line 241 新增 posthog.com 条目 |

## 回写前置条件

- [x] 已读取 `spec_standard_ref`（父 capability `sitemap-driven-crawl` spec + 本 change spec delta）
- [x] `verification.md` 已生成且无阻塞项（in-scope 全部 PASS；唯一缺口 out-of-scope 抽取质量，已转入 follow-up）
- [x] 回写目标页已确认存在且可编辑（3 架构文档 + skill 均存在；2 站点文件为 change 产物）
- [x] capability/spec 增量摘要已核对 proposal 与 specs 一致

## 不回写的内容

- 不复制完整 `proposal.md`、`design.md`、`specs/*/spec.md`、`tasks.md` 正文
- 不写与本次 change 无关的历史信息（如父 capability 的 GameAnalytics 细节）
- 不回写抽取引擎行为（out-of-scope，转 follow-up `posthog-extraction-quality`）
