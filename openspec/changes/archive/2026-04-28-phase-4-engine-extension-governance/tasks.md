# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `engine-registry` spec 覆盖：注册格式（JSON 结构、9 个必填字段）、三维特性评分（efficiency/stability/adaptability + note）、`composite_score` 加权公式（adaptability×0.50 + stability×0.30 + efficiency×0.20）、`default_rank` 推导规则（Scrapling-first 强制覆盖）、引擎生命周期（draft/frozen/superseded）、标识符约定（kebab-case、避免冲突）、与 engine-contracts 及策略 schemas 的集成规则
- [x] 1.2 确认 `extension-api` spec 覆盖：6 项 artifact checklist（contract spec + registry entry + engine-contracts 更新 + strategy 集成 + 决策记录 + smoke-check evidence）、contract spec 模板（含 `{{ }}` 占位符）、引擎命名规范（`<tool-prefix>-<capability>` pattern）、自定义要求（draft→frozen 条件）、接入治理规则（opensec change 强制）
- [x] 1.3 确认 `scrapling-bulk-fetch-contract` spec 覆盖：input contract（urls 数组、extraction_type/css_selector/main_content_only、session_id 复用、browser 参数）、output contract（per-URL status/content[0]/url）、error contract（timeout/network/browser crash/block/parse）、smoke-check（example.com + httpbin.org 双 URL）
- [x] 1.4 确认 `engine-contracts` MODIFIED spec：删除内联 engine 注册表 → 引用 `configs/engine-registry.json`、更新选择映射（引用 engine-preferences + engine_priority + default_rank）、更新错误矩阵（新增 scrapling-bulk-fetch 列）、更新 smoke-check 清单（新增 scrapling-bulk-fetch 行）、移除 compliance status 子 scenario
- [x] 1.5 确认 `anti-crawl-schema` MODIFIED spec：RENAMED engine_sequence → engine_priority、REMOVED purpose 字段、ADDED rank 字段（连续整数，至少 1 个）、更新 default 策略的 engine_priority 表述
- [x] 1.6 确认 `site-strategy-schema` MODIFIED spec：ADDED engine_preference 字段（optional, file-level 和 per-page level）、更新 frontmatter 必填字段表、更新 structure.pages[] 字段表

## 2. 注册索引与模板

- [x] 2.1 创建 `configs/engine-registry.json`：包含 6 个 engine 条目（scrapling-get、scrapling-fetch、scrapling-stealthy-fetch、scrapling-bulk-fetch、chrome-devtools-mcp、chrome-cdp），每个条目含 id/type/characteristics（3 维 + note）/composite_score/default_rank/best_for/contract_spec/status 全部 9 个字段
- [x] 2.2 为 scrapling-get 设置：efficiency: 0.95, stability: 0.90, adaptability: 0.30, composite_score: 61, default_rank: 1, best_for: ["static_page", "static_article"]
- [x] 2.3 为 scrapling-fetch 设置：efficiency: 0.60, stability: 0.80, adaptability: 0.60, composite_score: 66, default_rank: 2, best_for: ["dynamic_content", "dynamic_list", "search_results"]
- [x] 2.4 为 scrapling-stealthy-fetch 设置：efficiency: 0.40, stability: 0.85, adaptability: 0.90, composite_score: 79, default_rank: 3, best_for: ["high_protection"]
- [x] 2.5 为 scrapling-bulk-fetch 设置：efficiency: 0.55, stability: 0.75, adaptability: 0.55, composite_score: 62, default_rank: 3 (与 stealthy-fetch 同 rank，用于批量场景), best_for: ["bulk_operations"]。实现按主 spec 公式落地为 `61`，见 `verification.md`
- [x] 2.6 为 chrome-devtools-mcp 设置：efficiency: 0.30, stability: 0.70, adaptability: 0.95, composite_score: 81, default_rank: 4, best_for: ["diagnostic"]。实现按主 spec 公式落地为 `75`，见 `verification.md`
- [x] 2.7 为 chrome-cdp 设置：efficiency: 0.20, stability: 0.60, adaptability: 0.85, composite_score: 71, default_rank: 5, best_for: ["authenticated"]。实现按主 spec 公式落地为 `65`，见 `verification.md`
- [x] 2.8 创建 `openspec/specs/extension-api/contract-template.md`：基于 `extension-api` spec 中定义的模板，包含 `{{ }}` 占位符的完整 contract spec 骨架
- [x] 2.9 创建 `openspec/specs/scrapling-bulk-fetch-contract/spec.md`：将 delta spec 写入正式位置（本 change 的 spec 文件当前在 `specs/scrapling-bulk-fetch-contract/spec.md`，需同步到 `openspec/specs/scrapling-bulk-fetch-contract/spec.md`）
- [x] 2.10 创建 `openspec/specs/engine-registry/spec.md`：将 delta spec 写入正式位置
- [x] 2.11 创建 `openspec/specs/extension-api/spec.md`：将 delta spec 写入正式位置

