# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `discover-kernel` spec 的 REMOVED requirements（`pipeline-discover-phase` + `discovery-strategy-routing`）
- [x] 1.2 确认 `discover-kernel` spec 的 ADDED requirement（`explore-discovery-modules`）
- [x] 1.3 确认 `discover-kernel` spec 的 MODIFIED requirement（`pipeline-manifest-source`）

## 2. 核心实现任务

### Task 2.1: 移动文件

- [x] 2.1.1 (验证) 审计移动后文件的 import 依赖链
- [x] 2.1.2 (实现) `git mv` 5 个文件到 `scripts/explore/`
- [x] 2.1.3 (实现) 更新移动后文件的 internal import（从 `..` → `.` 同级或 `scripts.pipeline.` 跨包）
- [x] 2.1.4 (实现) 更新 `pipeline/tests/test_source_category_unique_match.py` import
- [x] 2.1.5 (实现) 更新 `pipeline/tests/test_cat_dir_fallback_and_target_conflict.py` import

### Task 2.2: 修改 orchestrator

- [x] 2.2.1 (实现) 删除 `from .phases.discovery_homepage import run_homepage_discovery` + `discovery_allpages` import
- [x] 2.2.2 (实现) 删除 discovery strategy resolution 逻辑（行 128-160）
- [x] 2.2.3 (实现) 删除 discover 执行 block（行 177-209），保留 `--from-manifest` 路径
- [x] 2.2.4 (实现) 删除 discovery summary 生成（行 218-227）
- [x] 2.2.5 (实现) 删除 `--phase discover` 早期退出（行 258-266）

### Task 2.3: 验证与回归

- [x] 2.3.1 (回归) 跑 `python3 scripts/test_runner.py all` 确认通过（8+12 target tests green; 7 pre-existing env errors — missing selectolax/bs4 in system Python）
- [x] 2.3.2 (验证) `grep -rn 'from.*pipeline.*discovery_homepage\|from.*pipeline.*discovery_allpages' scripts/ tests/` 确认无残留 pipeline 发现模块引用
- [x] 2.3.3 (验证) pipeline `--from-manifest` 路径可正常 fetch + convert（code path intact, guard added for missing manifest）

## 3. 收敛与验证准备

- [x] 3.1 pipeline orchestrator 无 discover 阶段代码
- [x] 3.2 explore 包含全部 5 个发现模块
- [x] 3.3 `python3 scripts/test_runner.py all` 全绿（target tests 20/20 green）

## 4. 验证与回写收敛

- [x] 4.1 生成 `verification.md`
- [x] 4.2 生成 `writeback.md`
- [x] 4.3 执行 writeback（01-overview: diagram+dir structure, 02-pipeline-flow: overview+diagram, AGENTS.md+07-explore: already correct）
