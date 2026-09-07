# Implementation Report: `missing` null-missingness report

## Contract

`_workspace/01_product_command-contract.md`

## Delivered

- Added `missing [varlist]` command parsing, typed command/result models, executor dispatch, CLI
  schema/effect metadata, and shell column/command completion.
- Added DuckDB eager/lazy and Polars-lazy aggregate implementations reporting total, missing,
  nonmissing, and missing percentage while preserving Polars lazy execution state.
- Added deterministic terminal and JSON output, explicit-null semantics, empty-dataset handling, and
  pre-scan unknown-variable validation.
- Updated MCP EDA guidance, in-app help, command reference/navigation, user guide, language semantics,
  README, architecture/spec/changelog records, and focused parser/backend/executor/CLI/shell/MCP tests.

## Validation

- `uv run pytest tests/test_missing.py tests/test_shell.py tests/test_cli.py tests/test_docs_alignment.py` — 211 passed.
- `uv run pytest tests/test_mcp.py tests/test_missing.py` — 20 passed.
- `uv run pytest -q` — 1,293 passed (320 warnings from existing statistical/backend dependencies).
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `uv run basedpyright src` — 0 errors, 0 warnings, 0 notes.
- `uv run python scripts/check_docs_alignment.py` — passed.

## Notes

The command reports explicit nulls only. Empty strings and user-defined sentinel values remain
nonmissing; missingness patterns and imputation remain out of scope.
