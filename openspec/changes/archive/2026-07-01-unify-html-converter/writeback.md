# Writeback

## 回写摘要

- change：`unify-html-converter`
- 回写结论：实现完成，三份 HTML→Markdown 实现归一为 `converter.py` 共享内核；绝大多数回写目标在 Stage 2 已预先同步，本次仅需 1 处文档行回写
- 关键结果：
  - 删除死代码 `fandom_html_to_markdown.py` 与 regex 实现 `html_to_markdown.py`
  - CDP 路径 + test_runner 切换到共享内核（`wiki_domain=""` generic 模式）
  - converter kernel 支持 `wiki_domain=""`（generic HTML），`None` 仍 `TypeError`
  - mirror equivalence golden snapshot 证明 B 轴两入口 byte-identical
  - 全量测试绿（80 unit + 13 site-samples + 1 golden snapshot）

## Capability / Spec 增量摘要

| Capability | 变更类型 | 对应 spec 文件 | 增量摘要 |
| --- | --- | --- | --- |
| `pipeline-converters` | Modified | `openspec/specs/pipeline-converters/spec.md`（frozen，本次无 SHALL 改动） | REMOVED `fandom-html-to-markdown-module`（死代码）；ADDED `strategy-variant-config-driven`（变体走配置非独立文件） |
| `pipeline-convert-phase` | Modified | `openspec/specs/pipeline-convert-phase/spec.md`（frozen，本次无 SHALL 改动） | ADDED `cdp-path-uses-shared-kernel`（CDP 走 `convert_html_to_markdown(wiki_domain="")`）；ADDED `mirror-equivalence-golden-snapshot` |

> frozen spec 文件本身无需回写：REMOVED `fandom-html-to-markdown-module` 在原 frozen spec 中**无对应 SHALL 条款**（fandom 从未被 spec 化为 requirement，仅作为实现死代码存在）；新增 requirement 待本 change archive 时由 openspec 工具合并 delta。

## 验证结论与证据入口

| 验证维度 | 结论 | 证据入口 |
| --- | --- | --- |
| Spec-to-Implementation | 全部 requirement 覆盖 | `verification.md` § Spec-to-Implementation Coverage |
| Task-to-Evidence | 33/33 task 通过 | `verification.md` § Task-to-Evidence Coverage |
| 测试 | 80 unit + 13 site-samples + 1 golden 全绿 | `python3 scripts/test_runner.py all`；`tests.test_golden_convert` |
| Adjacent fix | `test_assertions.py` escaped-pipe bug 修复+测试 | `tests/lib/test_md_table_assertions.py` |

## 回写目标与字段映射

| 目标页 | 同步字段/区块 | 回写内容 |
| --- | --- | --- |
| `AGENTS.md` §2 | Convert 能力行 | 无需改动——已声明 `converter.py` 为内核 + 三路径薄壳 + 可选 wiki_domain（Stage 2 完成） |
| `docs/architecture/01-overview.md` | 模块清单 | 无需改动——已无 `html_to_markdown.py` / `fandom_html_to_markdown.py` 引用（Stage 2 完成） |
| `docs/architecture/05-converter-architecture.md` §2.2 | Pipeline Converters 模块表 | **删除** `fandom_html_to_markdown.py` 死代码行（文件已删，"待 Stage 3 删除" 状态过期） |
| `openspec/specs/pipeline-converters/spec.md` | SHALL 条款 | 无需改动——原 frozen spec 无 fandom 对应条款 |

## 回写执行结果

| 目标页 | 执行结果 | 执行时间 | 执行人 | 结果说明/链接 |
| --- | --- | --- | --- | --- |
| `AGENTS.md` §2 | 跳过（已同步） | 2026-07-01 | opsx-apply | grep 确认无 stale 引用；Convert 行已反映统一内核 |
| `docs/architecture/01-overview.md` | 跳过（已同步） | 2026-07-01 | opsx-apply | grep 确认无 stale 引用 |
| `docs/architecture/05-converter-architecture.md` | 成功 | 2026-07-01 | opsx-apply | 删除 §2.2 表中 `fandom_html_to_markdown.py` 行；§2.3 已正确描述 converter.py 为唯一内核 + wiki_domain 可选 |
| `openspec/specs/pipeline-converters/spec.md` | 跳过（无对应条款） | 2026-07-01 | opsx-apply | frozen spec 无 fandom SHALL 条款，delta 待 archive 合并 |

## 回写前置条件

- [x] 已读取 `spec_standard_ref`（`openspec/specs/pipeline-converters/spec.md` + `pipeline-convert-phase/spec.md`）
- [x] `verification.md` 已生成且无阻塞项
- [x] 回写目标页已确认存在且可编辑
- [x] capability/spec 增量摘要已核对 proposal 与 specs 一致

## 不回写的内容

- 不复制完整 `proposal.md`、`design.md`、`specs/*/spec.md`、`tasks.md` 正文
- 不写与本次 change 无关的历史信息
- 不在 frozen spec 中手动合并 delta（由 openspec archive 流程处理）
