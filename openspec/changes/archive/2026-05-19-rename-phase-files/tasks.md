# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `specs/pipeline-phase-naming/spec.md` 中所有 requirement 有对应实现任务覆盖
- [x] 1.2 确认前置条件：Change 3 已完成，`pipeline/pipeline/phases/fetch.py` 和 `convert.py` 已存在

## 2. 核心实现任务

### 2.1 移动 phase_0.py → phases/discovery_homepage.py

- [x] 2.1.1 `git mv scripts/pipeline/pipeline/phase_0.py scripts/pipeline/pipeline/phases/discovery_homepage.py`
- [x] 2.1.2 更新 `discovery_homepage.py` 内部 import：`.homepage_parser` → `..homepage_parser`，`.page_assigner` → `..page_assigner`
- [x] 2.1.3 更新 `orchestrate.py` import：`from .phase_0 import run_phase_0` → `from .phases.discovery_homepage import run_phase_0`
- [x] 2.1.4 验证：`python3 -c "from scripts.pipeline.pipeline.phases.discovery_homepage import run_phase_0; print('OK')"`

**Spec 覆盖**: `phase-file-naming-alignment` (discovery_homepage)
**验证方式**: import 成功 + `python3 -m scripts.pipeline --help` 正常

### 2.2 移动 phase_a.py → phases/discovery_allpages.py

- [x] 2.2.1 `git mv scripts/pipeline/pipeline/phase_a.py scripts/pipeline/pipeline/phases/discovery_allpages.py`
- [x] 2.2.2 更新 `discovery_allpages.py` 内部 import：`..client` → `...client`，`..strategies` → `...strategies`
- [x] 2.2.3 更新 `orchestrate.py` import：`from .phase_a import run_phase_a` → `from .phases.discovery_allpages import run_phase_a`
- [x] 2.2.4 验证：`python3 -c "from scripts.pipeline.pipeline.phases.discovery_allpages import run_phase_a; print('OK')"`

**Spec 覆盖**: `phase-file-naming-alignment` (discovery_allpages)
**验证方式**: import 成功 + `python3 -m scripts.pipeline --help` 正常

### 2.3 移动 phase_c.py → phases/assemble.py

- [x] 2.3.1 `git mv scripts/pipeline/pipeline/phase_c.py scripts/pipeline/pipeline/phases/assemble.py`
- [x] 2.3.2 更新 `assemble.py` 内部 import：`..strategies` → `...strategies`
- [x] 2.3.3 更新 `orchestrate.py` import：`from .phase_c import run_phase_c` → `from .phases.assemble import run_phase_c`
- [x] 2.3.4 验证：`python3 -c "from scripts.pipeline.pipeline.phases.assemble import run_phase_c; print('OK')"`

**Spec 覆盖**: `phase-file-naming-alignment` (assemble)
**验证方式**: import 成功 + `python3 -m scripts.pipeline --help` 正常

### 2.4 拆分并删除 phase_b.py

- [x] 2.4.1 将 `phase_b.py` 中 `fetch_single_page` 函数（行 27-43）复制到 `phases/fetch.py`，放在 `run_phase_fetch` 函数之前
- [x] 2.4.2 更新 `phases/fetch.py`：移除 `from ..phase_b import fetch_single_page`，添加 `from ...client import ApiClient, PageNotFoundError` 和 `from ...strategies import ContentAcquisitionStrategy`（如尚未存在）
- [x] 2.4.3 将 `phase_b.py` 中 `convert_single_page`（行 44-132）和 `_process_html_page`（行 167-250）复制到 `phases/convert.py`，放在 `run_phase_convert` 函数之前
- [x] 2.4.4 更新 `phases/convert.py`：移除 `from ..phase_b import convert_single_page`，添加缺失的 import（`from ...client import PageNotFoundError`、`from ...strategies import HtmlRenderedAcquisitionStrategy, HtmlToMarkdownConverter, LinkResolver, TemplateProcessor`、`from ...strategies import convert_wikitext_to_markdown`）
- [x] 2.4.5 添加 `from __future__ import annotations` 到 `phases/convert.py`（`_process_html_page` 使用了 `dict | None` 语法）
- [x] 2.4.6 删除 `scripts/pipeline/pipeline/phase_b.py`
- [x] 2.4.7 从 `orchestrate.py` 移除 `from .phase_b import run_phase_b`
- [x] 2.4.8 验证：`python3 -c "from scripts.pipeline.pipeline.phases.fetch import run_phase_fetch, fetch_single_page; from scripts.pipeline.pipeline.phases.convert import run_phase_convert, convert_single_page; print('OK')"`

**Spec 覆盖**: `phase-b-function-consolidation`, `dead-code-removal`
**验证方式**: import 成功 + 无 `phase_b` 引用残留

### 2.5 删除顶层残留旧文件

- [x] 2.5.1 删除 `scripts/pipeline/phase_a.py`
- [x] 2.5.2 删除 `scripts/pipeline/phase_b.py`
- [x] 2.5.3 删除 `scripts/pipeline/phase_c.py`
- [x] 2.5.4 验证：`grep -rn "phase_b\|phase_c" scripts/pipeline/ --include="*.py"` 确认仅 `phases/` 内有合法引用

**Spec 覆盖**: `dead-code-removal` (stale-top-level-files-removal)
**验证方式**: 文件不存在 + grep 零残留

### 2.6 可选：orchestrate.py → orchestrator.py

- [x] 2.6.1 `git mv scripts/pipeline/pipeline/orchestrate.py scripts/pipeline/pipeline/orchestrator.py`
- [x] 2.6.2 更新 `pipeline/pipeline/__init__.py` 中 `from .orchestrate import ...` → `from .orchestrator import ...`
- [x] 2.6.3 更新 `pipeline/cli.py` 中 `from .pipeline import run_pipeline, EXIT_INVALID_ARGS` — 确认此处通过 `__init__.py` 间接引用，无需修改
- [x] 2.6.4 验证：`python3 -m scripts.pipeline --help` 正常

**Spec 覆盖**: N/A (治理对齐，非 spec 约束)
**验证方式**: CLI 入口正常

## 3. 全局验证

- [x] 3.1 零旧引用检查：`grep -rn "from.*\.phase_0\|from.*\.phase_a\|from.*\.phase_b\|from.*\.phase_c" scripts/pipeline/ --include="*.py"` → 返回空
- [x] 3.2 零 `phase_b` 残留：`grep -rn "phase_b" scripts/pipeline/ --include="*.py"` → 仅注释/docstring 中提及
- [x] 3.3 Python 测试通过：`python3 scripts/pipeline/tests/test_discovery_summary.py`
- [x] 3.4 Node.js 测试通过：`node --test tests/`
- [x] 3.5 CLI 入口正常：`python3 -m scripts.pipeline --help`
- [x] 3.6 LSP diagnostics：`python3 -m scripts.pipeline` 无 import 错误

**Spec 覆盖**: 所有 requirements
**验证方式**: 自动化命令输出
