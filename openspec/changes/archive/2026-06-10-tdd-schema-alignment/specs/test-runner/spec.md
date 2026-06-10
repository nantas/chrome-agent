# Specification Delta

## Capability 对齐（已确认）

- Capability: `test-runner`
- 来源: `proposal.md`（testing-governance change 中创建，本次 modified）
- 变更类型: modified
- 用户确认摘要: grill session 确认——项目级 opsx-verify prompt 增加 test_runner 调用

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: opsx-verify runs project test suite
The project-level `.pi/prompts/opsx-verify.md` SHALL include a step that runs the project test suite and incorporates results into the verification report, with J3 severity grading.

#### Scenario: Test suite exists and passes
- **WHEN** `scripts/test_runner.py` exists and `python3 scripts/test_runner.py all` exits with code 0
- **THEN** the verification report SHALL include a "Test Suite" section showing all tests passed

#### Scenario: Test suite exists and has failures
- **WHEN** `python3 scripts/test_runner.py all` exits with non-zero code
- **THEN** the verification report SHALL include each failure as an issue with appropriate J3 severity

#### Scenario: Test runner not found
- **WHEN** `scripts/test_runner.py` does not exist
- **THEN** this step SHALL be skipped with a note in the report
