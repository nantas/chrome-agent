# Verification

## 验证结论

KI Lifecycle 的行为规范和任务分解已完成。核心设计——分类（owner domain）、优先级（P0-P3）、状态机（5 状态）、顺序修复——均有对应 spec 和 tasks。本 session 的 6 个 KI 可作为完整的验证数据集。

## Spec-to-Implementation Coverage

| Requirement | Design 章节 | Tasks | 状态 |
|------------|------------|-------|------|
| ki-classification-by-owner | Design §3.1 | Tasks 2.1.1-2.1.5 | 设计完成 |
| ki-priority-assignment | Design §3.2 | Tasks 2.2.1-2.2.6 | 设计完成 |
| ki-fix-priority-order | Design §3.4 | Tasks 2.5.1-2.5.4 | 设计完成 |
| ki-status-tracking | Design §3.3 | Tasks 2.3.1-2.3.3 | 设计完成 |
| ki-table-in-strategy | Design §3.5 | Tasks 2.4.1-2.4.4 | 设计完成 |
| ki-separation-from-architecture-gate | Design §工作流位置 | Task 3.3 | 设计完成 |

## Task-to-Evidence Coverage

| Task | 验证方式 | 预期证据 |
|------|---------|---------|
| 2.1.1 `ki_lifecycle.py` 创建 | `python3 -c "import scripts.explore.ki_lifecycle"` | Import 成功 |
| 2.1.5 分类验证 | 对本 session 6 个 KI 运行 classify | 输出正确的 owner domain 映射 |
| 2.2.6 优先级验证 | 对 KI-1..KI-6 运行 assign_priority | KI-6=P0, KI-2/KI-5=P1, KI-1=P2, KI-3/KI-4=P3 |
| 2.4.4 KI 表更新 | 对 Isaac Wiki strategy.md 运行 update | KI 表含 7 列，无数据丢失 |
| 2.5.4 批次分组 | plan_fix_batches([KI-1..KI-6]) | 返回 3 个批次 |

## 关键证据入口

| 证据类型 | 证据路径/链接 | 对应 requirement/task |
| --- | --- | --- |
| 分类测试数据 | 本 session 6 个 KI (KI-1..KI-6) | ki-classification-by-owner |
| KI 表参考实现 | `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` (commit 08e3ea9) | ki-table-in-strategy |
| Spec 覆盖 | `specs/explore-ki-lifecycle/spec.md` | 全部 6 个 requirement |

## 缺口与阻塞项

- **阻塞**: 无 — design + specs + tasks 完整，等待实现
- **待实现**: `scripts/explore/ki_lifecycle.py` (新建文件)
- **待更新**: `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` KI 表 (已在 commit 08e3ea9 中部分更新为 7 列)
