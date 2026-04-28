# output-lifecycle-git-governance Specification

## Purpose
TBD - created by archiving change align-output-lifecycle-gitignore. Update Purpose after archive.
## Requirements
### Requirement: Disposable outputs git ignore alignment
The repository MUST ignore disposable run outputs under `outputs/` in `.gitignore`.

#### Scenario: Disposable output generated
- **WHEN** a workflow emits transient run-scoped files beneath `outputs/`
- **THEN** those files SHALL remain untracked by default under Git status

### Requirement: Durable reports versioning visibility
The repository MUST keep durable report artifacts under `reports/` eligible for version control by default.

#### Scenario: Durable report created
- **WHEN** a workflow writes a reusable report or evidence file under `reports/`
- **THEN** the file SHALL be allowed to appear in Git status and be commit-eligible

