# Proposal

## 问题定义

MediaWiki discovery 移到 explore 后没有公共调用者，crawl 仍向 pipeline 传已删除的 discover 阶段：新 run 缺 manifest 返回 20，旧 run 可无操作假成功。错误又降级到不支持 discovery-only/API manifest 的 Scrapling 抓取。allpages 清单遗漏列表页标记，并把未分类 ns0 页留在根目录。另有旧 cleanup 形状被局部校验跳过、完整 Gate 崩溃，模板名称过期；bootstrap 继承站点语义并立即注册，容易把未验证草稿用于生产。

## 范围边界

两组修复共同恢复用户可验证的端到端契约：

1. 复用已冻结策略，在 explore 枚举页面，公共 crawl 产出准确 manifest/summary 后停止等待确认；pipeline 只消费 manifest。补齐列表页资格、索引与 Misc 规则，分类错误和 fallback，不改变请求语义。
2. 统一 extraction 配置形状/名称验证，迁移 Fandom 模板及 Neon Abyss 旧配置，bootstrap 白名单继承平台机制、重新验证站点身份，freeze/registry 阻止草稿生产使用。

非目标：不恢复 pipeline discover；不把 manifest 塞进 frontmatter；不对已有策略重跑完整站点测绘；不迁移历史 manifest/Markdown/digest，不重抓旧 515 页，不回灌 my-wiki，不执行本次 1596 页抽取。1596 仅为诊断样本规模，不是线上固定规模或最终 Markdown 数量验收。本轮仅规划，不实施。

## Capabilities

### New Capabilities

无新增业务能力；新增入口复用已有 discover 内核，不重复注册镜像。

### Modified Capabilities

- `discover-kernel`: 接通已冻结策略页面发现、版本化清单/列表资格/Misc/真实 summary，并保持 pipeline manifest-only。
- `cli`: 修正公共 crawl 分阶段调用、确认门、manifest兼容边界与保留语义的错误输出和降级。
- `explore-architecture-gate`: 按共享内核验证 extraction 形状和名称，结构化失败代替静默跳过或崩溃。
- `strategy`: 迁移旧 extraction 配置并升级 bootstrap、freeze、registry 的平台继承及生产资格契约。

## Capabilities 待确认项

无阻塞项：用户已授权上述两组目标。`cli` 与 `strategy` 为仓库已合并能力目录；delta 内记录具体既有文件与 requirement 映射，归档写回原文件，避免平行真源。

## Impact

涉及 `scripts/chrome-agent-cli.mjs`、`scripts/explore/`、pipeline 参数/清单消费/assemble、共享 extraction 校验、Fandom 模板、Neon Abyss 策略与 registry/scaffold 生命周期。行为变化包括：无效配置不再自动降级；不完整清单明确拒绝；草稿不被生产匹配；未分类 ns0 新清单进入 Misc。需公共CLI离线回归、Python unittest/Node node:test、站点样本、能力检查、C10全局同步和架构/spec回写。既有用户站点改动不得覆盖。

## 关联绑定

- 关联 binding: `binding.md`。
- 已确认标准页 / 项目页 / 回写目标：按 binding 中本仓治理与架构/spec清单执行；本轮无外部系统写入。
