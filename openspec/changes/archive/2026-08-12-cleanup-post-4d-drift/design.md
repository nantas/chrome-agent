# Design

## 决策 1：直接删除而非保留 deprecation 过渡

`discovery_summary.py` 全仓零 import（含 `.mjs` spawn 路径），无运行时调用方可达，无需过渡期。测试文件测的是副本而非模块本身，同步删除。

## 决策 2：等价证明指针替换而非并存

`test_golden_convert.py` 与 `test_convert_equivalence.py` 并存会造成「哪个是真证明」的二义（ADR 0013 反模式：无声明的重复）。新测试覆盖旧测试的全部意图且更强（三镜像 + 内核、内嵌 fixture 不 skip、含 KI 字符哨兵），旧测试删除。

## 决策 3：zombie requirements 用 REMOVED 而非改写

pipeline-discovery 的 3 个 requirement 规定的是模块组织（文件必须存在/测试必须通过），不是外部行为。模块删除后改写无意义，直接 REMOVED。`discovery_summary.json` 的产出行为由 cli.mjs 承担，属 CLI 行为域，不在本 spec 重建 requirement（YAGNI：无消费方投诉其缺失）。

## 风险

- 删除被外部脚本依赖：已验证全仓（含 docs/、openspec/ 活动 change）无 import；openspec 归档目录中的引用为历史记录，不改。
