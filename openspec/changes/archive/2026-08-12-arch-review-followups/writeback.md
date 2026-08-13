# Writeback

> 本 change 为回溯性记录。binding 已声明无新增回写目标——convert spec 永久文件指针已在 `archive/2026-08-12-cleanup-post-4d-drift/` 回填，fanbox 不归属任何能力。writeback 记录「确认无新增回写」+ 归档时对 convert 永久 spec 的 scenario 合并。

## 回写目标

| 目标 | 字段映射 | 前置条件 | 状态 |
|------|----------|----------|------|
| `openspec/specs/convert/spec.md` | 合并本 change delta 的 2 个新 scenario（fixture-discriminates-preprocessing、test-never-skips）入 `mirror-equivalence-golden-snapshot` requirement | verification 通过 | 归档时执行（task 4.3） |
| （无其他回写目标） | — | — | 见 binding 确认 |

## 不需回写的确认

- **`docs/architecture/00-target-architecture.md` §3.1**：已指向 `tests/test_convert_equivalence.py`（无需改）
- **`CONTEXT.md`**：html_to_markdown.py 过期从句已在删除批 change 修正（无需改）
- **能力注册表 `configs/capability-registry.yaml`**：本 change 无新增能力（convert 为 Modified，非新增）
- **fanbox 相关文档**：fanbox 无架构/spec/README 引用，无需回写

## 回写执行证据

（归档时由 task 4.3 填充：链接、时间、执行结果）

| 回写 | 执行时间 | 结果 |
|------|----------|------|
| `openspec/specs/convert/spec.md` 合并 2 个新 scenario 入 `mirror-equivalence-golden-snapshot` | 2026-08-12 | ✅ grep 确认 fixture-discriminates-preprocessing + test-never-skips 计数 2 |
| `node scripts/chrome-agent-cli.mjs doctor --check capabilities`（C11 归档前置） | 2026-08-12 | ✅ 全 `[durable] (checked)`，`next_action: none` |
| change 目录归档 `archive/2026-08-12-arch-review-followups/` | 2026-08-12 | ✅ 已移动，活跃 change 仅余 `obsidian-safe-filenames` |
