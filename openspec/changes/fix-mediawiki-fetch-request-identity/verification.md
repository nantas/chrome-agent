# 验证

测试先于实现，三个垂直切片分别观察到红灯：显式 API 缺 strategy、history 被拒绝、oldid 未支持。实现后通过。后续边界用例揭示空 action 未在网络前拒绝，修复后转绿。

`node --test tests/mediawiki-fetch-identity.test.mjs tests/fetch-strategy-selector.test.mjs tests/content-admission-fetch.test.mjs tests/mediawiki-crawl.test.mjs tests/chrome-agent-runtime.test.mjs`：45/45 通过。新增 10 项覆盖真实 Python bridge（仅 ApiClient 网络边界模拟）、Node fetch 编排与落盘 artifact/manifest、完整 API 载荷、源 HTML、真实响应身份、共享准入拒绝、默认历史上限与固定页续页、旧版/错页拒绝、非法组合请求前拒绝、普通输出与子页标题。

`node --check scripts/chrome-agent-cli.mjs` 通过。C10 runtime/skill 源与全局副本相同，重复制并刷新 installed-hash；`chrome-agent doctor --format json` 为 success，dispatch_allowed=true。实现阶段未修改共享 ApiClient、不请求线上历史数据、不接管浏览器、不修改策略，也未提交或推送。

2026-10-19提交前复核：上述45项相关测试再次通过，语法与`git diff --check`通过。本次测试中的既有runtime doctor可能执行仓库freshness的git fetch；未发起页面采集或浏览器调用。用户现已明确授权整理提交，提交后刷新C10安装记录，推送不在本轮范围。

覆盖为本地受控响应；真实站点可用性与历史内容判断由调用方的定向获取核验。未运行全量转换/站点样本，因为转换、站点配置和 API 内核未变；该 change 尚未归档。
