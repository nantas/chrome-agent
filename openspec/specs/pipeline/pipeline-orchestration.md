# Pipeline Domain: Orchestration — Merged Spec

## Source Attribution

| Source Spec | Type |
|------------|------|
| `pipeline-orchestration` | frozen |
| `pipeline-phases-fetch` | frozen |
| `pipeline-phases-convert` | frozen |
| `pipeline-resume` | frozen |
| `api-error-semantics` | frozen |

Paths have been updated to reflect the current directory structure.

---

# Pipeline Orchestration Specification

## Purpose

Defines the pipeline orchestrator responsibilities, phase module extraction (fetch/convert as independent modules), checkpoint/resume support, and API error semantics including the `PageNotFoundError` exception hierarchy.

---

## Requirements

### Requirement: orchestrator-responsibility

`pipeline/orchestrator.py` SHALL 仅包含：exit code 常量、`validate_api_config()` 函数、`run_pipeline()` 主编排函数。所有从 `registry.py`、`discovery_summary.py`、`phases/fetch.py`、`phases/convert.py` 导入的符号通过明确的 import 声明依赖。

#### Scenario: orchestrator-size-limit
- **WHEN** `orchestrator.py` 完成重构
- **THEN** 文件行数 ≤ 350 行
- **AND** 不包含 `_STRATEGY_REGISTRY`、`build_pipeline`、`build_discovery_summary`、`run_phase_fetch`、`run_phase_convert` 的定义

#### Scenario: orchestrator-delegates
- **WHEN** `run_pipeline()` 需要构建管线策略 → 调用 `registry.build_pipeline()`
- **WHEN** `run_pipeline()` 需要构建发现摘要 → 调用 `discovery_summary.build_discovery_summary()`
- **WHEN** `run_pipeline()` 执行 fetch phase → 调用 `phases.fetch.run_phase_fetch()`
- **WHEN** `run_pipeline()` 执行 convert phase → 调用 `phases.convert.run_phase_convert()`

### Requirement: run-pipeline-no-behavior-change

`run_pipeline()` 的端到端行为 SHALL 与重构前完全一致。

#### Scenario: end-to-end-preservation
- **WHEN** 执行 `python3 -m scripts.pipeline pipeline <url> --strategy <path> --output <dir>`
- **THEN** 产出与重构前完全相同，退出码语义不变

### Requirement: public-api-compatibility

`pipeline/pipeline/__init__.py` SHALL 重新导出所有 `orchestrator.py` 中的公共 API，确保消费者 import 路径不需要更改符号名。

#### Scenario: init-re-exports
- **WHEN** `from scripts.pipeline.pipeline import run_pipeline, EXIT_SUCCESS` 被执行
- **THEN** 成功获取对应符号

### Requirement: fetch-phase-module

系统 SHALL 将 `run_phase_fetch()` 函数从 `orchestrate.py` 提取到独立模块 `pipeline/phases/fetch.py`。

#### Scenario: module-extraction
- **WHEN** `pipeline/phases/fetch.py` 被创建
- **THEN** 文件包含 `run_phase_fetch()` 函数及其内部 `_fetch_one()` 辅助函数
- **AND** 函数签名、并发逻辑、缓存跳过逻辑、统计计数与重构前完全一致

### Requirement: fetch-phase-imports

模块 SHALL 从同级模块导入，不依赖 `orchestrator.py`。

#### Scenario: self-contained-imports
- **WHEN** `phases/fetch.py` 的 import 被审查
- **THEN** 不存在对 `orchestrator.py` 或 `orchestrate.py` 的 import

### Requirement: fetch-phase-no-behavior-change

`run_phase_fetch()` 的行为 SHALL 与重构前完全一致。

#### Scenario: fetch-behavior-preservation
- **WHEN** 对同一站点执行 fetch phase
- **THEN** 产出与重构前完全相同

### Requirement: convert-phase-module

系统 SHALL 将 `run_phase_convert()` 函数从 `orchestrate.py` 提取到独立模块 `pipeline/phases/convert.py`。

#### Scenario: module-extraction
- **WHEN** `pipeline/phases/convert.py` 被创建
- **THEN** 文件包含 `run_phase_convert()` 函数，函数签名与重构前完全一致

### Requirement: convert-phase-imports

模块 SHALL 从 `..registry` 导入 `build_pipeline`，不依赖 `orchestrator.py`。

