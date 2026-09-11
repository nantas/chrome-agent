# Design

## Context

行为依据：`specs/discover-kernel/spec.md`、`specs/cli/spec.md`、`specs/explore-architecture-gate/spec.md`、`specs/strategy/spec.md`。现状证据是 CLI 仍传 discover、pipeline仅载入manifest、两个explore枚举函数无公共调用者；allpages缺is_list_page；完整Gate遇dict cleanup抛TypeError。源码消费者位于共享库，不能凭旧pipeline目录检索判断操作是否存在。

## Goals / Non-Goals

**Goals:** 恢复发现、确认、抽取链路；清单与索引一致；错误可定位；配置在副作用前验证；草稿不被误用于生产。

**Non-Goals:** 不恢复pipeline发现，不重做已知站点测绘，不在frontmatter保存清单，不迁移历史manifest/Markdown/digest，不回灌my-wiki，不重抓515页或1596页；不把样本页数作为线上不变式。本轮仅产规划。

## Decisions

### 1. Explore owns enumeration; public CLI owns workflow

实现 explore 下的薄页面发现入口，输入 frozen strategy、run_dir、显式scope选项，输出统一发现结果。复用 allpages/homepage 内核及共享ApiClient，不复跑 `explore/main.py` 的probe/structure/scaffold/sample全链。公共 `crawl --discovery-only` 和 `--phase discover` 调此入口；默认all缺清单时先发现并停在确认门；只有完整成功且明确--yes才允许续跑，discovery-only即使--yes也始终停止。partial_success不自动抽取；调用方明确接受部分范围后以--from-manifest恢复。

pipeline入口保留 `python3 -m scripts.pipeline`，参数仅fetch/convert/assemble/all，清单/阶段校验前置到API probe之前。禁止把兼容discover委派回pipeline。CLI与pipeline共享清单校验语义；声明新文件时更新已有discover能力归属，不另注册独立同坐标内核或把CLI镜像注册为第二发现实现。

### 2. One manifest contract drives summary and assembly

新清单使用schema_version=2、domain、策略语义指纹、pages及list-page decisions；指纹覆盖影响范围/分类/输出语义的frontmatter，忽略叙述正文和序列化格式。page保留title/ns/pageid/categories/target_directory/target_filename，增加明确is_list_page及列表目标信息。同身份去重、同路径冲突报错。

枚举时解析配置列表页的规范身份，按同一redirect/scope/exclude规则决定纳入；真实列表内容存在不等于获准纳入。范围外、排除、缺失或身份不明记录skip reason，不把孤立list_page_content变成额外页面。assembly仅消费纳入且标记的列表页，生成真实index并保持链接可达；其他有实体目录生成普通成员index。summary使用相同资格判断。新生成ns0页仅在未分类且原target_dir为空时用Misc，其他namespace和StS前缀原样保留。

summary目录计数从最终清单聚合，过滤/失败数来自内核返回的实际计数，不从日志猜测；未知使用null+reason。估时带测量/模型依据，不写伪实测常数；失败率明确分母。全失败不产可抽取success清单。artifact引用相对summary目录，交接可移植。不是每个输入页必对应一个最终md：真实列表替换、自动索引与说明文件均需分别计数。

### 3. Legacy input compatibility never migrates historical artifacts

缺schema_version才进入legacy adapter；显式非2版本一律unsupported-version拒绝。无版本清单满足title/ns/目标路径最低契约时可内存兼容：精确命中配置列表标题且目标目录一致，才补is_list_page=true；无任何列表标题匹配则false。别名/目录冲突/缺核心字段拒绝并定位字段，不猜测。孤立list_page_content明确skip；不增页面。保留旧目标路径，包括根目录空字符串；此次Misc仅约束新发现，绝不借兼容自动搬37页。输入文件字节不改，不自动重发现。v2缺必要字段/domain或语义指纹不符明确拒绝，提供重新确认策略/清单的建议而不代替用户执行。

### 4. Errors retain the original contract

