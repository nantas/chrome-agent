# Design

## Context

用户通过 chrome-agent 对 `bindingofisaacrebirth.wiki.gg` 执行首页驱动全站爬取时，遭遇 exit code 11（EXIT_PHASE_A_FAILURE）。根因是三层问题交织：P-line 异常处理不统一（`except RuntimeError` 漏掉 `PageNotFoundError`）、S-line 策略数据错误（`list_pages` 含不存在的 ns=0 页面）、S/W-line 分类排除缺口（无法表达 "排除 Music、Modding、Version History"）。

本 change 通过 P-line→S-line→CLI 三层推进修复，不引入新 capability（5 个 modified）。

## Goals / Non-Goals

**Goals:**
- 统一 discovery/acquisition 策略层异常处理，使 `PageNotFoundError` 被正确降级
- Phase A 的 `fetch_list_pages()` 增加防御性保护，单个 list_page 失败不阻断全流程
- 策略 schema 新增 `api.homepage.exclude_categories` 字段
- Phase 0 集成分类排除过滤
- CLI 新增 `--exclude-category` 参数，与策略字段合并取并集
- 修正 BOI 站点策略的 `taxonomy.list_pages`

**Non-Goals:**
- 不修改 `PageNotFoundError` 的类层次（保持 `Exception` 基类）
- 不修改 Phase A 的全量发现逻辑（仅修复异常处理和防御性保护）
- 不修改 Phase B/C（已有正确的异常处理）
- 不新增 discovery 策略类型

## Decisions

### D1: `except RuntimeError` → `except Exception`（不引入自定义基类）

**Decision**: 将所有策略层的 `except RuntimeError` 改为 `except Exception`，不引入 `RecoverableApiError` 中间基类。

**Rationale**: 引入中间基类需要变更 `PageNotFoundError` 的继承链，增加 API 表面。当前 `client.py` 中仅 `PageNotFoundError` 是 `Exception` 的非 `RuntimeError` 子类，且 future-proof——如果将来新增更多可恢复异常（如 `ApiRateLimitError`），它们也应被 `except Exception` 覆盖。保持简单。

**Alternatives considered**:
- 让 `PageNotFoundError` 继承 `RuntimeError`：违背 `api-error-semantics` spec 的原始设计意图（区分业务可恢复异常和不可恢复异常）
- 引入 `RecoverableApiError(Exception)` 中间基类：过度设计，当前无第二个可恢复异常类型

### D2: Phase A 的 `fetch_list_pages()` 用宽泛 try/except 包裹

**Decision**: `run_phase_a()` 对整个 `fetch_list_pages()` 调用包裹一个 `try/except Exception`，失败后 `list_page_content` 设为空 dict。

**Rationale**: `fetch_list_pages()` 本身也改为 `except Exception`，但 Phase A 增加外层保护提供防御深度。单个 list_page 失败（无论原因）不应阻断整个 Phase A 的 manifest 构建——list_page_content 是"best effort"数据，Phase C 可在缺失时使用简化逻辑。

### D3: 排除取并集，不设"覆盖"语义

**Decision**: 策略 `exclude_categories` 和 CLI `--exclude-category` 合并取**并集**，不设优先级覆盖。

**Rationale**: 策略字段代表持久化偏好（用户项目级配置），CLI 参数代表临时覆盖。并集语义最安全——用户不会因为漏看策略字段而意外爬取不想爬的分类。如果合并结果不符合预期，用户修改策略文件即可（持久化修正）。

**User feedback**: 用户确认"策略字段和参数的排除页面需要合并处理，如果排除的不符合用户预期可以改策略文件里的字段"。

### D4: Page-assignment 无需内部变更

**Decision**: `assign_pages()` 不做任何代码修改。排除在 Phase 0 源头完成。

**Rationale**: 排除发生在 `_discover_category_pages()` 调用前，assigner 收不到被排除分类的页面数据。这避免了在分配逻辑中增加过滤分支，保持 assigner 简单。`page-assignment` spec 的 delta 仅为行为声明（输入已过滤）。

### D5: 排除日志级别为 info

**Decision**: 排除分类的日志 SHALL 使用 info 级别，包含排除列表和来源统计。

**Rationale**: 排除是用户显式意图，应始终在日志中可见。来源统计（strategy=N, cli=M）帮助用户理解排除分类的来源，便于排查"为什么某个分类没被爬取"。

## Risks / Migration

### Risk 1: `except Exception` 过宽可能掩盖真实错误

**Mitigation**: 在所有 `except Exception` 块中，错误仍以 `log.warning` 记录，不会被静默吞掉。仅 `PageNotFoundError` 是需要额外覆盖的非 `RuntimeError` 异常类型。`RuntimeError` 本身仍被 `Exception` 捕获（`RuntimeError` IS-A `Exception`），行为从"向上传播"变为"降级 warning"，这是预期行为。

### Risk 2: Legacy `_strategies_legacy.py` 修改无测试覆盖

**Mitigation**: 修改模式与 `discovery.py` 完全相同（`except RuntimeError` → `except Exception`），风险低。legacy 策略类的 `fetch_list_pages()` 和 `fetch_page_content()` 在结构上与新策略类一致。

### Risk 3: 排除名称拼写错误导致静默未排除

**Mitigation**: spec 要求对未匹配的排除分类名输出 `log.info("Exclude category 'X' not found in homepage categories — ignoring")`。用户可据此察觉拼写错误。

### Risk 4: `category_page_types` 与 `list_pages` 未来再不同步

**Mitigation**: 本次修正 `taxonomy.list_pages` 移除 Modes/Objects，但长期看，Phase A 应检查 `category_page_types` 在遍历 `list_pages` 时跳过已知为 category_page 的条目。这属于后续优化的范围（Non-Goal in this change）。

### Migration Path

1. 现有策略文件无需修改（`exclude_categories` 可选，`except Exception` 向后兼容）
2. BOI 策略文件需回填：移除 Modes/Objects 从 `list_pages`，新增 `exclude_categories`
3. 已有 CLI 调用无需修改（`--exclude-category` 可选）
4. 使用 `--phase all` 的用户不会被此 change 影响（`exclude_categories` 仅影响 Phase 0）
