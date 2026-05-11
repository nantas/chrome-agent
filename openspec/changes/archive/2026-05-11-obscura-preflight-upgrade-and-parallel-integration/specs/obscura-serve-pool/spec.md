# Specification Delta

## Capability 对齐（已确认）

- Capability: `obscura-serve-pool`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: 确认所有 6 项 capability

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: serve-pool-lifecycle

The system SHALL implement a serve pool lifecycle manager that starts an `obscura serve --workers N` process, waits for workers to be ready, and cleanly terminates the process when done.

#### Scenario: serve-pool-start
- **WHEN** a batch fetch requires parallel workers
- **THEN** the system SHALL find an available port, spawn `obscura serve --workers <N> --port <PORT>` as a detached child process, and wait up to 5 seconds for the load balancer to accept connections

#### Scenario: serve-pool-stop
- **WHEN** all URLs in the batch have been fetched
- **THEN** the system SHALL terminate the serve process group (kill child workers), verify all processes are cleaned up, and release the port

#### Scenario: serve-pool-port-availability
- **WHEN** the default port range (9200+) is occupied
- **THEN** the system SHALL scan upward to find the first available port, up to port 9299

### Requirement: serve-pool-concurrent-fetch

The system SHALL support concurrent page content retrieval by distributing fetch requests across the serve worker pool's load balancer.

#### Scenario: concurrent-fetch-distribution
- **WHEN** N URLs are submitted with M workers configured (M ≥ 1)
- **THEN** the system SHALL use a thread pool (max_workers=M or min(N, M)) and issue `obscura fetch <URL> --dump html --quiet --timeout <T>` calls for each URL, relying on Obscura's built-in load balancer to distribute to individual workers

#### Scenario: concurrent-fetch-return-html
- **WHEN** a fetch completes successfully
- **THEN** the system SHALL receive the full page HTML as stdout output and save it to a named HTML file following the convention `NN.html` where NN is the zero-padded page number

#### Scenario: concurrent-fetch-timeout
- **WHEN** a single URL fetch exceeds the configured timeout (default 15s, max 60s)
- **THEN** the system SHALL log the timeout for that URL, continue processing remaining URLs, and report the failure in the results

### Requirement: serve-pool-content-compatibility

The system SHALL produce HTML output that is structurally compatible with the existing Markdown conversion pipeline (`convertTraversalToMarkdown`).

#### Scenario: markdown-via-scrapling-ai-targeted
- **WHEN** Obscura serve pool fetches complete and HTML content is available
- **THEN** the system SHALL write the pre-fetched HTML to a temporary file, then convert to Markdown using `scrapling extract get file://<TEMP>.html <OUTPUT>.md --ai-targeted`, producing Markdown output of equivalent quality to the Scrapling serial path

#### Scenario: markdown-pipeline-reuse
- **WHEN** Obscura serve pool fetches complete and HTML files are saved to the run directory
- **THEN** the system SHALL call `convertTraversalToMarkdown(runDir, manifest, opts)` with `prefetchedHtml` populated, and the conversion step SHALL use Scrapling `--ai-targeted` (via `file://` URL) instead of the simple `htmlToMarkdown()` regex converter

#### Scenario: html-to-markdown-fallback
- **WHEN** Scrapling CLI is unavailable for post-processing (e.g., preflight failure) or the `file://` approach fails
- **THEN** the system SHALL fall back to the built-in `htmlToMarkdown()` regex converter to avoid blocking the Markdown pipeline

#### Scenario: temp-file-cleanup
- **WHEN** Markdown conversion via Scrapling `file://` is complete
- **THEN** the system SHALL clean up all temporary HTML files created for conversion
