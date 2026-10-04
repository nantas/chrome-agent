# Proposal

## 问题定义

Crypt Keeper 的 Permanent Conditions 为 colspan=2 的富文本单元格。当前共享转换器保留原格图片，但直接删除延续格图片，产生 `or or` 和缺少状态名称的副本。S5 正确暴露输出质量问题；图片总量不变、与旧产物一致不能证明延续格语义完整。

本 change 承接 fix-conversion-structure-and-audit-fidelity 的剩余问题，细化 fix-wiki-table-sample-integrity 的 merged-cell-asset-retention 约定。

## 范围边界

- 原格保留图片；colspan/rowspan 延续格以可靠文本名称替代图片，保留文字顺序及链接目的。
- 名称优先使用策略精确映射，其次有效 alt/title；文件名式或缺失名称输出明确占位，禁止猜测。
- 增加可校验的策略配置，补充 DD2 已知文件名标签映射；共享内核统一生效。
- 升级转换契约版本，离线回放 209 页并独立审查预期差异，保持 S5 检查强度。
- 不处理锚点缺口、跨 DD1 映射、通用图片命名或 wikitext；不重抓、不发布正式 collection。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `table-grid-parser`: 合并单元格延续槽位以可靠文本表示图标，不复制资产、不删除语义。
- `strategy-schema`: 支持合并单元格图标名称的精确映射配置及非法配置显式失败。

## Capabilities 待确认项

无阻塞项；能力归属依据现有永久规范及表格修复 delta，用户已授权整理讨论方案创建 change。

## Impact

影响 converter.py、extraction/schema.py、能力注册、DD2 策略及相关测试；转换缓存须失效。可能改变其他站点含图片的合并格副本，验收不能只检查 Crypt Keeper。无新依赖，遵循 Python 3.9、共享内核及 vertical slice TDD。

## 关联绑定

见 binding.md；沿用 OrbitOS v0.3 标准引用，实施验证后回写转换器架构、策略 Schema 和 handoff。
