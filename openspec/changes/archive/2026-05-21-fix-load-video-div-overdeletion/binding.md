# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: 无既有 spec 涉及此行为（converter clean_html 为内部实现细节）
- `project_page_ref`: `docs/architecture/05-converter-architecture.md`（转换器架构文档）
- `additional_context_refs`: `scripts/lib/extraction/converter.py` L260-275（clean_html 中的 Load video 清理循环）

## Source of Truth

- 行为规范真源：本 change 的 design.md 即为真源（无既有 spec）
- 项目页面角色：上下文输入
- 非真源说明：本 change 仅修复 converter 内部 bug，不涉及外部能力规范变更

## 回写目标

- `writeback_targets`: 无需回写（内部 bug fix）
- `writeback_owner`: N/A
- `writeback_timing`: N/A

## 同步约束

- 本 change 为纯代码修复，无 spec 需同步
- 修复后应更新 `tests/fixtures/boi-crawl-100-validation-baseline.json` 以反映改善后的指标

## 待确认项

- [x] 已确认标准页引用（无既有 spec）
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限（无需回写）
- [x] 已确认异常处理与冲突策略（N/A）
