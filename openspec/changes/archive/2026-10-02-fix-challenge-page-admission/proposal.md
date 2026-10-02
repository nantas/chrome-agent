# Proposal

## 问题定义

P-line：抓取进程成功被误当作正文成功。2026-10-02 Darkest Dungeon wiki.gg 探测得到 Cloudflare 验证页，scrapling 适配器仅检查退出码与文件存在，返回 success 并写死 http_status=200；探测链立即停止。后置 protection_identifier 虽识别 cloudflare-managed，结构分析已经把 Just a moment 当成导航，后续仍生成草稿，CLI 描述 deep discovery completed 并建议 freeze。

本地真实 HTML 离线回放（仅模拟引擎退出 0）已证明真实适配器和 probe 链放行挑战页，fallback 调用 0 次。指定 handoff 本身只证明 strategy_gap，不作为挑战页的单独证据。

## 范围边界

- 统一原始 HTML 内容准入；拒绝挑战页、空或不可读结果；记录真实 HTTP 元数据及结构化判定证据。
- probe 每次成功候选先校验，再选择 success_engine；失败继续既有引擎链，全部失败停止结构分析、草稿生成和自动样本工作。
- 样本、fetch/crawl HTML 获取及生产缓存消费复用准入；受阻内容仅作诊断，不能产出成功正文或通过 resume。
- CLI 区分内容受阻与内部故障；成功/部分成功必须有可用内容依据，失败不推荐 freeze。
- 兼容正常正文提及 Cloudflare、普通 Turnstile 组件，不以关键字、大小或 403 单独判为挑战页。
- 不增加验证码绕过方式，不改变浏览器授权与 Crawl Gate，不升级引擎，不冻结/发布本站策略，不迁移或删除旧证据。
- HTML 受阻后独立 API 发现/恢复、全站质量评分与任意登录墙识别扩展不在本次范围。

## Capabilities

### New Capabilities
- `fetch-content-admission`: 对获取及复用的 HTML 统一判断是否可作为正文消费，保留拒绝原因与证据，并覆盖多入口等价行为。

### Modified Capabilities
- `explore`: 将内容准入接入引擎选择、下游停止条件与 CLI 输出，防止挑战页产生成功探测或可冻结建议。

## Capabilities 待确认项

- 2026-10-02 用户在收到完整方案后调用 openspec-propose 要求创建 change；以上能力为该范围的规范拆分，无新增产品范围或阻塞确认项。
- fetch-content-admission 属 A=fetch、B=shared、C=generic、D=html_generic/html_mediawiki；不是新增引擎或站点特例。

## Impact

涉及 scripts/lib 共享判定、explore probe/main/protection/sample、Node CLI 的 HTML 获取及结果汇总、生产 HTML 缓存消费边界；具体接线见 design。新增 unittest/node:test 回归，无第三方测试依赖。CLI 的虚假 200 改为真实值或 null；无有效内容的 Explore 由 partial_success 降为 failure，这是有意修正。新增模块执行 C11，CLI 修改执行 C10。已有有效页面转换、选择器配置与缓存身份规则应保持不变。

## 关联绑定

- 关联 binding: `binding.md`。
- 标准、项目页面和回写目标沿用 binding 中引用；归档新增 fetch-content-admission 规范并合并既有 Explore 聚合规范，不创建重复真源。
