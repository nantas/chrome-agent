# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `pipeline-converters` spec 覆盖：`converter-location-in-lib`、`converter-importers-updated`、`converter-internal-imports` 三条 requirement
- [x] 1.2 确认 `mediawiki-api-extraction-pipeline` spec 覆盖：`phase-function-naming`、`phase-naming-in-logs` 两条 requirement
- [x] 1.3 确认 `html_to_markdown.py` 当前 4 个 import 方无新增引用（vs 规划文档附录 A 的清单）

## 2. 核心实现任务

### 2.1 移动 `html_to_markdown.py` → `lib/extraction/converter.py` (spec: pipeline-converters)

- [x] 2.1.1 移动文件
  - 执行: `mv scripts/pipeline/converters/html_to_markdown.py scripts/lib/extraction/converter.py`
  - 验证: `ls scripts/lib/extraction/converter.py` 存在；`ls scripts/pipeline/converters/html_to_markdown.py` 不存在

- [x] 2.1.2 更新 docstring 中的 import 示例
  - 文件: `scripts/lib/extraction/converter.py`
  - 修改行 6: `from scripts.mediawiki_api_extract.converters.html_to_markdown import HtmlToMarkdownConverter` → `from scripts.lib.extraction.converter import HtmlToMarkdownConverter`
  - 验证: 文件内无残留 `mediawiki_api_extract` 或 `mediawiki-api-extract` 引用

### 2.2 更新 4 个 import 方 (spec: pipeline-converters/converter-importers-updated)

- [x] 2.2.1 更新 `pipeline/converters/__init__.py`
  - 文件: `scripts/pipeline/converters/__init__.py`
  - 修改行 6: `from .html_to_markdown import HtmlToMarkdownConverter` → `from scripts.lib.extraction.converter import HtmlToMarkdownConverter`
  - 验证: `python3 -c "from scripts.pipeline.converters import HtmlToMarkdownConverter; print(HtmlToMarkdownConverter.__module__)"` 输出含 `lib.extraction.converter`

- [x] 2.2.2 更新 `pipeline/strategies/__init__.py`
  - 文件: `scripts/pipeline/strategies/__init__.py`
  - 修改行 227: `from ..converters.html_to_markdown import HtmlToMarkdownConverter` → `from scripts.lib.extraction.converter import HtmlToMarkdownConverter`
  - 验证: `python3 -c "from scripts.pipeline.strategies import HtmlToMarkdownConverter; print(HtmlToMarkdownConverter.__module__)"` 输出含 `lib.extraction.converter`

- [x] 2.2.3 更新 `pipeline/standalone.py`
  - 文件: `scripts/pipeline/standalone.py`
  - 修改行 13: `from .converters.html_to_markdown import HtmlToMarkdownConverter` → `from scripts.lib.extraction.converter import HtmlToMarkdownConverter`
  - 验证: `python3 -m scripts.pipeline --help` 正常

- [x] 2.2.4 更新 `scripts/explore/sample_converter.py`
  - 文件: `scripts/explore/sample_converter.py`
  - 修改行 438: `importlib.import_module('scripts.mediawiki-api-extract.converters.html_to_markdown')` → `importlib.import_module('scripts.lib.extraction.converter')`
  - 验证: 运行 explore 流程（sample 转换）→ 产出与重构前一致

- [x] 2.2.5 全局验证：确认无残留旧路径引用
  - 执行: `grep -rn "from.*pipeline.*converters.*html_to_markdown\|from.*mediawiki-api-extract.*converters.*html_to_markdown\|from.*mediawiki_api_extract.*converters.*html_to_markdown" scripts/ --include="*.py" | grep -v __pycache__`
  - 验证: 零匹配
  - 执行: `grep -rn "scripts.mediawiki-api-extract.converters.html_to_markdown\|scripts.mediawiki_api_extract.converters.html_to_markdown" scripts/ --include="*.py" | grep -v __pycache__`
  - 验证: 零匹配

### 2.3 重命名 Phase 函数 (spec: mediawiki-api-extraction-pipeline/phase-function-naming)

- [x] 2.3.1 重命名 `discovery_homepage.py` 函数
  - 文件: `scripts/pipeline/pipeline/phases/discovery_homepage.py`
  - 替换: `def run_phase_0` → `def run_homepage_discovery`
  - 验证: `grep "def run_homepage_discovery" scripts/pipeline/pipeline/phases/discovery_homepage.py` 非空

