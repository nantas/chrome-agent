# Design

## Context

`fix-pipeline-quality-gaps` change 暴露了多文件间职责重叠的系统性结构问题。源码审计确认了以下重复模式：

- **YAML frontmatter 解析**：6 处独立实现，`parse_strategy()`（`---` split）和 `regex` 两类
- **速率限制配置**：`orchestrate.py` 和 `rate_limit.py` 完全重复的 `RateLimitConfig`/`resolve_rate_limit_config()`/`_load_anti_crawl_strategy()`
- **排除分类解析**：`_resolve_exclude_categories()` 内联在 `orchestrate.py` 中

本项目结构重构规划（`docs/plans/2026-05-19-structure-refactor-and-docs.md`）将 Change 1 定义为："提取共享库 `lib/`"，作为后续 Change 2（统一转换器）和 Change 3（orchestrator 拆分）的基础。

用户已通过 ask_user 确认以下决策：
1. 速率配置移至 `lib/config_resolver.py`
2. YAML 解析仅提取 `parse_strategy()`（非全覆盖）
3. `_resolve_exclude_categories` 直接移动（保持签名）

## Goals / Non-Goals

**Goals:**
- 新建 `scripts/lib/` Python 包，作为跨模块共享代码的存放位置
- 提取 `parse_strategy()` 到 `lib/strategy_loader.py`
- 合并 `RateLimitConfig`/`resolve_rate_limit_config()`/`load_anti_crawl_strategy()`/`resolve_exclude_categories()` 到 `lib/config_resolver.py`
- 清理 `orchestrate.py` 中的重复函数定义，改为从 `lib/` 导入
- 删除 `rate_limit.py`（内容已迁移）
- 更新 `__init__.py` 和 `pipeline.py` 的导出路径
- 建立 Python 3.9 兼容的 `lib/` 包（`from __future__ import annotations` 或 `Optional[X]` 语法）
- 所有现有测试通过，行为完全不变

**Non-Goals:**
- 不统一其他 5 处 YAML frontmatter 解析实现
- 不改动 `architecture_gate.py`
- 不改动 Node.js 侧的 `chrome-agent-cli.mjs`
- 不涉及转换器合并（Change 2）
- 不涉及包重命名（Change 3）
- 不涉及测试新增

## Decisions

### D1: 包名与导入路径

`scripts/lib/` 使用顶级包名 `lib`，通过相对导入被 `/scripts/mediawiki-api-extract/` 子包引用。

```
scripts/
├── lib/
│   ├── __init__.py          # 空包声明
│   ├── strategy_loader.py   # parse_strategy() + parse_frontmatter_from_content()
│   └── config_resolver.py   # RateLimitConfig + resolve_rate_limit_config() + ...
├── mediawiki-api-extract/
│   ├── __init__.py
│   ├── pipeline/
│   │   ├── orchestrate.py   # 改为 from ...lib.strategy_loader import parse_strategy
│   │   ├── __init__.py      # 改为从 lib/ 导出
│   │   └── rate_limit.py    # 删除
│   └── ...
└── explore/
    └── ...
```

导入路径示例（从 `orchestrate.py` 发起）：
```python
from ...lib.strategy_loader import parse_strategy
from ...lib.config_resolver import resolve_rate_limit_config, resolve_exclude_categories, RateLimitConfig
```

在 `python3 -m scripts.mediawiki-api-extract` 调用方式下，`scripts` 在 Python 模块搜索路径中，因此 `...lib` 可以正确解析。

### D2: rate_limit.py 迁移策略（两阶段）

`rate_limit.py` 已有 `RateLimitConfig` + `resolve_rate_limit_config()` + `_load_anti_crawl_strategy()` 的 canonical 版本。但 `orchestrate.py` 另有重复版本。

**执行顺序：**
1. **先建 lib/，再改 orchestrate.py**：新建 `lib/config_resolver.py`，将 `rate_limit.py` 的代码移入（作为 canonical），然后修改 `orchestrate.py` 删除重复代码并改为从 `lib/config_resolver.py` 导入
2. **更新 __init__.py**：`__init__.py` 的 `RateLimitConfig` 导出从 `rate_limit.py` 改为 `lib/config_resolver`
3. **删除 rate_limit.py**：确认无残留引用后删除

这种顺序确保任何时刻代码都是可运行的（不会出现同时缺失两个来源的情况）。

### D3: Python 3.9 兼容性

`AGENTS.md` 要求新建模块兼容 Python 3.9。策略：

- `lib/strategy_loader.py` 和 `lib/config_resolver.py` 在文件顶部加 `from __future__ import annotations`（与 `html_to_markdown.py` 当前做法一致），允许 `Optional[X]` 风格
- 所有类型注解使用 `Optional[X]` 而非 `X | None`
- `from typing import Optional`

### D4: `_resolve_exclude_categories` 重命名为 `resolve_exclude_categories`

保持函数体不变，但去掉 `_` 前缀变为公开函数。这已在 spec 中记录为 RENAMED requirement。

### D5: `load_anti_crawl_strategy` 增加 `repo_root` 参数

原 `_load_anti_crawl_strategy()` 通过 `os.path.dirname(__file__)` 计算相对路径。移动到 `lib/` 后，路径需要调整为使用 `repo_root` 参数（默认空值时回退到相对于 `lib/config_resolver.py` 的路径）。

因为在 `lib/config_resolver.py` 内部，`..` 的层级与原来不同（需要从 `scripts/lib/` 到 `sites/anti-crawl/`）。具体路径计算：

```python
# In rate_limit.py (old): os.path.join(os.path.dirname(__file__), "..", "..", "sites", "anti-crawl")
# In lib/config_resolver.py: os.path.join(os.path.dirname(__file__), "..", "..", "sites", "anti-crawl")
```

相同路径（`scripts/lib/` → `../../sites/anti-crawl/` = `sites/anti-crawl/`）正确。

## Risks / Migration

| 风险 | 可能性 | 影响 | 缓解 |
|------|--------|------|------|
| 相对导入路径解析失败 | 低 | 高 | 先在会话中用 `python3 -c "from scripts.lib.strategy_loader import parse_strategy; print('ok')"` 验证；再用 `python3 -m scripts.mediawiki-api-extract --help` 端到端验证 |
| `rate_limit.py` 删除后有残留导入引用 | 低 | 中 | 删除前执行 `grep -r "rate_limit" scripts/` 确认零引用 |
| `__init__.py` 导出符号丢失 | 低 | 中 | 显示验证 `__all__` 保持完整；`__init__.py` 当前导入 `RateLimitConfig` 覆盖自 `rate_limit.py`，需同步更新 |
| `pipeline.py` backcompat shim 未同步 | 低 | 中 | `pipeline.py` 从 `pipeline/` 包 re-export 符号，其路径不直接引用 `rate_limit.py`，只需确认 `__init__.py` 的导出正确即可 |
