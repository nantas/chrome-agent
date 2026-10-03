# Proposal

## 问题定义

DD2 handoff 的 P-1～P-4 已离线复现。Crawl 已传入匹配策略，但 CloakBrowser 的本地 Markdown 转换丢失 selector；Scrapling 即使收到 selector，也不消费完整 extraction、不调用共享内核，技能表仍出现 600 列。S1 将全页图片与正文 Markdown 比较，六样本均多算 11 张皮肤图；S9 将连续 Items 正文误判导航且漏报真实登录导航；S5 将源文已有的 of of / over over 判为转换错误。

本次诊断运行真实 CLI 转换函数和真实本地 Scrapling，仅替换远端获取边界；最小 fixture 均稳定复现。共享内核重放六份 DD2 HTML，去除基线外层标题/来源及末尾换行后正文一致，正文 S1 和表格断言通过；站点 13/13 回归通过。诊断脚本在 outputs/debug-dd2-diagnosis，仅作本机证据，正式测试不得依赖它们。

## 范围边界

一个 change 修复全部四项：crawl 各 HTML 转换分支使用已匹配策略的共享内核；建立 S1/S9/S5 的来源证据契约并接入 explore main/iterate。已匹配策略转换失败时明确失败，不降级通用转换；保持获取阶段既有 fallback 与正文准入。

包括普通遍历、sitemap manifest、预取/并行输入及缓存 convert；复用已匹配策略，不重新匹配域名。无策略通用路线保持兼容。缺失 extraction 的已匹配策略以空规则走内核，非法 extraction 明确失败。

不改变发现、确认 Gate、采集范围、引擎安装/选择、站点内容或其他 active change；不自动重抓 DD2；不推广修改独立 fetch/scrape 命令的转换语义。此阶段仅创建可实施 artifacts。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `convert`: 增加 crawl HTML 镜像的共享内核委托、跨分支等价及失败不降级契约。
- `fetch-strategy-selector`: 将已匹配策略的 crawl 从旧 Scrapling selector-only 契约迁移到共享内核，保留独立 fetch 和无策略通用路线。
- `explore-workflow`: 明确自检来源范围、基于来源的导航判断及重复文本归因，并保持自动修复与汇总兼容。

## Capabilities 待确认项

- [x] 用户已确认四项修复合并及失败不降级；上述归属为既有 convert、selector 路由和 explore 自检职责，不新增业务范围。

## Impact

- CLI 的 convertTraversalToMarkdown、sitemap extraction 及 scripts/lib/crawl_scrapling.mjs：统一已获取 HTML 到共享内核的边界，保留 URL/输出上下文和成功失败身份。
- 应用层 Python bridge：加载/校验传入规则、调用 convert_page_full；Node 使用 resolveAppPython 和结构化参数，不在引擎 venv 运行应用代码。
- scripts/explore/self_check.py、main.py、iterate.py：新增显式审计上下文；不以转换后清理结果替代原始来源证据。
- tests/ 增加 node:test/unittest 的真实编排与来源反例，保留现有站点 13 样本回归。
- 能力注册和镜像等价证明同步；CLI 修改触发 C10。依赖现有共享内核，不引入第三方测试依赖。
- 与 fix-wiki-table-sample-integrity 的关系：消费当前已实现的表格内核，不重复修改其 artifacts 或表格算法。

## 关联绑定

关联 `binding.md`；标准引用、五份 architecture 项目页及 CONTEXT-MAP 回写目标遵循 binding。行为真源为本 change delta specs。