## 3. 策略文件迁移（engine_sequence → engine_priority）

- [x] 3.1 迁移 `sites/anti-crawl/default.md`：`engine_sequence` → `engine_priority`，为每个 entry 添加 `rank`（1-4），删除 `purpose` 字段，保持 `engine` 不变
- [x] 3.2 迁移 `sites/anti-crawl/cloudflare-turnstile.md`：stealthy-fetch rank: 1, chrome-devtools-mcp rank: 2
- [x] 3.3 迁移 `sites/anti-crawl/login-wall-redirect.md`：scrapling-fetch rank: 1, chrome-devtools-mcp rank: 2
- [x] 3.4 迁移 `sites/anti-crawl/cookie-auth-session.md`：chrome-cdp rank: 1
- [x] 3.5 迁移 `sites/anti-crawl/rate-limit-api.md`：scrapling-fetch rank: 1, chrome-devtools-mcp rank: 2
- [x] 3.6 更新 `sites/anti-crawl/registry.json`：将 `primary_engine` 字段值更新为每个策略 rank: 1 的引擎（已符合，但需验证一致性）

## 4. Spec 主文件更新

- [x] 4.1 更新 `openspec/specs/engine-contracts/spec.md`：合并 MODIFIED delta——删除内联 engine 注册表（替换为 engine-registry 引用）、更新选择映射（三步优先级链）、更新错误矩阵（新增 scrapling-bulk-fetch 列）、更新 smoke-check 清单、移除 compliance status 子 scenario、保留其他所有 requirement 不变
- [x] 4.2 更新 `openspec/specs/anti-crawl-schema/spec.md`：合并 MODIFIED delta——RENAMED engine_sequence → engine_priority（含 rank 字段定义）、REMOVED purpose 相关 scenario、更新 default 策略表述、保留其他所有 requirement（目录结构、必填字段、protection_type 词汇表、detection、success/failure signals、body 章节、registry.json、治理约束）不变
- [x] 4.3 更新 `openspec/specs/site-strategy-schema/spec.md`：合并 MODIFIED delta——ADDED engine_preference requirement（file-level + per-page，optional，引用 engine-registry）、更新 frontmatter 必填字段表（新增 engine_preference 行）、更新 structure.pages[] 字段表（新增 engine_preference 行）、保留其他所有 requirement 不变

## 5. 文档更新

- [x] 5.1 更新 `AGENTS.md`：在能力框架表格中将 `engine-registry` 状态从"未实现"改为"已规范"；在策略库治理章节之后、参考索引之前新增"引擎扩展治理"章节（引用 engine-registry、extension-api、engine-contracts specs，明确新引擎必须通过 openspec change 接入，engine-registry.json 必须同步更新）
- [x] 5.2 更新 `docs/governance-and-capability-plan.md`：Phase 4 描述与交付物精确定义对齐，排他边界中增加"不包含策略自动选择、不包含编排层"
- [x] 5.3 创建 `docs/decisions/2026-04-28-engine-registry-design.md`：记录 Phase 4 核心决策——registry 解耦、特性评分公式、default_rank 规则、engine_priority 迁移、engine_preference 字段（参照 design.md 的 8 个 Decision）
- [x] 5.4 更新 `docs/decisions/README.md`：添加新决策记录的索引条目

## 6. 收敛与验证准备

- [x] 6.1 逐文件验证 `configs/engine-registry.json`：6 个条目所有 9 个字段完整，characteristics 三个维度 score + note 齐全，composite_score 按公式计算正确，default_rank 符合 Scrapling-first 规则
- [x] 6.2 逐文件验证 anti-crawl 迁移：5 个文件的 `engine_priority` 字段使用 `rank`（非 `purpose`），rank 值连续从 1 开始，engine 标识符存在于 registry
- [x] 6.3 交叉引用验证：anti-crawl 的 `engine_priority.engine` 和 site-strategy 的 `engine_preference.preferred` 值都在 `configs/engine-registry.json` 的 `id` 列表中
- [x] 6.4 合约模板验证：`openspec/specs/extension-api/contract-template.md` 包含所有 `{{ }}` 占位符，结构与 extension-api spec 定义一致
- [x] 6.5 Spec 完整性验证：3 个新 spec（engine-registry、extension-api、scrapling-bulk-fetch-contract）和 3 个 MODIFIED spec（engine-contracts、anti-crawl-schema、site-strategy-schema）均位于 `openspec/specs/` 正确位置，内容与 delta spec 一致

## 7. 验证与回写收敛

- [x] 7.1 基于实现结果生成或更新 `verification.md`（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 7.2 基于 `verification.md` 结论生成或更新 `writeback.md`（目标、字段映射、前置条件）
- [x] 7.3 执行 `writeback.md` 中定义的回写目标，记录可审计证据（链接、时间、执行人、结果）
