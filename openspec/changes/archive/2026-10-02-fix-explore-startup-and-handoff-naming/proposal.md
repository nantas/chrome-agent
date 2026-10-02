# Proposal

## 问题定义

跨仓库执行 `chrome-agent explore https://darkestdungeon.wiki.gg/wiki/Darkest_Dungeon_Wiki_1` 在 deep discovery 启动时失败，交接错误为 `ModuleNotFoundError: No module named 'scripts'`，属于 P-line 代码缺陷。

`main.py:24` 仅将入口目录 `scripts/explore/` 放入 sys.path。提交 `d10858db`（2026-09-11）在 `architecture_gate.py:11` 新增 `from scripts.lib.extraction.schema import ...`，该导入依赖仓库根目录可见，但入口没有建立此条件。CLI 虽设置 cwd=repoRoot，Python 直接执行脚本时也不会因此自动将根目录加入 sys.path。

已完成确定性最小复现：清除 PYTHONPATH，在 /tmp 中执行 `python3 /Users/nantas-agent/projects/chrome-agent/scripts/explore/main.py --help`，连续两次得到原始异常；仅切换 cwd 到仓库根仍失败；仅补充 PYTHONPATH 为仓库根后退出 0 并显示帮助。现有测试以包导入方式加载 architecture_gate，未覆盖真实入口子进程。

附带独立缺陷：`generateHandoff()` 从 `nowParts()` 解构 slug，但后者只返回 date/stamp，导致交接目录出现 `explore-undefined`。正常运行目录已使用 `slugify(targetUrl)`，可复用相同规则。

## 范围边界

纳入：
- 在 Explore 入口导入其它模块之前，基于 __file__ 定位并加入仓库根目录，保留已有 sibling import 兼容性。
- 通过真实 main.py 子进程测试锁定清除 PYTHONPATH 后的入口启动行为；覆盖仓库 cwd 与外部 cwd。
- Handoff 命名从 target 派生 slug，复用现有 slugify 规则与空值回退 target；覆盖有/无 runDir 两类内部失败。
- 保留 failure、handoff_path、错误详情与工作流 Gate；执行 CLI 修改后的全局同步。

排除：网站策略创建、实际批量抓取、引擎升级、Python 环境重构、全部 Explore 模块入口迁移、历史交接目录重命名。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `explore-workflow`: 使 deep discovery 的真实脚本入口独立于调用方 cwd/PYTHONPATH 完成仓库内模块导入；新增入口子进程回归契约。
- `governance`: 修正已有 handoff-storage-path 契约的 target slug 来源，保证有/无运行目录时均生成有效交接路径。

## Capabilities 待确认项

- [x] 2026-10-02 用户回复“能力确认”，确认两个已有能力修改项；governance 的冻结要求位于 `openspec/specs/governance/handoff.md`，本 change delta 使用 `specs/governance/spec.md` 并明确归档合并目标，避免新增平行真源。

## Impact

- 实现位置：`scripts/explore/main.py`、`scripts/chrome-agent-cli.mjs` 的 generateHandoff。
- 测试位置：`tests/` 中 Python unittest 子进程测试与 Node node:test CLI 内部失败测试；使用离线 fixture/stub，不依赖网站或浏览器。
- Python 保持 3.9+ 兼容；Node 纯 ESM、顶层 function 声明，不引入第三方测试依赖。
- CLI 参数、解释器 resolveAppPython 规则、discovery/confirmation Gate 保持原有契约。
- 验收：确定性入口测试、真实 CLI 离线 handoff 测试、Python/Node 回归、doctor --check capabilities、C10 同步及 verification/writeback 证据。
- 原始目标命令在实现阶段验证启动故障已解除；若有网络或引擎失败，单独记录实际结果，不将 --help 成功等同于网站抓取成功，不进入未授权 extraction。

## 关联绑定

- 关联 binding：`binding.md`。
- 标准、项目页面与回写目标遵循 binding 所列引用；此阶段不实施代码修改或外部回写。
