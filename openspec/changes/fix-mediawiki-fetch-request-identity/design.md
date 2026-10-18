# 实现设计

CLI 解析并验证请求意图后，仍经应用层 Python 与共享 ApiClient 获取。显式 `/api.php` 或 `/w/api.php` 只允许 action=parse、单页 page 或 oldid、text/revid 与 JSON。端点来自请求自身同源路径；策略页面来自已有 api.base_url 且校验同源。

history 调用 query(prop=revisions)，默认最多 50 条，返回 ids/timestamp/comment/size，不请求 user，不自动续页。rvcontinue 只用于当前固定标题。oldid 调用 query(action=parse, oldid=...)，验证真实响应 revid 等于请求且页面标题匹配；不能携带 page 与 oldid 互斥参数。

HTML 保留 text['*'] 原文并通过共享正文准入；JSON 保留完整解析后的 API 载荷（不是 HTTP 原始字节）。manifest.mediawiki 给出真实 title/pageid/revid、响应文件路径和请求参数。未知动作/参数、缺失身份、空正文、版本不符都失败，不 fallback 当前页。

普通策略 fetch 保持既有输出路径；显式 API / oldid 用 content.html，history 用 history.json。测试隔离 ApiClient 网络边界，执行真实 Python bridge 与 Node 编排。
