# Proposal

## 问题定义

2026-08-12 架构审查（improve-codebase-architecture）产出 7 个候选。本 session 执行了其中两项，但以**直接 git 提交**绕过了 change 生命周期，缺少治理记录：

1. **候选 1 — convert 镜像等价证明**：`docs/architecture/00-target-architecture.md` §3.1 声明 `tests/test_convert_equivalence.py` 为 CV3/CV4/CV5 三镜像相对 CV1 内核的等价证明，但该文件不存在（ADR 0013 §4.3 的核心治理机制空转）。本 session 实现了它（commit `f03376d`、`ac08bba`），含覆盖 /wiki/ 链接、rowspan/colspan 表格、KI 字符（表格 `|`、字面 `*`、带括号/撇号页面标题、KI-5 图链连排、tooltip 对）的内嵌 fixture。
2. **候选 6 — fanbox helper 去重**：`fanbox-generate-nfo.mjs` 与 `-external.mjs`（共 ~630 行）复制了 ~10 个相同 helper。本 session 提取到 `scripts/lib/fanbox-shared.mjs`（commit `42e2dcc`），两脚本仅保留差异。

本 change **回溯性记录**上述已实现事项，固化治理轨迹并确认 spec 合规。实现不重做，只补记录。

同 session 的删除批（候选 2/3/7）已记录于 `openspec/changes/archive/2026-08-12-cleanup-post-4d-drift/`，不在本 change 范围。

## 范围边界

**范围内：**
- 候选 1：`tests/test_convert_equivalence.py`（3 用例：CV3≡kernel、CV4≡kernel、CV5≡kernel-generic），内嵌 fixture 不依赖 `.cache`、永不 skip
- 候选 6：`scripts/lib/fanbox-shared.mjs`（10 个无状态 helper）+ `tests/fanbox-shared.test.mjs`（node:test，6 用例）；两脚本改为 import 共享层
- spec delta：convert 能力（确认 `mirror-equivalence-golden-snapshot` requirement 现由 `test_convert_equivalence.py` 兑现——指针已由 cleanup-post-4d-drift 回填，本 change 不再改 spec 文本，仅做合规确认记录）

**范围外：**
- 候选 2/3/7（删除批）—— 见 `archive/2026-08-12-cleanup-post-4d-drift/`
- 候选 4（cli.mjs 提取）、候选 5（standalone.py 归属）—— 结构重构，暂停观察
- convert spec 文本变更 —— 指针回填已在删除批 change 完成
- fanbox 任何能力声明 —— 非能力工具脚本，无 spec

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `convert`: 确认 `mirror-equivalence-golden-snapshot` requirement 已被 `tests/test_convert_equivalence.py` 兑现（CV3/CV4/CV5 三镜像相对内核的字节级 golden snapshot），记录实现状态

## Capabilities 待确认项

- [x] 能力清单已确认（仅 convert 一个能力，fanbox 不归属任何能力）

## Impact

- **行为影响**：零。候选 1 为新增测试（不改运行时）；候选 6 为纯重构（两脚本外部行为不变，详见 design 中两处有意硬化）
- **spec 影响**：convert spec 文本无新增变更（指针回填在删除批完成），本 change 的 convert delta 为「实现兑现确认」性质的记录
- **测试影响**：净增测试（Python 3 用例 + Node 6 用例），全套绿
- **回溯性质**：实现先于 change，本 change 为补登记；verification 阶段复跑现有测试确认状态

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：ADR 0013、GOVERNANCE.md §3、00-target-architecture.md §4.3
  - 项目页：2026-08-12 架构审查报告（候选 1 + 候选 6 来源）
  - 回写目标：无新增（见 binding）
