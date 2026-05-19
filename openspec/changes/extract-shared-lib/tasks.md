# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认三个 capability spec 的实现范围：`shared-strategy-loader`（`parse_strategy` + `parse_frontmatter_from_content` 占位）、`shared-config-resolver`（4 个函数/类）、`mediawiki-api-extraction-pipeline`（orchestrate.py 导入路径改建 + rate_limit.py 删除）
- [x] 1.2 确认无前置依赖：Change 1 无外部前置依赖；`fix-pipeline-quality-gaps` 的未完成任务（3.1, 3.2）是 Change 2 的前置，不影响本 change

## 2. 核心实现任务

### 2.1 新建 `scripts/lib/` 包

- [x] 2.1.1 创建 `scripts/lib/__init__.py` — 空文件（仅包声明）

### 2.2 创建 `lib/strategy_loader.py`

- [x] 2.2.1 从 `orchestrate.py:60-71` 复制 `parse_strategy()` 到 `lib/strategy_loader.py`，添加 `from __future__ import annotations` 和 `from typing import Optional`
  - **验证**: `python3 -c "from scripts.lib.strategy_loader import parse_strategy; print('ok')"` 输出 `ok`
  - **覆盖 spec**: `shared-strategy-loader:parse_strategy() 共享暴露` + `导入路径一致性`

- [x] 2.2.2 在 `lib/strategy_loader.py` 中添加 `parse_frontmatter_from_content(content: str) -> Optional[dict]` 预留函数
  - **验证**: `python3 -c "from scripts.lib.strategy_loader import parse_frontmatter_from_content; print(parse_frontmatter_from_content('---\na: 1\n---'))"` 输出 `{'a': 1}`
  - **覆盖 spec**: `shared-strategy-loader:parse_frontmatter_from_content() 预留占位`

### 2.3 创建 `lib/config_resolver.py`

- [x] 2.3.1 从 `rate_limit.py` 复制 `RateLimitConfig` dataclass、`_load_anti_crawl_strategy()`、`resolve_rate_limit_config()` 到 `lib/config_resolver.py`；将 `_load_anti_crawl_strategy` 重命名为 `load_anti_crawl_strategy`（公开函数），添加 `repo_root` 参数
  - **验证**: `python3 -c "from scripts.lib.config_resolver import RateLimitConfig, resolve_rate_limit_config; print('ok')"` 输出 `ok`
  - **覆盖 spec**: `shared-config-resolver:RateLimitConfig dataclass` + `resolve_rate_limit_config()` + `load_anti_crawl_strategy()`

- [x] 2.3.2 从 `orchestrate.py:257-273` 复制 `_resolve_exclude_categories()` 到 `lib/config_resolver.py`，重命名为 `resolve_exclude_categories(strategy, cli_excludes)`
  - **验证**: `python3 -c "from scripts.lib.config_resolver import resolve_exclude_categories; print('ok')"` 输出 `ok`
  - **覆盖 spec**: `shared-config-resolver:resolve_exclude_categories()`

### 2.4 修改 `orchestrate.py`

- [x] 2.4.1 删除 `parse_strategy()` 函数（原行 60-71），在文件顶部添加 `from ...lib.strategy_loader import parse_strategy`
  - **验证**: `run_pipeline()` 中 `parse_strategy(args.strategy)` 仍可正常工作

- [x] 2.4.2 删除 `RateLimitConfig` dataclass（原行 78-85），改为从 `lib/config_resolver` 导入
  - **验证**: `build_discovery_summary()` 和 `_estimate_time()` 中 `RateLimitConfig` 引用正常

- [x] 2.4.3 删除 `_load_anti_crawl_strategy()`（原行 238-250）和 `resolve_rate_limit_config()`（原行 276-353），添加 `from ...lib.config_resolver import resolve_rate_limit_config`
  - **验证**: `run_pipeline()` 中 `resolve_rate_limit_config(strategy, args)` 调用正常

- [x] 2.4.4 删除 `_resolve_exclude_categories()`（原行 257-273），添加 `from ...lib.config_resolver import resolve_exclude_categories`
  - **验证**: `run_pipeline()` 中调用从 `_resolve_exclude_categories(...)` 改为 `resolve_exclude_categories(...)` 正常工作
  - **覆盖 spec**: `mediawiki-api-extraction-pipeline:函数来源外部化`

### 2.5 更新 `__init__.py`

- [x] 2.5.1 修改 `scripts/mediawiki-api-extract/pipeline/__init__.py`：将 `from .rate_limit import RateLimitConfig as _RateLimitConfig, resolve_rate_limit_config` 改为从 `lib/config_resolver` 导入
  - **验证**: `__all__` 保持完整无缺失符号
  - **覆盖 spec**: `mediawiki-api-extraction-pipeline:rate_limit.py 删除`

### 2.6 更新 `pipeline.py` backcompat shim

- [x] 2.6.1 检查 `scripts/mediawiki-api-extract/pipeline.py` 是否需更新（当前从 `pipeline/` 子包 re-export，子包的 `__init__.py` 已修改则无需额外修改）
  - **验证**: `python3 -c "from scripts.mediawiki_api_extract.pipeline import parse_strategy, resolve_rate_limit_config, RateLimitConfig; print('ok')"` 输出 `ok`

### 2.7 删除 `rate_limit.py`

- [x] 2.7.1 执行 `grep -r "rate_limit" scripts/mediawiki-api-extract/` 确认无残留引用后，删除 `scripts/mediawiki-api-extract/pipeline/rate_limit.py`
  - **验证**: `grep -r "rate_limit" scripts/` 无 import 命中的残留（仅注释引用的 false alarm 可接受）

## 3. 收敛与验证准备

- [x] 3.1 整理 verification 检查点：包可导入性、CLI help、现有测试、端到端验证
- [x] 3.2 标记 writeback 信息：change 状态（done）、修改文件清单、无行为变更

## 4. 验证与回写收敛

- [x] 4.1 基于实现结果生成 `verification.md`，覆盖：
  - spec-to-implementation 映射（每个 spec requirement 是否覆盖）
  - 物理验证结果（包导入、CLI help、测试通过）
  - grep 确认零残留引用
- [x] 4.2 基于 verification.md 结论生成 `writeback.md`
- [x] 4.3 执行 writeback.md 中定义的回写目标
