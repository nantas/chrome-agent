# Specification Delta

## Capability 对齐（已确认）

- Capability: `strategy-schema`
- 来源: `proposal.md`（testing-governance change 中 modified，本次继续 modified）
- 变更类型: modified
- 用户确认摘要: grill session 确认——AGENTS.md C9 扩展 + 08-tech-stack 新增 TDD 段落

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: C9 references TDD vertical slice
AGENTS.md §0.5 C9 SHALL reference the TDD vertical slice methodology, directing developers to `08-tech-stack.md` §4 for detailed guidance.

#### Scenario: Developer reads C9
- **WHEN** a developer reads AGENTS.md §0.5 C9
- **THEN** the constraint text SHALL include "遵循 vertical slice TDD（详见 `08-tech-stack.md` §4 TDD 约定）"

### Requirement: TDD conventions paragraph in tech-stack
`docs/architecture/08-tech-stack.md` §4 SHALL include a "TDD 约定" subsection documenting the project's test-driven development methodology.

The subsection SHALL cover:
- Vertical slice principle: one test → one implementation → pass, repeated
- Anti-horizontal slicing: do not write all tests then all code
- Behavior over implementation: tests verify public interfaces, not internals
- Refactor only after GREEN

#### Scenario: Developer reads TDD conventions
- **WHEN** a developer reads `08-tech-stack.md` §4
- **THEN** a "TDD 约定" subsection SHALL be present with the four principles listed above
