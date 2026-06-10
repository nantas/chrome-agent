# Specification Delta

## Capability 对齐（已确认）

- Capability: `sample-discovery`
- 来源: `proposal.md`
- 变更类型: new
- 用户确认摘要: grill session 确认——agent 选样本、用户确认、写入 strategy.md frontmatter

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Sample list in strategy frontmatter
The site strategy SHALL declare sample pages in the `samples` field of its YAML frontmatter.

Each entry SHALL contain:
- `page`: the URL path or cache-safe path identifying the page
- `label`: a human-readable description of why this page is representative

#### Scenario: Strategy with samples
- **WHEN** a strategy.md frontmatter contains:
  ```yaml
  samples:
    - page: "Packages/.../Pages/Page_239857945.html"
      label: "复杂嵌套表格页面"
  ```
- **THEN** the test runner SHALL locate this page in `.cache/` and include it in sample regression

#### Scenario: Strategy without samples
- **WHEN** a strategy.md has no `samples` field
- **THEN** the test runner SHALL skip that domain entirely

### Requirement: Sample page data from cache
Sample regression SHALL read input data from the standard `.cache/` directory using the same cache mechanism as the pipeline.

#### Scenario: Cached sample page
- **WHEN** a sample page listed in strategy frontmatter has a corresponding `.cache/chrome-cdp/<domain>/<safe_path>.json` entry
- **THEN** the runner SHALL load the cached HTML and run it through the conversion pipeline

#### Scenario: Missing cache for sample page
- **WHEN** a sample page listed in strategy frontmatter has no cache entry
- **THEN** the runner SHALL report a test ERROR indicating the sample page must be fetched first
