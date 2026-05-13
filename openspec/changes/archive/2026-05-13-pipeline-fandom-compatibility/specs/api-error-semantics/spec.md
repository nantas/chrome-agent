# Specification Delta

## Capability 对齐（已确认）

- Capability: `api-error-semantics`
- 来源: `proposal.md` — New Capabilities
- 变更类型: `new`
- 用户确认摘要: 用户确认在 pipeline 中需要区分可跳过的业务异常和不可恢复系统异常

## 规范真源声明

- 本文件是 `api-error-semantics` 在本次 change 中的行为规范真源

## ADDED Requirements

### Requirement: 异常层次结构

The system SHALL 在 `client.py` 中定义以下异常层次：

```
Exception
├── PageNotFoundError      # missingtitle, nosuchpage — 可跳过，页面不存在
├── ApiRateLimitError      # HTTP 429 — 应退避重试（现有 _request 重试逻辑可处理）
└── (RuntimeError)         # 其他 API 错误 — 不可恢复，继续传播
```

`client._request()` SHALL 在检测到 `"error"` 响应时，检查 `data["error"]["code"]`：
- `code` 为 `"missingtitle"` 或 `"nosuchpage"` 时，`raise PageNotFoundError`
- 其他 `code` 值时，保持当前 `raise RuntimeError(f"API error: {data['error']}")`

#### Scenario: missingtitle 页面触发 PageNotFoundError

- **WHEN** `client.parse(page="Bosses")` 且 API 返回 `{"error": {"code": "missingtitle"}}`
- **THEN** `_request()` SHALL 抛出 `PageNotFoundError("Bosses")` 而非 `RuntimeError`
- **AND** `PageNotFoundError` SHALL 继承自 `Exception`（可被 `except Exception` 捕获，但不被误判为不可恢复错误）

#### Scenario: 其他 API 错误保持 RuntimeError

- **WHEN** API 返回 `{"error": {"code": "internal_api_error", "info": "..."}}`
- **THEN** `_request()` SHALL 保持抛出 `RuntimeError`
- **AND** 行为与当前一致

### Requirement: Phase B 对 PageNotFoundError 的优雅处理

The system SHALL 在 `process_single_page()` 中捕获 `PageNotFoundError`，返回 `status: "skipped"` 而非 `status: "error"`。

#### Scenario: 页面缺失时优雅跳跃

- **WHEN** `content_strategy.fetch_page_content()` 抛出 `PageNotFoundError`
- **THEN** `process_single_page()` SHALL 返回 `{"title": title, "status": "skipped", "error": None, "reason": "page_not_found"}`
- **AND** SHALL 不记入 failure_count（保持 success + skipped + failure 三维统计）
- **AND** 日志级别为 `info` 而非 `warning`

#### Scenario: 非 PageNotFoundError 的异常处理

- **WHEN** `content_strategy.fetch_page_content()` 抛出非 `PageNotFoundError` 的异常
- **THEN** `process_single_page()` SHALL 保持返回 `status: "error"`
- **AND** 行为与当前一致

### Requirement: _process_html_page None-safety

The system SHALL 修复 `_process_html_page()` 中 `raw.get("html", "")` 的 None-safety 问题。

#### Scenario: html 值为 None

- **WHEN** `raw` dict 包含 `{"html": None, "images": [], "wikitext": None}`
- **THEN** `html = raw.get("html", "")` SHALL 返回 `""`（空字符串）
- **AND** 方法 SHALL 返回 `{"title": title, "status": "empty", "error": "Empty HTML"}` 而非崩溃

#### Scenario: html 值为有效字符串

- **WHEN** `raw` dict 包含 `{"html": "<div>content</div>", ...}`
- **THEN** `_process_html_page()` SHALL 正常处理 HTML 内容
- **AND** 行为不变
