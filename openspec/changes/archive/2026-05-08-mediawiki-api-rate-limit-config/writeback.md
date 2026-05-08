# Writeback

## 回写摘要

- change：`mediawiki-api-rate-limit-config`
- 回写结论：所有回写目标均已在实现阶段直接更新到仓库文件中，无需额外同步步骤
- 关键结果：MediaWiki API pipeline 的 rate limit 控制从硬编码改为四层策略驱动（CLI → Site Strategy → Anti-Crawl tier → 代码默认值）

## Capability / Spec 增量摘要

| Capability | 变更类型 | 对应 spec 文件 | 增量摘要 |
| --- | --- | --- | --- |
| `anti-crawl-schema` | Modified | `openspec/specs/anti-crawl-schema/spec.md` | 新增可选 `rate_limit_tiers` 字段，支持按保护机制定义分级化的请求频率模板 |
| `site-strategy-schema` | Modified | `openspec/specs/site-strategy-schema/spec.md` | 在 `api` 块下新增 `rate_limit` 字段，支持引用 anti-crawl tier 并提供本地数值覆盖；定义四层覆盖优先级 |
| `mediawiki-api-extraction` | Modified | `openspec/specs/mediawiki-api-extraction/spec.md` | 新增 Rate Limit 配置解析 requirement；更新 Phase B 并发/延迟/429 退避章节为策略驱动描述；新增独立 Concurrency and rate limiting requirement |

## 验证结论与证据入口

| 验证维度 | 结论 | 证据入口 |
| --- | --- | --- |
| Spec-to-Implementation | 8 个 spec requirement 全部有对应实现，无缺口 | `verification.md` Spec-to-Implementation Coverage 表格 |
| Task-to-Evidence | 14/14 任务完成，均有可验证证据 | `verification.md` Task-to-Evidence Coverage 表格 |
| 代码语法 | 所有修改的 `.py` 文件通过 `py_compile` | 各文件 `py_compile` 输出 |
| YAML/JSON 格式 | 所有策略文件通过解析校验 | `yaml.safe_load` / `json.load` 输出 |

## 回写目标与字段映射

| 目标文件 | 同步字段/区块 | 回写内容 |
| --- | --- | --- |
| `sites/anti-crawl/rate-limit-api.md` | frontmatter: `rate_limit_tiers`, `detection.http.status_codes`, `failure_signals.http.status_codes`, `sites`; body: MediaWiki API 429 章节 | 新增 default/strict/very-strict 三级 tier 模板；扩展 HTTP 429 检测；添加 slaythespire.wiki.gg 到 sites |
| `sites/anti-crawl/registry.json` | `rate-limit-api` 条目 | 更新 detection_summary 和 sites |
| `sites/strategies/slaythespire.wiki.gg/strategy.md` | frontmatter: `anti_crawl_refs`, `api.rate_limit` | 追加 `rate-limit-api` 引用；新增 `api.rate_limit`（tier: strict，本地覆盖 batch_delay_ms=800, retry.max_retries=5, retry.backoff_multiplier=2.5） |
| `sites/strategies/registry.json` | `slaythespire.wiki.gg` 条目 | 同步 `anti_crawl_refs` |
| `docs/decisions/2026-05-08-rate-limit-config-architecture.md` | 完整文件（新建） | ADR：Context / Decision / Consequences |

## 回写执行结果

| 目标文件 | 执行结果 | 执行时间 | 执行人 | 结果说明 |
| --- | --- | --- | --- | --- |
| `sites/anti-crawl/rate-limit-api.md` | 成功 | 2026-05-08 | Pi agent | 直接编辑仓库文件 |
| `sites/anti-crawl/registry.json` | 成功 | 2026-05-08 | Pi agent | 直接编辑仓库文件 |
| `sites/strategies/slaythespire.wiki.gg/strategy.md` | 成功 | 2026-05-08 | Pi agent | 直接编辑仓库文件 |
| `sites/strategies/registry.json` | 成功 | 2026-05-08 | Pi agent | 直接编辑仓库文件 |
| `docs/decisions/2026-05-08-rate-limit-config-architecture.md` | 成功 | 2026-05-08 | Pi agent | 新建文件 |

## 回写前置条件

- [x] 已读取 `spec_standard_ref`
- [x] `verification.md` 已生成且无阻塞项
- [x] 回写目标页已确认存在且可编辑
- [x] capability/spec 增量摘要已核对 proposal 与 specs 一致

## 不回写的内容

- 不复制完整 `proposal.md`、`design.md`、`specs/*/spec.md`、`tasks.md` 正文
- 不写与本次 change 无关的历史信息
- 不回写到外部 wiki 或项目页面（本次回写目标均为仓库内文件）
