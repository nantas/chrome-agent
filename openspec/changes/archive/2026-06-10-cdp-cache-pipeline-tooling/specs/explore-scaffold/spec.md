# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore-scaffold`
- 来源: `proposal.md`
- 变更类型: modified
- 用户确认摘要: 确认 — scaffold 生成需保护手动编辑的策略文件

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: Scaffold generation with overwrite guard
The strategy scaffold generator SHALL check for an existing `strategy.md` file before writing.

- If the file does not exist, the generator SHALL create it normally.
- If the file exists and its first line starts with `# Auto-generated scaffold`, the generator SHALL overwrite it (re-generation is safe for auto-generated files).
- If the file exists and its first line does NOT start with `# Auto-generated scaffold`, the generator SHALL skip the write and return a result indicating the file was skipped, with a reason message directing the user to delete the file manually if regeneration is desired.

#### Scenario: Generate new strategy
- **WHEN** `sites/strategies/example.com/strategy.md` does not exist
- **THEN** the scaffold generator SHALL create the file with auto-generated frontmatter and content

#### Scenario: Overwrite auto-generated strategy
- **WHEN** `strategy.md` exists and its first line is `# Auto-generated scaffold — review recommended`
- **THEN** the scaffold generator SHALL overwrite the file with updated discovery results

#### Scenario: Skip manually-edited strategy
- **WHEN** `strategy.md` exists and its first line is `# developer.nintendo.com — Nintendo Developer Portal`
- **THEN** the scaffold generator SHALL NOT write to the file and SHALL return `{"skipped": true, "reason": "Manually-edited strategy exists — delete it first to regenerate."}`

### Requirement: Skipped result signaling
When the scaffold generator skips a write due to the overwrite guard, the result dict SHALL include a `skipped` field set to `true` and a `reason` field explaining why.

#### Scenario: Explore reports partial success
- **WHEN** the scaffold generator skips a manually-edited strategy
- **THEN** the explore CLI output SHALL include `"skipped": true` and the reason string, allowing higher-level orchestration to decide whether to proceed or abort
