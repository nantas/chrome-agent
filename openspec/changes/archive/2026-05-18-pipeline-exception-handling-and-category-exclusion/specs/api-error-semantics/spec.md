# Specification Delta

## Capability 对齐（已确认）

- Capability: `api-error-semantics`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: 异常层次结构

The system SHALL 在 `client.py` 中定义以下异常层次：

```
Exception
├── PageNotFoundError      # missingtitle, nosuchpage — 可跳过，页面不存在
└── (RuntimeError)         # 其他 API 错误 — 不可恢复，继续传播
```

`client._request()` SHALL 在检测到 `"error"` 响应时，检查 `data["error"]["code"]`：
- `code` 为 `"missingtitle"` 或 `"nosuchpage"` 时，`raise PageNotFoundError`
- 其他 `code` 值时，保持当前 `raise RuntimeError(f"API error: {data['error']}")`

#### Scenario: missingtitle 页面触发 PageNotFoundError

- **WHEN** `client.parse(page="Bosses")` 且 API 返回 `{"error": {"code": "missingtitle"}}`
- **THEN** `_request()` SHALL 抛出 `PageNotFoundError("Bosses")` 而非 `RuntimeError`
- **AND** `PageNotFoundError` SHALL 继承自 `Exception`（可被 `except Exception` 捕获，但不被 `except RuntimeError` 误判为不可恢复错误）

#### Scenario: 其他 API 错误保持 RuntimeError

- **WHEN** API 返回 `{"error": {"code": "internal_api_error", "info": "..."}}`
- **THEN** `_request()` SHALL 保持抛出 `RuntimeError`
- **AND** 行为与当前一致

### Requirement: 策略层对 PageNotFoundError 的优雅处理

The system SHALL 在所有调用 `client.parse()` 和 `client.query()` 的管线策略层代码（discovery 策略、acquisition 策略、legacy 策略）中使用 `except Exception` 捕获 `PageNotFoundError`，不得使用 `except RuntimeError`。

具体受影响的方法：
- `AllPagesDiscoveryStrategy.fetch_list_pages()`（`strategies/discovery.py`）
- `CategoryMembersDiscoveryStrategy.fetch_list_pages()`（`strategies/discovery.py`）
- `HtmlRenderedAcquisitionStrategy.fetch_page_content()`（`strategies/acquisition.py`）
- `HybridAcquisitionStrategy.fetch_page_content()`（`strategies/acquisition.py`）
- `_strategies_legacy.py` 中所有 legacy 策略类的 `fetch_list_pages()` 和 `fetch_page_content()`

`PageNotFoundError` 被捕获后 SHALL 以 `log.warning` 记录，不影响当前分类/页面的其他处理，不向上传播。

#### Scenario: discovery-fetch-list-pages-missing-title

- **WHEN** `AllPagesDiscoveryStrategy.fetch_list_pages()` 调用 `client.parse(page="Modes")` 且 API 返回 `missingtitle`
- **THEN** `client.parse()` SHALL 抛出 `PageNotFoundError("Modes")`
- **AND** `fetch_list_pages()` SHALL 以 `except Exception` 捕获该异常
- **AND** SHALL 记录 `log.warning("Failed to fetch list page Modes: ...")` 
- **AND** SHALL 继续处理 `list_pages` 中的下一个条目

#### Scenario: acquisition-fetch-page-missing-title

- **WHEN** `HtmlRenderedAcquisitionStrategy.fetch_page_content()` 调用 `client.parse(page="NonExistent")` 且 API 返回 `missingtitle`
- **THEN** `client.parse()` SHALL 抛出 `PageNotFoundError("NonExistent")`
- **AND** `fetch_page_content()` SHALL 以 `except Exception` 捕获该异常
- **AND** SHALL 记录 `log.warning` 并返回包含 `wikitext: None` 的结果

### Requirement: Phase A 对 fetch_list_pages 的防御性保护

The system SHALL 在 `run_phase_a()` 中对 `discovery_strategy.fetch_list_pages()` 调用包裹 try/except，确保单个 list_page 获取失败不阻断整个 Phase A。

#### Scenario: phase-a-fetch-list-pages-graceful

- **WHEN** `run_phase_a()` 调用 `discovery_strategy.fetch_list_pages()` 时，内部某个 list_page 的 `client.parse()` 触发 `PageNotFoundError`
- **THEN** `run_phase_a()` SHALL 捕获来自 `fetch_list_pages()` 的任何异常
- **AND** SHALL 记录 `log.warning("Failed to fetch list page content: ... — continuing without")`
- **AND** SHALL 将 `list_page_content` 设为空 dict `{}`
- **AND** SHALL 继续构建 manifest 并完成 Phase A

#### Scenario: phase-a-unchanged-on-other-errors

- **WHEN** `fetch_list_pages()` 因非 `PageNotFoundError` 的异常（如网络超时重试耗尽）而失败
- **THEN** `run_phase_a()` SHALL 以相同的 try/except 保护捕获，行为与 `PageNotFoundError` 一致
- **AND** SHALL 不区分异常类型，全部降级为 warning 并继续

## ADDED Requirements

*(无新增 requirements，本次仅修改现有 requirement 的范围和约束)*
