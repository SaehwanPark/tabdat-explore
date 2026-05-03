# Request Summary: Phase 4 SQL Integration

## Goal

Implement roadmap Phase 4 on a temporary branch and publish it as a PR.

## Phase Fit

Phase 4 adds SQL power without broadening the Stata-inspired command surface:

- `sql` command for single-line and multiline result-producing queries
- active dataset exposed as `active`
- `into <table>` support

## User Decision

`into <table>` should change/update the active dataset. The table name is used in user-facing output;
it is not a persistent table catalog feature.

## Touched Surfaces

- command model
- parser
- executor
- DuckDB backend
- formatter
- CLI shell continuation for multiline SQL
- tests
- README, SDD docs, and workspace handoff artifacts

## Non-Goals

- no persistent writes
- no `use <table>` support
- no prompt-toolkit UX
- no non-result SQL statements
