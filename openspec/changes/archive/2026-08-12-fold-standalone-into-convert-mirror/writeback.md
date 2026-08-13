# Writeback

## 回写目标

| 目标 | 字段映射 | 前置条件 | 状态 |
|------|----------|----------|------|
| `docs/architecture/00-target-architecture.md` §3.1 | 目标模块表新增 CV4-standalone 变体行；表后新增「内核三层接口」表+说明 | verification 通过 | ✅ 已执行（task 2.6/2.7） |
| `CONTEXT.md` | 评估是否需补 standalone / 三层接口术语 | — | 无需补（standalone 是 CV4 薄壳变体，已在 §3.1 声明；三层接口是实现细节，不需进领域词汇表） |

## 不需回写的确认

- **`scripts/pipeline/cli.py`**：子命令签名/参数/退出码未变，无需回写
- **能力注册表 `configs/capability-registry.yaml`**：无新增能力（convert 为 Modified）
- **`openspec/specs/convert/spec.md`**：归档时由 delta 回填（task 4.3）

## 回写执行证据

| 回写 | 执行时间 | 结果 |
|------|----------|------|
| `00-target-architecture.md` §3.1 CV4-standalone 变体行 + 「内核三层接口」段落 | 2026-08-12 | ✅ task 2.6/2.7 完成 |
| CONTEXT.md 评估 | 2026-08-12 | ✅ 结论：无需补术语 |
| `doctor --check capabilities`（C11 归档前置） | 归档时执行 | — |
