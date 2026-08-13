# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `docs/architecture/00-target-architecture.md` §3.1（CV3/CV4 镜像声明 + 不变量 I2「mirror 不包含转换逻辑，只做编排」）、§4.3（mirror 等价证明）、`docs/architecture/05-converter-architecture.md`（两阶段转换 + 共享提取引擎）、`openspec/specs/convert/spec.md` `convert-kernel-three-layer-interface` requirement（三层接口：class / convert_html_to_markdown / convert_page_full）
- `project_page_ref`: 架构再审查报告 New #1（CV3 post-ops 分歧）来源 `/var/folders/.../architecture-review-20260813-154550.html`；`scripts/explore/sample_converter.py:140-205`（CV3 未声明的 post-op markdown 层）；`scripts/pipeline/pipeline/phases/convert.py:163-184`（CV4 跳过该层 + line 165 虚假的 proxy 声称）；`tests/test_convert_equivalence.py`（证明 fixture 省略所有分歧 key）
- `additional_context_refs`: `scripts/lib/extraction/converter.py:984-1021`（`convert_page_full` 内核，post-op 的目标归宿）；`openspec/specs/explore/explore-scaffold.md::apply-extraction-uses-shared-lib`（声明 _apply_extraction 为 4 步管线，post-op 当前是未声明的第 5 步）；`configs/capability-registry.yaml`（3 个 cleanup_ops 错误指向 sample_converter.py）；4 站策略实际使用分歧 key（cleanup ops（strip_empty_parens/fix_separators/normalize_internal）×4 + url_conversion/youtube_cleanup ×1（bindingofisaacrebirth））

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`: `openspec/specs/convert/spec.md`（MODIFIED `convert-kernel-three-layer-interface`：声明第 4 个公开入口 `apply_post_conversion_ops` + post-op 步骤；归档时 spec delta 提升为 frozen）；`openspec/specs/explore/explore-scaffold.md::apply-extraction-uses-shared-lib`（REMOVED/精简：post-op 不再在 _apply_extraction，由 kernel 承接）；`configs/capability-registry.yaml`（3 个 cleanup_ops 的 `implemented_in` 从 `sample_converter.py` 改指 `converter.py`）；`docs/architecture/00-target-architecture.md` §3.1（CV3 mirror 行：post-op 归属订正）
- `writeback_owner`: 实施 agent
- `writeback_timing`: 验证通过后、归档前
- C10 全局同步：**不触发**。本 change 仅修改 `scripts/lib/extraction/converter.py` + `scripts/explore/sample_converter.py` + `scripts/pipeline/pipeline/phases/convert.py` + `tests/`，不触碰 C10 tracked files（runtime.mjs / cli.mjs / SKILL.md）。

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- **行为变更披露（重要）**：本 change 不是纯重构。CV4（pipeline 生产路径）修复后将开始应用此前跳过的 post-ops——对配置了 `text_normalization`/`url_conversion`/`youtube_cleanup`/`cleanup` ops 的策略（4 站），pipeline 产出 Markdown 会变化。这是预期质量修复（让 pipeline 与 explore 一致），但 SHALL 经 `site-samples` 回归确认无破坏性回归
- 预存结构缺陷（归档时顺带修）：`openspec/specs/convert/spec.md` 与 fetch spec 一样用了 change-only 的 `## ADDED Requirements` 头且缺 `## Purpose`，归档 `openspec archive` 会拒绝。需在同次归档前改为 `## Requirements` + 补 Purpose（与 fix-crawl-scrapling-bare-call-bug 归档时对 fetch spec 做的修复同模式）

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限（C10 不触发；convert spec 结构缺陷归档时顺带修）
- [x] 已确认异常处理与冲突策略（行为变更经 site-samples 回归把关）
