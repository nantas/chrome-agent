# 回写

目标：docs/architecture/05-converter-architecture.md，更新表格转换说明。Delta 规范留在当前 active change，待评审归档时合并，当前不归档。


## 2026-10-03 全量交付核验

最终 440 页（原 438 页加误排两首领），226 重定向核验。图片与标题完整，表格格式通过，目录本地目标 36,893 项零断链，额外章节目标审计零问题。242 项 Python 与七样本通过。全量剩余 74 页启发式告警已保留来源证据，不作为自动全部通过；原 HTML 分词 Pull/ed 合并为 Pulled 已人工核对。交付及证据：/Users/nantas-agent/projects/my-wiki/30-raw/external/game-wikis/darkest-dungeon-1/_metadata/采集与质量报告.md。

最终兼容性检查：222 处双层来源引用标签转为普通 Markdown 链接。修复后本目录普通链接目标 37,013 项零断链、Wiki Link 零问题；全仓仍有原有 101 条 Wiki Link 及 38 条 frontmatter 引用问题。

## 2026-10-04 前置规范同步记录

在 fix-merged-cell-icon-semantics 归档时，本 change 的 delta 已同步至永久规范；本目录仍 active。后续归档应保留已同步结果。merged-cell-asset-retention 已被后续 change 更新为副本语义标签契约，不得用早期 block 回退；其余未提及场景保持。
