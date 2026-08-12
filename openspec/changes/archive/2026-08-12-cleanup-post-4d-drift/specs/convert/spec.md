# Delta: convert

## MODIFIED Requirements

### Requirement: mirror-equivalence-golden-snapshot

A golden snapshot test SHALL verify that explore, pipeline, and pipeline(cdp) convert paths produce byte-identical Markdown from the same HTML input as the shared kernel.

#### Scenario: golden-snapshot-passes
- **WHEN** the same HTML fixture is converted via explore (`sample_converter._apply_extraction`), pipeline (`convert_single_page`), pipeline(cdp) (`convert_html_to_markdown`) and the kernel (`convert_page_full`)
- **THEN** all outputs SHALL be identical to the kernel output (after stripping declared path-specific wrapping)
- **AND** tests/test_convert_equivalence.py SHALL assert this with an embedded fixture that never skips
