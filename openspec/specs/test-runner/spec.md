# Specification Delta

## Capability 对齐（已确认）

- Capability: `test-runner`
- 来源: `proposal.md`
- 变更类型: new (modified by tdd-schema-alignment)
- 用户确认摘要: grill session 逐项确认——统一测试入口、I2 动态 TestCase 生成、stdlib discover

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Test directory structure
The project SHALL maintain a top-level `tests/` directory with subdirectories mirroring the source module structure under `scripts/`.

- `tests/lib/` for tests of `scripts/lib/` modules
- `tests/pipeline/` for tests of `scripts/pipeline/pipeline/phases/` modules
- Each subdirectory SHALL contain an `__init__.py` file.

#### Scenario: Test discovery via stdlib
- **WHEN** `python -m unittest discover -s tests -v` is executed from the repo root
- **THEN** all test modules under `tests/` SHALL be discovered and executed

### Requirement: Unified test runner entry point
The system SHALL provide `scripts/test_runner.py` as a unified test entry point supporting multiple subcommands.

#### Scenario: Run all tests
- **WHEN** `python3 scripts/test_runner.py all` is executed
- **THEN** both stdlib discover tests AND site sample regression tests SHALL be executed

#### Scenario: Run site sample regression
- **WHEN** `python3 scripts/test_runner.py site-samples --domain <domain>` is executed
- **THEN** only the site sample regression tests for the specified domain SHALL be executed
- **THEN** if `--domain` is omitted, all domains with samples SHALL be tested

### Requirement: I2 dynamic TestCase generation for site samples
The site sample runner SHALL scan `sites/strategies/*/strategy.md` for `samples` frontmatter fields and dynamically generate a separate `unittest.TestCase` class per `(domain, page)` combination.

#### Scenario: Each sample is an independent test case
- **WHEN** a strategy has 3 sample pages defined
- **THEN** 3 separate `TestCase` classes SHALL be generated, each with its own test method
- **THEN** the test report SHALL show each sample as an independent pass/fail entry

#### Scenario: Strategy with no samples
- **WHEN** a strategy.md has no `samples` field
- **THEN** no test cases SHALL be generated for that domain

### Requirement: Test framework uniformity
All Python test files SHALL use `unittest` exclusively. The use of `pytest` or other third-party test frameworks is prohibited.

#### Scenario: Existing pytest test migrated
- **WHEN** a test file imports `pytest`
- **THEN** it SHALL be migrated to use `unittest.TestCase` and `unittest` assertions instead

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
