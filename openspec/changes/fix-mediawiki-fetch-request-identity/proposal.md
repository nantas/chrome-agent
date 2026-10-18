# 修复 MediaWiki 请求身份

当前 fetch 忽略 URL 查询参数，使 history 与 oldid 静默返回当前正文；无策略的显式 API URL 又会将 JSON 当网页转换。修复三种单页入口：受限显式 parse URL、指定修订 HTML、有界历史元数据。保留原请求 URL、服务端真实页面/修订身份与完整 API 响应，不增加 HTTP 客户端、自动分页或站点遍历。
