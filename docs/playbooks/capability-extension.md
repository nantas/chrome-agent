# Capability Extension Playbook

> 当 explore 工作流发现新能力需求时的操作手册。
> 适用于：开发者在 `scripts/explore/freeze.py` 被 capability gate 阻断后。

## 决策树

```
freeze.py exit 5 → capability-gap.yaml 已生成
│
├─ gap type: new_cleanup_op → 方案 A（新增 cleanup op）
├─ gap type: new_infobox_handler → 方案 B（新增 infobox handler）
└─ 不确定 → 方案 C（走 openspec change）
```

## Gap Report 格式

`capability-gap.yaml` 输出格式：

```yaml
- capability: convert
  issue: new_cleanup_op
  detail: "Unknown cleanup op: custom_format_parser"
- capability: extract
  issue: new_infobox_handler
  detail: "Unknown handler: custom_field_renderer"
```

## 方案 A：新增 cleanup op

1. **实现清理逻辑**：在 `scripts/lib/extraction/preprocessor.py` 的 `_apply_cleanup_ops()` 中添加处理逻辑
2. **注册到 registry**：在 `configs/capability-registry.yaml` 的 `convert.cleanup_ops` 中添加 entry
3. **运行 doctor**：`chrome-agent doctor --check capabilities` 确认一致
4. **重新 freeze**：重新运行 `python3 -m scripts.explore.freeze <repo_root> <scaffold_path>`，此时应通过

## 方案 B：新增 infobox handler

1. **实现 handler**：在 `scripts/lib/extraction/infobox.py` 的 `_apply_bs4_handler()` 中添加 handler 分支
2. **注册到 registry**：在 `configs/capability-registry.yaml` 的 `extract.infobox_handlers` 中添加 entry
3. **运行 doctor**：`chrome-agent doctor --check capabilities` 确认一致
4. **重新 freeze**：重新运行 freeze，此时应通过

## 方案 C：走 openspec change

1. **检查现有能力**：`chrome-agent doctor --check capabilities` 确认当前 registry 覆盖范围
2. **创建 change**：`openspec new <change-name>` 描述新增能力
3. **在 change 中实现**：按 openspec 流程完成 spec、design、tasks、implementation
4. **归档前验证**：`doctor --check capabilities` 通过后方可归档
5. **回写文档**：确保 `AGENTS.md` §2、`GOVERNANCE.md` §7、架构文档同步更新

## 工作流示意

```
explore → scaffold → freeze
                        │
                        ├─ gate pass → strategy.md 写入 ✓
                        │
                        └─ gate block → capability-gap.yaml
                                          │
                                          ├─ 小改动（1-2 个新 capability）→ 方案 A/B
                                          └─ 大改动（新能力类型）→ openspec change
```

## 相关文档

- `AGENTS.md` §0.5 C11 — 能力注册同步约束
- `docs/GOVERNANCE.md` §7 — 派生文档同步原则
- `configs/capability-registry.yaml` — 能力注册 SSOT
- `scripts/explore/capability_gate.py` — gate 实现
