# Writeback

## 回写摘要

- change：`explore-strategy-pipeline-bridge`
- 回写结论：修复策略配置与管线执行之间的 3 层断层（引擎选择 / 转换器可发现性 / 工作流发现），确保 `api.platform` 配置被正确消费，`sample_converter.py` 可被 agent 发现和调用
- 关键结果：Isaac Wiki 的 explore/fetch 不再走 scrapling；agent 知道使用 `sample_converter.py` 而非裸 markdownify

## Capability / Spec 增量摘要

| Capability | 变更类型 | 对应 spec 文件 | 增量摘要 |
| --- | --- | --- | --- |
| `explore-strategy-pipeline-bridge` | New | `specs/explore-strategy-pipeline-bridge/spec.md` | 6 requirements: API 引擎选择、API handler、CLI 入口、main.py 引擎、SKILL 文档 |
| `engine-contracts` | Modified | `specs/engine-contracts/spec.md` | 4 requirements: registry 新类型、selectFetcher API 感知、runEngineFetch 分派、平台驱动非域名驱动 |
| `explore-workflow` | Modified | `specs/explore-workflow/spec.md` | 2 requirements: runExplore 返回转换引擎信息、main.py 引用 API 探测 |
| `site-strategy` | Modified | `specs/site-strategy/spec.md` | 2 requirements: api.platform 被引擎选择消费、rate-limit-api 推荐 API |

## 验证结论与证据入口

| 验证维度 | 结论 | 证据入口 |
| --- | --- | --- |
| Spec-to-Implementation | 14/14 requirements 有 tasks | `verification.md` §Spec-to-Implementation |
| Task-to-Evidence | 10/10 tasks 有验证方式 | `verification.md` §Task-to-Evidence |

## 回写目标与字段映射

| 目标页 | 同步字段/区块 | 回写内容 |
| --- | --- | --- |
| `scripts/chrome-agent-cli.mjs` | `selectFetcher()` + `runEngineFetch()` + `runExplore()` | API 平台检测、API handler、conversion_engine 字段 |
| `scripts/explore/sample_converter.py` | 文件末尾 | `main()` + argparse CLI |
| `scripts/explore/main.py` | line ~63 | engine 选择引用 api_config |
| `configs/engine-registry.json` | engines 数组 | `mediawiki-api` 条目 |
| `sites/anti-crawl/rate-limit-api.md` | engine_priority | `mediawiki-api` rank 0 |
| `~/.agents/skills/chrome-agent/SKILL.md` | Agent Gate 或新章节 | Route to sample conversion |

## 回写执行结果

| 目标页 | 执行结果 | 执行时间 | 执行人 | 结果说明/链接 |
| --- | --- | --- | --- | --- |
| 全部 | 跳过（等待实现） | — | — | 运行 `/opsx-apply` 后执行 |

## 回写前置条件

- [x] 已读取 `spec_standard_ref`
- [x] `verification.md` 已生成且无阻塞项
- [x] 回写目标页已确认存在且可编辑
- [x] capability/spec 增量摘要已核对 proposal 与 specs 一致

## 不回写的内容

- 不复制完整 `proposal.md`、`design.md`、`specs/*/spec.md`、`tasks.md` 正文
- 不修改 Isaac Wiki 策略的 `protection_level` 或 taxonomy
- 不修改 `phase_b.py`（重型管线，不在范围内）
