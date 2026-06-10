# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 6 个 capability spec 文件已创建且无占位符（`test-runner`, `golden-diff`, `sample-discovery`, `explore-scaffold`, `pipeline-fetch`, `strategy-schema`）
- [x] 1.2 确认 `scripts/pipeline/tests/test_table_grid.py` 为唯一使用 `pytest` 的文件，评估迁移范围

## 2. 核心实现任务

### 2.1 测试目录结构与基础（`test-runner`）

- [x] 2.1.1 创建 `tests/` 顶层目录结构：`tests/__init__.py`、`tests/lib/__init__.py`、`tests/pipeline/__init__.py`
  - 验证：`python -m unittest discover -s tests -v` 可执行（即使无测试文件也不报错）

- [x] 2.1.2 清理 `scripts/pipeline/tests/test_table_grid.py` 中的 `pytest` 依赖
  - 将 `import pytest` 替换为 `import unittest`
  - 将 `def test_xxx()` 转换为 `class TestXxx(unittest.TestCase)` + `def test_xxx(self)`
  - 验证：`python -m unittest scripts.pipeline.tests.test_table_grid` 通过

### 2.2 通用测试入口 `test_runner.py`（`test-runner`）

- [x] 2.2.1 新增 `scripts/test_runner.py`，实现 `all` 子命令
  - `all`：调用 `unittest discover -s tests`，然后调用站点样本 runner
  - 验证：`python3 scripts/test_runner.py all` 执行不报错

- [x] 2.2.2 实现 `site-samples` 子命令
  - 扫描 `sites/strategies/*/strategy.md`，提取 `samples` 字段
  - 为每个 `(domain, page)` 动态生成 `unittest.TestCase` 类（I2）
  - 支持 `--domain <domain>` 过滤
  - 验证：对无 samples 的策略目录，输出 "0 test cases generated"；对有 samples 的目录，生成正确数量的独立 TestCase

### 2.3 结构断言规则集（`golden-diff`）

- [x] 2.3.1 新增 `scripts/lib/test_assertions.py`，实现三个内置断言函数
  - `assert_no_raw_html_tags(md_text)` — 检测残留 HTML 标签
  - `assert_links_resolved(md_text)` — 检测未解析的 `../Pages/Page_*.html` 链接
  - `assert_valid_md_tables(md_text)` — 检测表格列数一致性
  - 每个断言失败时抛出 `AssertionError` 并附带描述性消息
  - 验证：用包含各类问题的 MD 文本测试每个断言的 pass/fail 行为

- [x] 2.3.2 将结构断言集成到 site-samples runner
  - 每个 TestCase 在 golden diff 前先运行结构断言
  - 结构断言失败 = test FAIL + 描述性消息
  - 验证：用已知有问题的 golden file 跑 runner，确认断言正确捕获

### 2.4 Golden diff 机制（`golden-diff`）

- [x] 2.4.1 实现 golden diff 对比逻辑
  - 从 `.cache/` 读取样本页面 HTML → 调用 `html_to_markdown()` 转换 → 读取 `sites/strategies/<domain>/samples/<page>.md` golden → unified diff
  - diff 为空 → PASS；diff 存在 → FAIL + 输出 diff
  - 支持 `--update-golden` 刷新 golden file
  - 验证：创建测试用策略 + cache + golden，确认 diff 正确检测变更

### 2.5 站点策略 schema 扩展（`strategy-schema` + `sample-discovery`）

- [x] 2.5.1 更新 `docs/architecture/03-strategy-schema.md`，新增 `samples` 字段定义
  - 字段名：`samples`
  - 类型：`array of {page: string, label: string}`
  - 必填：否（可选字段）
  - 默认值：空列表
  - 验证：文档 review

- [x] 2.5.2 更新 `strategy_loader.py`（如需要），确保 `samples` 字段可被正确解析
  - 验证：加载含 `samples` 字段的 strategy.md，确认 frontmatter 解析输出包含 `samples` 数组

### 2.6 治理文档更新

- [x] 2.6.1 更新 `AGENTS.md` §0.5：扩展 C5 描述 + 新增 C9 测试义务硬约束
  - C5 扩展：补充目录约定（`tests/` 顶层）、运行命令
  - C9 新增：修改 `scripts/lib/`、`scripts/pipeline/pipeline/phases/`、`scripts/lib/extraction/` 时必须新增或更新 `tests/` 对应测试；修改站点策略时必须运行 `site-samples` 确认回归通过
  - 验证：文档 review

- [x] 2.6.2 更新 `AGENTS.md` §9 Reference Index：新增 `tests/` 目录、`scripts/test_runner.py`、`scripts/lib/test_assertions.py` 条目
  - 验证：文档 review

- [x] 2.6.3 更新 `AGENTS.md` §11 Prerequisite Reading：新增"测试相关任务"行
  - 必读：`docs/architecture/08-tech-stack.md` §4 + 本 change specs
  - 验证：文档 review

- [x] 2.6.4 重写 `docs/architecture/08-tech-stack.md` §4 Test Infrastructure
  - 目录结构（`tests/` 顶层 + 站点 golden files 跟策略走）
  - 运行命令（`python -m unittest discover -s tests`、`python3 scripts/test_runner.py site-samples`、`python3 scripts/test_runner.py all`）
  - 站点样本回归机制说明（I2 动态 TestCase、golden diff、`--update-golden`）
  - 结构断言规则集说明
  - 验证：文档 review

## 3. 收敛与验证准备

- [x] 3.1 为 cdp-cache-pipeline-tooling 的 5 个新增模块补齐单元测试
  - `tests/lib/test_html_to_markdown.py`
  - `tests/lib/test_markdown_link_resolver.py`
  - `tests/lib/test_cdp_image_downloader.py`
  - `tests/pipeline/test_fetch_cdp.py`
  - `tests/pipeline/test_convert_html.py`
  - 验证：`python -m unittest discover -s tests -v` 全部通过

- [x] 3.2 运行 `python3 scripts/test_runner.py all` 确认全部测试通过
- [x] 3.3 用 Nintendo 站点策略做端到端验证：补 samples 清单 → 创建 golden → 跑 site-samples → 通过

## 4. 验证与回写收敛

- [x] 4.1 基于验证结果生成 `verification.md`
- [x] 4.2 基于 verification 结论生成 `writeback.md`
- [x] 4.3 执行文档回写（见 2.6），记录回写证据
