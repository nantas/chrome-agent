# 验证

- 新回归测试先红后绿（合并图片、表格标题、英文误报、嵌套表格配对）。
- `.venv/bin/python -m unittest discover -s tests -v`：231 项通过。
- 7 样本重新调用共享转换内核及 S1–S12：7/7 通过，0 失败；架构门通过。
- 745 次图片出现及 URL 多重集完全匹配；296 个正文 wiki 目标无缺失；章节与标题总数 59→59。
- 所有样本 Markdown 表格、无原始 HTML 残留断言通过。
- 原站局部锚点在不同 Markdown 阅读器中的兼容性不在本次自动检查覆盖内；远端链接可访问性不作保证。
- 证据：outputs/dd1-quality-fixed/quality-report.json、质量报告.md、python-tests.log、recheck.py。
- 未归档、未提交、未冻结站点策略、未开始批量采集。


## 2026-10-03 全量交付核验

最终 440 页（原 438 页加误排两首领），226 重定向核验。图片与标题完整，表格格式通过，目录本地目标 36,893 项零断链，额外章节目标审计零问题。242 项 Python 与七样本通过。全量剩余 74 页启发式告警已保留来源证据，不作为自动全部通过；原 HTML 分词 Pull/ed 合并为 Pulled 已人工核对。交付及证据：/Users/nantas-agent/projects/my-wiki/30-raw/external/game-wikis/darkest-dungeon-1/_metadata/采集与质量报告.md。

最终兼容性检查：222 处双层来源引用标签转为普通 Markdown 链接。修复后本目录普通链接目标 37,013 项零断链、Wiki Link 零问题；全仓仍有原有 101 条 Wiki Link 及 38 条 frontmatter 引用问题。
