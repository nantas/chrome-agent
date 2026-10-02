# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 读取 `specs/explore-workflow/spec.md`、`specs/governance/spec.md`、design 与对应 AGENTS 必读文档；确认只修改 main.py 启动路径与 generateHandoff 命名，记录需求到实现/测试映射。
- [x] 1.2 确认应用层依赖与解释器可用，检查工作区已有改动；确定离线 CLI fixture 和真实入口测试 seam，不替换待验证的 import 路径或 slug 生产逻辑。

## 2. 核心实现任务（按 slice 顺序执行）

- [x] 2.1 RED：在 `tests/` 新增 unittest 子进程测试，移除 PYTHONPATH，从临时 cwd 执行真实 main.py --help，断言帮助成功；先运行并记录原始 scripts ModuleNotFoundError。
- [x] 2.2 GREEN：在 `scripts/explore/main.py` 模块导入前基于 __file__ 加入仓库根路径，保留 sibling import；立即重跑 2.1 并记录通过。
- [x] 2.3 为同一入口补充 repo cwd 场景及真实 CLI strategy-gap 离线集成验证，断言启动后抵达可控 probe 边界，未再出现原始导入异常；若发现新失败，先记录 RED 再最小修复并验证 GREEN。
- [x] 2.4 RED：以 node:test 的真实 CLI 内部失败 fixture 触发有 runDir 的 handoff，断言原目标的精确 slug、JSON handoff_path/文件存在/文档目标与错误，记录当前 undefined 命名失败。
- [x] 2.5 GREEN：generateHandoff 从 nowParts 仅取 stamp，使用现有 slugify(target) 生成 slug；立即重跑 2.4 验证通过。
- [x] 2.6 补充无 runDir 的内部失败、空归一化 slug 回退 target、长 slug/标点归一化用例，验证 governance spec 各场景；必要测试 seam 先写行为测试再实现，不复制生产 slug 算法形成循环验证。

## 3. 收敛与验证准备

- [x] 3.1 运行受影响 Python/Node 测试，然后执行 `python3 -m unittest discover -s tests -v` 与适用 Node 全量测试；记录实际解释器、命令、结果与既有失败，检查无临时 DEBUG 日志或未清理 fixture。
- [x] 3.2 从外部 cwd、无 PYTHONPATH 环境重跑原始 `chrome-agent explore https://darkestdungeon.wiki.gg/wiki/Darkest_Dungeon_Wiki_1`，记录启动异常已消失的证据和真实上游结果；不将独立网络/引擎故障等同于本缺陷，不进入 extraction。
- [x] 3.3 按 C10 / 全局安装 playbook Case 6 同步 runtime、skill，刷新 installed-hash 至当前 git HEAD，核对副本一致性；运行 `chrome-agent doctor --format json` 与 `chrome-agent doctor --check capabilities` 并记录结果，能力检查必须在归档前通过。

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成 verification.md，逐项覆盖两个 spec 的 requirement/scenario、实现文件、task-to-evidence、RED/GREEN 证据与原目标重跑结果；明确未覆盖项或独立环境失败。
- [x] 4.2 回写前解析并读取 binding 的 spec_standard_ref，基于 verification 生成 writeback.md，列明 capability/spec 增量、目标、字段映射、时间/执行人/结果和前置条件。
- [x] 4.3 完成 binding 中两个架构文档的结论回写并记录证据；归档时分别合并 delta 到 `openspec/specs/explore/explore-deep-discovery.md` 的 deep-discovery 块与 `openspec/specs/governance/handoff.md` 的 handoff-storage-path 块，保持其它要求，不创建平行真源。
- [x] 4.4 运行 OpenSpec strict validate，核对 tasks/verification/writeback 闭环、所有回写目标结果和 capabilities 检查证据后再声明具备归档条件。