- [x] 2.3.2 重命名 `discovery_allpages.py` 函数
  - 文件: `scripts/pipeline/pipeline/phases/discovery_allpages.py`
  - 替换: `def run_phase_a` → `def run_allpages_discovery`
  - 验证: `grep "def run_allpages_discovery" scripts/pipeline/pipeline/phases/discovery_allpages.py` 非空

- [x] 2.3.3 重命名 `fetch.py` 函数
  - 文件: `scripts/pipeline/pipeline/phases/fetch.py`
  - 替换: `def run_phase_fetch` → `def run_fetch`
  - 验证: `grep "def run_fetch" scripts/pipeline/pipeline/phases/fetch.py` 非空

- [x] 2.3.4 重命名 `convert.py` 函数
  - 文件: `scripts/pipeline/pipeline/phases/convert.py`
  - 替换: `def run_phase_convert` → `def run_convert`
  - 验证: `grep "def run_convert" scripts/pipeline/pipeline/phases/convert.py` 非空

- [x] 2.3.5 重命名 `assemble.py` 函数
  - 文件: `scripts/pipeline/pipeline/phases/assemble.py`
  - 替换: `def run_phase_c` → `def run_assemble`
  - 验证: `grep "def run_assemble" scripts/pipeline/pipeline/phases/assemble.py` 非空

- [x] 2.3.6 更新 `orchestrator.py` 中的 import 和调用
  - 文件: `scripts/pipeline/pipeline/orchestrator.py`
  - 替换 import 行 19-29:
    - `from .phases.discovery_allpages import run_phase_a` → `run_allpages_discovery`
    - `from .phases.assemble import run_phase_c` → `run_assemble`
    - `from .phases.discovery_homepage import run_phase_0` → `run_homepage_discovery`
    - `from .phases.fetch import run_phase_fetch` → `run_fetch`
    - `from .phases.convert import run_phase_convert` → `run_convert`
  - 替换所有调用位置（行 182, 196, 309, 332, 395）
  - 验证: `grep -rn "run_phase_" scripts/pipeline/pipeline/orchestrator.py` 零匹配

- [x] 2.3.7 全局验证：确认无残留旧函数名
  - 执行: `grep -rn "def run_phase_\|run_phase_0\|run_phase_a\|run_phase_c\|run_phase_fetch\|run_phase_convert" scripts/ --include="*.py" | grep -v __pycache__ | grep -v "# was\|# renamed\|docstring"`
  - 验证: 零匹配

### 2.4 精简 orchestrator.py (尽最大努力)

- [x] 2.4.1 提取 discovery_summary 生成逻辑
  - 将 `run_pipeline()` 中 discovery summary 生成段（约 20 行）提取为独立函数或移入已有的 `build_discovery_summary()` 调用
  - 验证: `orchestrator.py` 行数 ≤ 400（目标 ≤350，本次放宽至 400）

## 3. 收敛与验证准备

- [x] 3.1 验证 import 路径完整性
  - 执行: `python3 -m scripts.pipeline --help`
  - 执行: `python3 -c "from scripts.lib.extraction.converter import HtmlToMarkdownConverter; from scripts.pipeline.converters import HtmlToMarkdownConverter; from scripts.pipeline.strategies import HtmlToMarkdownConverter"`
  - 验证: 以上命令均不报 ImportError

- [x] 3.2 验证管线端到端
  - 执行: 对 `bindingofisaacrebirth.wiki.gg` 运行 crawl → 产出与重构前一致
  - 检查点:
    - [ ] Infobox 表格正常
    - [ ] 页面无遗漏
    - [ ] 日志中无 `"Phase 0"` / `"Phase A"` / `"Phase B"` / `"Phase C"` 裸标签
    - [ ] 日志中使用新的函数签名对应的描述性词汇

- [x] 3.3 验证 explore 路径
  - 执行: 对 BOI 站点的 The Sad Onion 页面运行 sample 转换 → 产出与重构前一致

## 4. 验证与回写收敛

- [x] 4.1 基于验证结果生成 verification.md
- [x] 4.2 基于 verification.md 结论生成 writeback.md
- [x] 4.3 执行回写:
  - 更新 `docs/plans/2026-05-19-structure-refactor-and-docs.md` 的 Change 3/4 完成状态
