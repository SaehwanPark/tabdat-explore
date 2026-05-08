# Phase 11 Append Implementation Report

## Summary

Implemented the second Phase 11 data workflow primitive on branch
`codex/tmp-phase11-append-stack`.

## Contract Consumed

`_workspace/01_product_command-contract.md` defines `append <table>` as a strict named-table
vertical stack operation over the active dataset.

## Implemented Behavior

- Added `append <table>` command parsing.
- Required the append input to be an existing session-local named table.
- Required active and appended datasets to have the same column names.
- Required matching DuckDB type names for same-name columns.
- Preserved the active dataset column order in the appended result.
- Replaced the active dataset with the materialized append result.
- Preserved named tables as session-local inputs that are not mutated by append.
- Added table-name completions for `append` and added missing `join` command completion.

## Files Changed

- `src/tabdat/models.py`
- `src/tabdat/parser.py`
- `src/tabdat/executor.py`
- `src/tabdat/backend.py`
- `src/tabdat/shell.py`
- focused parser, executor/backend, CLI tests
- `SPEC.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, and workspace artifacts

## Validation

- `uv run pytest tests/test_parser.py`
- `uv run mypy`
- `uv run pytest tests/test_parser.py tests/test_executor.py tests/test_cli.py tests/test_shell.py`
- `uv run ruff check .`

Final full validation is recorded in the delivery summary.

## Known Limits

- Only session-local named tables can be appended.
- `stack` is not an alias yet.
- The strict schema contract rejects missing, extra, or mismatched-type columns.
- No source indicator, permissive missing-column filling, type coercion policy, file-path append,
  reshape, panel metadata, remote data access, script variables, seeding, or control flow was
  added in this slice.
