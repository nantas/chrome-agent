## ADDED Requirements

### Requirement: 忠实的单页请求身份
系统 SHALL 保留 requested target 原样，使用共享 ApiClient 获取，记录服务端 page_title/page_id/revision_id 与完整 API 响应路径；SHALL NOT 以请求参数伪造响应身份。

#### Scenario: 显式 API parse
- **WHEN** fetch 收到同源 api.php 的受限单页 action=parse URL
- **THEN** 输出原始 HTML 与完整 API JSON，不进行 Markdown 转换，不探测其他站点或启动 crawl

#### Scenario: 指定修订
- **WHEN** 页面 URL 指定正整数 oldid
- **THEN** 获取该修订整页 HTML 并核对服务端 revid 与页面标题，不符则失败

#### Scenario: 有界历史
- **WHEN** 页面 URL 指定 action=history
- **THEN** 输出默认最多 50 条 revisions 元数据与 continuation，不自动分页、不请求贡献者字段

#### Scenario: 未支持的查询
- **WHEN** action、参数组合或重复参数不在受支持集合内
- **THEN** 请求前明确拒绝，不返回当前正文冒充
