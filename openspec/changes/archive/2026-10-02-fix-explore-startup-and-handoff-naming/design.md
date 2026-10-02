# Design

## Context

行为依据：`specs/explore-workflow/spec.md` 的 deep-discovery 与 `specs/governance/spec.md` 的 handoff-storage-path。已确认入口失败由脚本执行模式下仓库根目录不在 sys.path 导致；命名失败由 nowParts 不提供 slug 导致。

## Goals / Non-Goals

**Goals:** 真实 Explore 入口在无 PYTHONPATH、任意 cwd 下可导入共享库；内部失败交接使用 target 派生的有效 slug；通过真实启动方式验证两个问题。

**Non-Goals:** 不迁移全部 Python 入口为 -m，不改解释器解析、策略/引擎选择、抓取范围或 Gate，不重命名历史 handoff，不引入测试依赖。

## Decisions

1. **入口建立 import path。** 在 main.py 导入 Explore 模块前，使用 __file__ 的绝对路径推导仓库根并加入 sys.path；保留 scripts/explore 的 sibling import 路径。由实际入口负责建立条件，不在 architecture_gate 内加环境补丁，不改用户 PYTHONPATH。单改 cwd 无效；CLI 注入 PYTHONPATH 只能覆盖单个调用方；全量模块入口迁移超出本次范围。
2. **命名复用 slugify。** generateHandoff 仅从 nowParts 取得 stamp，再以 slugify(target) 生成 slug。沿用现有 lowercase/标点归一化/80 字符限制和空结果回退 target；不扩充 nowParts 的职责，不假设 runDir 已存在。缺失/非字符串 target 不在有效内部失败输入契约内，本次不扩大参数 API。
3. **真实调用方式测试。** Python unittest 在临时 cwd 和 repo cwd 启动真实 main.py --help，复制 env 后移除 PYTHONPATH，使用 sys.executable、capture_output 和短超时；断言返回 0、帮助标识和原始异常不存在。依赖必须预先可用，不能靠 skip 掩盖失败。随后用真实 CLI、真实入口和可控本地 probe fixture 验证 strategy-gap 路由；替换网络/引擎边界，不替换入口和 architecture_gate import。
4. **交接测试使用 CLI 内部失败边界。** Node node:test 以临时仓库/已存在测试 fixture 离线触发有 runDir 的 discovery 失败和无 runDir 的依赖预检失败。检查 JSON handoff_path、文件存在、精确 target slug、文档原始 target/错误/运行目录引用，以及 failure envelope。空 slug 与长 slug 用同一真实命名实现的可控输入测试补充，避免复制生产实现来计算期望值；必要时只增加最小测试 seam，保持 CLI 顶层 function/ESM 约束。
5. **同步与治理。** CLI 为 repo-backed launcher 加载的代码；实现后按 C10/Case 6 刷新全局 runtime、skill 和 installed-hash，记录同步与 doctor 证据。归档合并到两个 delta 中指定的 merged spec 文件；自动 merge 若只认 spec.md，必须人工对目标 requirement 做完整块合并，避免重复真源。

## Risks / Migration

- 根路径加入顺序需确保本仓库 scripts 优先且 sibling imports 仍可解析；通过真实入口与相关 Explore 回归测试验证。
- --help 只证明启动。CLI 离线集成验证路由；原始 URL 重跑独立记录网络/引擎结果，不把其它失败误判为本缺陷仍存在或抓取成功。
- 改动可通过回退 main.py 的路径初始化与 generateHandoff 的 slug 来源撤销；历史交接文件保持原路径。
- 不解决同秒同 target 的 handoff 碰撞；该行为与本缺陷无关。
- 外部标准在回写前读取；verification/writeback 仅在实现有真实证据后生成。