建立MediaWiki subprocess结果分类：0成功、1显式部分成功、配置/参数/内部错误、外部网络错误、spawn/timeout/signal失败。status=null不能当1。内部错误统一复用internalFailure/handoff，记录上游exit/error/stderr摘要、mode、fallback reason；不要再次实现错误信封。外部失败仅在后端可保持discoveryOnly或manifest页面/路径语义时允许降级；现有Scrapling的visited模式不兼容API pages，故这些请求默认停止。任何后端都不能把发现命令降成正文爬取。

### 5. Validate configuration before inspecting or executing it

在共享提取层维护实际操作与支持schema的权威声明，Gate/策略写入和生产消费共同使用；cleanup支持集合与capability-registry交叉检查，避免第二份手写列表。首先验证形状和名称（cleanup、text_normalization、lazyload及被治理nested fields），再做consumer/audit；错误返回field_path/type/value/expected，不继续set(dict)或regex误判。支持共享consumer即覆盖所有薄编排路径，不要求重复实现。

Fandom模板和neon配置按实际消费者迁移：lazyload专用map、strip_edit_links/cleanup_selectors、合法normalizer，删除extraction.pipeline等已确认无效字段。不能机械把dict keys转字符串；edit/TOC默认已清理、wiki link有内核默认行为，回归应验证实际输出而非操作名出现次数。

### 6. Bootstrap emits a draft; freeze establishes production eligibility

平台继承白名单仅含已验证platform/variant/profile IDs、rate-limit、protection/engine refs与平台级提取默认。新domain/API base_url/image base_url来自目标；来源游戏名/版本/页面pattern/label/example/entry_points/taxonomy/特定handler不作为目标事实复制。缺站点身份保存在草稿待验证metadata；通用模板模式可带来源引用，不伪称已验证。bootstrap失败不写生产registry；成功也只报告draft和缺项。

freeze统一验证schema、目标identity/entry points、能力引用、审核证据，再以可回滚发布过程更新策略与registry；失败保留原文件和draft marker，避免当前先去marker再验证。lookup要求registry登记、schema通过且非draft；缺registry或仅移除marker不构成生产资格，新draft metadata保持到freeze成功。lookup排除所有显式draft/Bootstrapped/scaffold标记。历史无标记冻结策略可在当前schema通过后继续用，不强制重做站点分析；re-freeze也不得跳过验证。这升级现行 `字段适配规则` 的verbatim/url_pattern继承与 `Registry 索引更新` 的立即注册契约，按delta回填原合并文件。

## Risks / Migration

- 更严格schema会暴露其他旧策略问题：实施先库存审计并列出受影响域名，必须修此次模板/neon直接覆盖字段，其他问题明确报告，不静默兼容未知op。保留用户未提交站点变更。
- 草稿资格限制可能让历史bootstrap暂不能生产：结果需列出可修字段，不能自动freeze或复制虚假审核证据。
- 首页/allpages列表身份、排除和redirect交互需离线fixture覆盖；未知页面规模与平台实时行为不以历史1596作为断言。
- regression以公共CLI子进程stub、真实共享枚举/装配为主，禁止测试夹具依赖公网或用户会话。站点样本使用项目runner，缺样本记录阻塞而非造通过。
- 归档按各delta的精确文件映射回填cli-workflows、strategy-schema/lifecycle，移除派生文档中pipeline discover旧表述。后续C10手动同步runtime/skill并将installed-hash置当前HEAD（不把cli文件复制成runtime），C11 doctor --check capabilities通过。

### Implementation inventory clarification

Schema enforcement follows actual MediaWiki shared consumers. Five non-MediaWiki sites retain narrative rules. Four additional MediaWiki strategies remove unsupported inert op declarations with equivalence tests. Site samples now consume strategy configuration and MediaWiki caches; five bounded single-page API samples plus one existing cache replace the initial zero-sample gap. Canonical list aliases/redirects resolve only to retained identities; unresolved or excluded titles never create pages.
