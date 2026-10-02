# Proposal

## 问题定义

上一 change 已修复 Explore 导入路径并归档提交为 777d5b1。原始目标 `https://darkestdungeon.wiki.gg/wiki/Darkest_Dungeon_Wiki_1` 随后抵达 scaffold 生成，但在 `strategy_scaffold_generator.py:210` 因 extraction.cleanup 中的 `strip_edit_sections`、`strip_toc` 被 schema 拒绝而失败；本次为独立 P-line 问题。

根因是 extraction 契约收紧后配置生产端迁移不完整：提交 d10858db 增加 schema/生成阶段准入并迁移 Fandom 模板，但 generic MediaWiki 和 wiki.gg 模板仍使用没有共享内核实现的旧 cleanup 名称。模板直接校验也失败，因此不是网络、注册漏项或 scaffold 合并改变了配置。

诊断反馈环：`python3 outputs/debug/20261002-scaffold-schema/repro.py -v`，真实 generate()、临时仓库、无网络，两个模板稳定失败，约 28ms。临时副本中替换编辑链接操作并用 selectors 移除 TOC 后，三个 MediaWiki 模板均可生成；真实预处理删除 EDIT/TOC 且保留 KEEP。生产文件未改。

扩大生产端审计后发现：iterate 会再次添加 strip_edit_sections、strip_toc、fix_lazyload_images；auto_remediate 的 11 个 cleanup 映射中有 8 个不被 schema 接受。旧测试只锁定映射字符串，没有约束输出可准入或实际清理效果。仅修模板会将下一次失败推迟到反馈迭代/自动修复。

## 范围边界

纳入三个配置生产路径：

1. **模板**：generic MediaWiki、wiki.gg 将 strip_edit_sections 改为已有 strip_edit_links；移除 strip_toc 操作，TOC 使用 .toc/#toc 的 cleanup_selectors，保留 wiki.gg 已有其它 selectors 与图片规则；Fandom 作为合法控制样本。
2. **用户反馈 iterate**：编辑链接反馈使用已有操作，TOC 反馈合并 selectors；图片修复使用已有 unwrap_image_wrappers 与结构化 lazyload。仅在已有配置或样本证据足以定位 placeholder_pattern/real_src_attr 时更新 lazyload；否则记录未处理原因。修改候选配置先校验，再覆盖文件/开始转换；非法候选失败时原文件逐字节保持不变，禁止启动转换。
3. **自动修复**：只产生消费者已支持的操作/字段。对需要缺失参数或没有实现的修复保留自检问题，给出可审计原因并交给现有 KI 生命周期，不能用虚构 cleanup 名称假装修复。支持的批量修复仍保留，重检决定问题是否解决；合法不等于有效。
4. **防回归**：所有注册 MediaWiki 模板的 schema 与真实生成测试；编辑/TOC/lazyload 的实际效果测试；自动修复所有已知 fixable_type 输出准入与 unsupported 报告测试；iterate 校验失败保留原文件、停止转换测试。

非目标：放宽 schema、补注册无实现操作、网站特有策略创建、实现八项新清理能力、改引擎/抓取范围、重做平台识别和 API profile 推导、重构共享 converter、自动冻结或进入 extraction。非 MediaWiki 的描述性 extraction 规则保持其现有适用边界，不套用 MediaWiki schema。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `explore-scaffold`: 使模板生成、反馈迭代与样本自动修复只发布可准入且有消费者的 extraction 配置，并保留无法执行的修复问题及原因。

## Capabilities 待确认项

- [x] 2026-10-02 用户回复“确认”，已有 explore-scaffold 为本次唯一能力修改项。现有 template-content/auto-remediation-extended/ki-lifecycle-consumption 要求位于 merged spec `openspec/specs/explore/explore-scaffold.md`；本 change 输出 `specs/explore-scaffold/spec.md`，归档按真实 requirement 定位合并，保留独立的样本推荐要求。

## Impact

- 修改候选：`sites/templates/mediawiki.yaml`、`sites/templates/mediawiki-wiki-gg.yaml`、`scripts/explore/iterate.py`、`scripts/explore/self_check.py`；若 unresolved 结果需要传播，main.py 仅做薄层消费接线。
- 合约兼容：auto_remediate 当前返回 extraction dict，不能把报告元数据塞进 extraction；保留现有调用的返回契约，另提供可定位的修复计划/未处理原因，由调用方消费。保持输入不变、批量输出确定性和合法已有规则。
- schema/capability registry 与共享预处理器继续作为准入/消费真源；优先复用现有实现，不新增 cleanup aliases 或能力模块。
- Python 3.9+、unittest、tests 顶层、vertical slice TDD；修改自检测试的字符串映射断言为准入/消费者效果断言。CLI/runtime/skill 预期不修改。
- 验收：离线反馈环由 RED 转 GREEN；所有注册 MediaWiki 模板可生成合法草稿；自动修复不再注入未知操作；iterate 非法更新不落盘、不转换；Python/Node 回归与 doctor capabilities 通过；原命令仍在既有 Gate 下验证，独立后续故障如实记录。
- 已有生产策略不自动批量迁移；已有非法草稿应明确拒绝并报告字段错误，不静默删除未知规则。

## 关联绑定

- 关联 binding：`binding.md`；标准、项目页和回写目标依该文件。
- 关联已归档 change：`openspec/changes/archive/2026-10-02-fix-explore-startup-and-handoff-naming/verification.md`。
- 本阶段创建提案，不修改生产代码或执行网站工作流。