#### Scenario: self-contained-imports
- **WHEN** `phases/convert.py` 的 import 被审查
- **THEN** 不存在对 `orchestrator.py` 或 `orchestrate.py` 的 import

### Requirement: convert-phase-no-behavior-change

`run_phase_convert()` 的行为 SHALL 与重构前完全一致。

### Requirement: state-file-persistence

系统 SHALL 维护 `.pipeline_state.json` 文件追踪 pipeline 进度。包含 `phase`、`completed_pages`、`total_pages`、`last_updated`、`run_id` 字段。

#### Scenario: state-file-created-on-start
- **WHEN** pipeline 以 `--resume` 启动且无已有状态文件
- **THEN** 新状态文件 SHALL 被创建

#### Scenario: state-file-loaded-on-resume
- **WHEN** pipeline 以 `--resume` 启动且已有状态文件
- **THEN** 已完成页面 SHALL 被跳过

### Requirement: page-level-skip-on-resume

fetch/convert phase 中，已完成的页面 SHALL 被跳过（标题在 `completed_pages` 且输出文件存在）。

#### Scenario: skip-completed-page
- **WHEN** 页面在 `completed_pages` 且输出文件存在
- **THEN** 跳过，不发 API 调用

#### Scenario: re-extract-stale-page
- **WHEN** 页面在 `completed_pages` 但输出文件不存在
- **THEN** 重新提取

### Requirement: periodic-state-flush

系统 SHALL 定期将状态写入磁盘（默认每 100 页面，可通过 `--resume-flush-interval` 配置）。phase 完成时也 SHALL 写入最终状态。

### Requirement: resume-cli-flag

`--resume`（默认启用）和 `--no-resume` CLI flags。`--no-resume` 忽略已有状态重新开始。

#### Scenario: resume-enabled-by-default
- **WHEN** 无 `--resume`/`--no-resume` 参数
- **THEN** resume 行为启用，加载已有状态文件

#### Scenario: no-resume-fresh-start
- **WHEN** 使用 `--no-resume`
- **THEN** 不加载已有状态，创建新状态文件

### Requirement: 异常层次结构

系统 SHALL 在 `client.py` 中定义异常层次：

```
Exception
├── PageNotFoundError      # missingtitle, nosuchpage — 可跳过
└── (RuntimeError)         # 其他 API 错误 — 不可恢复
```

`client._request()` SHALL 根据 `data["error"]["code"]` 区分：`missingtitle`/`nosuchpage` → `PageNotFoundError`，其他 → `RuntimeError`。

#### Scenario: missingtitle 触发 PageNotFoundError
- **WHEN** API 返回 `{"error": {"code": "missingtitle"}}`
- **THEN** SHALL 抛出 `PageNotFoundError` 而非 `RuntimeError`

### Requirement: 策略层对 PageNotFoundError 的优雅处理

所有策略层代码（discovery、acquisition、legacy 策略）SHALL 用 `except Exception` 捕获 `PageNotFoundError`，记录 warning 并继续。

#### Scenario: discovery-fetch-list-pages-missing-title
- **WHEN** `AllPagesDiscoveryStrategy.fetch_list_pages()` 中 API 返回 `missingtitle`
- **THEN** SHALL 捕获异常，记录 warning，继续处理下一个条目

### Requirement: Phase A 对 fetch_list_pages 的防御性保护

`run_phase_a()` SHALL 对 `fetch_list_pages()` 调用包裹 try/except，单个 list_page 失败不阻断 Phase A。

#### Scenario: phase-a-fetch-list-pages-graceful
- **WHEN** `fetch_list_pages()` 内部触发 `PageNotFoundError`
- **THEN** SHALL 降级为 warning 并继续

### Requirement: Phase B 对 PageNotFoundError 的优雅处理

`process_single_page()` SHALL 捕获 `PageNotFoundError` 返回 `status: "skipped"`，不记入 failure_count。

#### Scenario: 页面缺失时优雅跳跃
- **WHEN** `content_strategy.fetch_page_content()` 抛出 `PageNotFoundError`
- **THEN** SHALL 返回 `{"title": title, "status": "skipped", "reason": "page_not_found"}`

### Requirement: _process_html_page None-safety

`_process_html_page()` SHALL 正确处理 `html` 值为 `None` 的情况。

#### Scenario: html 值为 None
- **WHEN** raw dict 包含 `{"html": None}`
- **THEN** SHALL 返回 `{"status": "empty", "error": "Empty HTML"}` 而非崩溃
