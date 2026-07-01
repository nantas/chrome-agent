# Design

## Context

Discover 能力的全部 5 个实现模块从 pipeline 移到 explore。Pipeline 仅通过 `--from-manifest` 消费 explore 生成的 manifest。详见 [proposal.md](./proposal.md)。

## Goals / Non-Goals

**Goals:**
- 移动 5 个文件到 `scripts/explore/`
- 更新所有 import 路径
- 更新测试 import
- Orchestrator 移除 discover 阶段
- 全量回归通过

**Non-Goals:**
- 不修改 explore CLI 入口（`main.py`）
- 不修改 probe_chain
- 不修改 pipeline fetch/convert/assemble
- 不移 `discovery_summary.py`

## Decisions

### D1: 文件移动清单

| 原路径 | 新路径 |
|--------|--------|
| `scripts/pipeline/pipeline/phases/discovery_homepage.py` | `scripts/explore/discovery_homepage.py` |
| `scripts/pipeline/pipeline/phases/discovery_allpages.py` | `scripts/explore/discovery_allpages.py` |
| `scripts/pipeline/strategies/discovery.py` | `scripts/explore/discovery.py` |
| `scripts/pipeline/pipeline/homepage_parser.py` | `scripts/explore/homepage_parser.py` |
| `scripts/pipeline/pipeline/page_assigner.py` | `scripts/explore/page_assigner.py` |

### D2: Import 路径更新策略

移动后的文件从 `scripts/explore/` 位置执行，原 relative import（`from ..homepage_parser`）→ absolute import：

```python
# Before (discovery_homepage.py 在 pipeline/pipeline/phases/)
from ..homepage_parser import parse_homepage
from ..page_assigner import assign_pages

# After — 全部在 scripts/explore/ 下，同级用 relative import
from .homepage_parser import parse_homepage
from .page_assigner import assign_pages
from .discovery import AllPagesDiscoveryStrategy
from scripts.pipeline.client import ApiClient
from scripts.pipeline.pipeline import cache
```


### D3: Orchestrator 修改

删除约 140 行 discover 相关代码：
- 删除 `from .phases.discovery_*.py` import（行 19-21）
- 删除 discovery strategy resolution（行 128-160）
- 删除 discover 执行 block（行 177-209）
- 删除 discovery summary 生成（行 218-227）
- 删除 `--phase discover` 早期退出（行 258-266）
- `--from-manifest` 成为必须（或已有 manifest 文件）

### D4: 测试 import 更新

```python
# Before
from scripts.pipeline.pipeline.page_assigner import _apply_source_category_assignments
from scripts.pipeline.pipeline.phases.discovery_homepage import _build_homepage_manifest

# After
from scripts.explore.page_assigner import _apply_source_category_assignments
from scripts.explore.discovery_homepage import _build_homepage_manifest
```

## Risks / Migration

| 风险 | 缓解 |
|------|------|
| import 循环依赖 | explore 模块只导入 pipeline 的 client/cache（单向依赖，无循环风险） |
| `--from-manifest` 变得强制 | Pipeline CLI 已有此参数且有效；pipeline 用户需调整工作流 |
| 测试 import 路径未完全覆盖 | `grep -rn 'from.*pipeline.*discovery\|from.*homepage_parser\|from.*page_assigner' scripts/ tests/` 全面审计 |
