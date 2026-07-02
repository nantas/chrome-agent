# Design

## Context

能力扩展工作流缺少可验证的 SSOT 和入口守卫。explore 流程发现新能力需求后，应产出 gap report 并触发 openspec change，而非直接写 strategy.md。详见 [proposal.md](./proposal.md)。

## Goals / Non-Goals

**Goals:**
- 创建 `capability-registry.yaml` 作为能力注册 SSOT
- 创建 `capability_gate.py` 检查探索需求是否可被已有能力覆盖
- `freeze.py` 集成 gap check 阻断
- `doctor --check capabilities` 交叉验证一致性
- 更新治理文档

**Non-Goals:**
- 不修改 openspec change 存档流程自动化
- 不添加 CI 集成
- 不修改 explore CLI 其他子命令

## Decisions

### D1: 注册表结构

```yaml
# configs/capability-registry.yaml
convert:
  cleanup_ops:
    - name: strip_fandom_infobox_tables
      implemented_in: scripts/lib/extraction/preprocessor.py
      strategy_field: extraction.cleanup
    - name: convert_ambox_to_text
      implemented_in: scripts/lib/extraction/preprocessor.py
      strategy_field: extraction.cleanup
    # ... all existing ops

extract:
  infobox_handlers:
    - name: text
      implemented_in: scripts/lib/extraction/infobox.py
      strategy_field: extraction.infobox_field_handlers
    - name: count_images
      implemented_in: scripts/lib/extraction/infobox.py
      strategy_field: extraction.infobox_field_handlers
    # ... all existing handlers

  special_capabilities:
    - name: card_stats
      implemented_in: scripts/pipeline/converters/card_stats.py
      strategy_field: capabilities
    - name: link_fixer
      implemented_in: scripts/pipeline/converters/link_fixer.py
      strategy_field: capabilities

fetch:
  engines:
    - name: scrapling-get
      implemented_in: scripts/explore/probe_chain.py
    - name: mediawiki-api
      implemented_in: scripts/pipeline/pipeline/phases/fetch.py
```

### D2: capability_gate.py 逻辑

```python
def check_requirements(scaffold: dict, registry: dict) -> list[dict]:
    gaps = []
    # Check cleanup ops
    known_ops = {op["name"] for op in registry.get("convert", {}).get("cleanup_ops", [])}
    for op in scaffold.get("extraction", {}).get("cleanup", []):
        if op not in known_ops:
            gaps.append({"capability": "convert", "issue": "new_cleanup_op", "detail": f"Unknown cleanup op: {op}"})
    # Check infobox handlers
    known_handlers = {h["name"] for h in registry.get("extract", {}).get("infobox_handlers", [])}
    for handler_name in scaffold.get("extraction", {}).get("infobox_field_handlers", {}).keys():
        if handler_name not in known_handlers:
            gaps.append({"capability": "extract", "issue": "new_infobox_handler", "detail": f"Unknown handler: {handler_name}"})
    return gaps
```

### D3: freeze.py 集成点

```python
# 在 freeze.py 中，strategy.md 写入前：
from scripts.explore.capability_gate import check_requirements
import yaml

registry_path = os.path.join(repo_root, "configs", "capability-registry.yaml")
with open(registry_path) as f:
    registry = yaml.safe_load(f)

gaps = check_requirements(scaffold, registry)
if gaps:
    gap_path = os.path.join(run_dir, "capability-gap.yaml")
    with open(gap_path, "w") as f:
        yaml.dump(gaps, f)
    print(f"❌ {len(gaps)} capability gap(s) found → {gap_path}")
    sys.exit(5)  # CAPABILITY_GAP_EXIT_CODE
```

### D4: doctor capabilities 检查

在 `chrome-agent-cli.mjs` 的 doctor 命令中新增 `capabilities` 子检查：
1. 读取 `capability-registry.yaml`
2. 验证每个 `implemented_in` 路径存在
3. 验证每个 capability 在 `openspec/specs/` 下有对应目录
4. 验证每个 capability 在 `AGENTS.md` §2 表中有对应行
5. 不一致输出 WARNING

## Risks / Migration

| 风险 | 缓解 |
|------|------|
| registry 初始填充可能遗漏已有 capability | 对照 `preprocessor.py`、`infobox.py`、`probe_chain.py` 手工审计 |
| freeze 阻断影响现有 explore 工作流 | 仅在新 capability gap 时阻断；已有策略不受影响 |
| doctor 检查新增 .mjs 复杂度 | 用简单的文件存在性检查 + grep，不引入新依赖 |
