# Changelog

All notable project changes are tracked here.

## Unreleased

### Added

- Added the Phase 3 inspection slice with executable `codebook`, `count`, `head`, and `tail`
  commands over the active Parquet dataset.
- Added the Phase 2 parser foundation with structured command options, `if` clauses, expression
  ASTs, parsed-only future command forms, and focused diagnostics tests.
- Fixed Phase 2 parser regressions so `summarize` rejects assignment syntax and punctuated varlist
  names remain supported.
- Added Phase 1 `tabdat` CLI skeleton with `use`, `describe`, and `summarize`.
- Added DuckDB-backed local Parquet loading and numeric summary execution.
- Added focused parser, executor/backend, and CLI smoke tests.
- Added Phase 0 product guardrails for positioning, naming, MVP assumptions, non-goals, and contributor expectations.
- Added the v0 command glossary with the initial 12-command surface.
- Added SDD state files with feature status and planned architecture.
- Added repository guidance for 2-space tab size and proactive linting/formatting.
