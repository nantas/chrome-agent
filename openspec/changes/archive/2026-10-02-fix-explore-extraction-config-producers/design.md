# Design

## Context

依据 `specs/explore-scaffold/spec.md` 的 template-content、auto-remediation-extended、ki-lifecycle-consumption 与 feedback-extraction-admission-before-write。现有消费者已支持 strip_edit_links、cleanup_selectors 和结构化 lazyload；旧模板、iterate 和 self_check 仍生产不支持的字符串操作。

实际 schema 准入适用于 MediaWiki。非 MediaWiki 的描述性规则不因本变更被施加同一 cleanup 枚举。已有 schema 对未知规则的拒绝行为不变。

## Goals / Non-Goals

**Goals:** 三条生产路径输出可准入配置；真实消费者验证清理效果；更新落盘前校验；不支持的修复保留问题与原因；无有效更新时结束重试。

**Non-Goals:** 不实现缺失的八项能力，不注册 cleanup aliases，不降低 schema 严格度，不批量修改既有策略，不自动冻结/扩大抓取，不改平台识别、引擎、API profile 推导或共享 converter。

## Decisions

### 1. 模板迁移复用已有消费者

两个旧模板的 cleanup 使用 strip_edit_links，TOC 清理走 cleanup_selectors。generic 增加 .toc/#toc；wiki.gg 保留现有 selectors 和图片过滤，删除无实现 strip_toc。Fandom 模板与 registry 遍历用作防遗漏控制。测试同时验证 schema、真实 generate、共享 preprocess_html 的正文/编辑/TOC 效果，不仅断言配置字符串。

### 2. 分离配置计划与修复诊断

优先在现有 self_check.py 提供规划函数，避免新能力模块：输入合法规则、请求动作和可选证据上下文；输出 `{extraction, applied, unresolved, changed}`。所有规则由深拷贝产生；applied 表示动作已写入可执行候选，不表示质量问题已解决。unresolved 项携带原始 issue/fixable_type、reason_code 与 detail，保留可交给 KI 的 failure 身份。

auto_remediate 保留原 extraction dict 返回契约，委托同一规划实现，兼容仅取配置的调用方。main.py 与 iterate 需要诊断时直接消费规划结果；不能把报告字段塞入 extraction。若合法已有配置包含非目标字段，保留这些字段，不能为让 schema 通过静默删改已有非法规则。

原因码建议固定为 unsupported_consumer、missing_evidence、invalid_configuration；候选非法时结构化返回字段错误并停止消费，不对已输入的非法 MediaWiki 配置作自动“清洗”。

### 3. 有消费者的动作与需保留的问题

| 请求 | 可执行配置 | 无法执行时 |
| --- | --- | --- |
| edit feedback | cleanup 添加 strip_edit_links | 已有非法配置按准入失败处理 |
| TOC feedback | cleanup_selectors 并入 .toc/#toc | 不添加 strip_toc，不通过广泛元素删除规避问题 |
| image_wrapper / link_resolution | cleanup 添加 unwrap_image_wrappers（仅已定义的 wrapper 清理语义） | 链接解析仍不通过时保留失败，不宣称该规则能修复任意 URL |
| table_class_missing | cleanup 添加 strip_fandom_infobox_tables | 后续质量重检决定是否修复 |
| space_normalization | text_normalization 添加 fix_spaces | 重检决定质量状态 |
| base64/lazyload | lazyload.enabled + 已有完整配置或显式证据给出的 placeholder_pattern/real_src_attr | 缺证据则 missing_evidence，保留已有合法规则，不猜 data-src |
| relative image/link、infobox residue、section loss、nav leak、YouTube title、ID navigation leak | 本 change 不新增对应 cleanup | unsupported_consumer，保留原失败交给 KI |

证据上下文如需要参数扩展应可选且显式。最低支持完整已有 lazyload 配置；没有证据时允许无法自动修复。iterate 的普通 image 反馈可先应用既有 wrapper 操作，同时单独报告 lazyload 不足。

### 4. 写入与重试边界

iterate 先 parse 原文件、生成候选、基于其平台边界执行准入，成功后才改写 frontmatter/调用转换。失败返回 ok=false 和 schema 字段诊断；文件字节不变，convert 调用次数为 0。回写只替换当前 frontmatter，不丢失正文与身份字段。非 MediaWiki 保留现有描述性规则适用边界。

main.py 的自动修复循环消费 changed/applied/unresolved；无实际配置变化时直接结束循环并显示 unresolved，不浪费重转换次数。合法更新重转换并重检，保留既有次数上限与 Gate。诊断字段进入报告，原 self-check failures 不因规划而被标记 resolved，交由已有 KI 分类。

### 5. 回归测试 seam

- 模板 registry 驱动的全集参数化 unittest：真实临时目录生成，不发布策略；schema/consumer 效果均覆盖。
- 规划/auto_remediate：枚举全部既有 fixable_type，断言准入、支持或 unresolved 的实际结果，深拷贝与排序/去重；现有虚构字符串映射测试改为行为测试。
- iterate：临时策略文件 + mock 仅隔离网络 convert，检查落盘 round-trip、实际 preprocess_html、非法配置字节不变/convert 未调用及非 MediaWiki 边界。
- main 循环：控制转换/自检结果，不替换规划器/schema；确认 unsupported-only 不重试、合法 changed 更新会重检且报告未处理原因。

## Risks / Migration

- 过去列为 fixable 的问题会被识别为当前无法自动修复，用户应看到原因而不是静默 success。兼容旧 auto_remediate 返回值，新的诊断由现有报告入口输出。
- 只保证拟更新配置合法；不保证所有既有 self-check 问题已经解决。质量状态仍由消费者输出重检决定。
- 已有非法 MediaWiki 草稿拒绝更新，保留文件并报告，不自动迁移历史策略。模板生成只输出 draft，不改 registry 生产资格。
- 不新增模块时无需能力注册扩展；若实施确有必要新增，应先更新设计/注册/tests，并保持 C11 检查通过。
- 原始 URL 可能在消除本错误后暴露其它故障；独立记录，不能以本次测试通过代替网站成功。回滚范围为模板规则与 producer/调用方的规划接线。
