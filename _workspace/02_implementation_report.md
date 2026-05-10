# Phase 9-10 Future Items Implementation Report

## Contract Consumed

`_workspace/01_product_command-contract.md`

## Files Changed

- `src/tabdat/backend.py`, `src/tabdat/executor.py`, `src/tabdat/models.py`,
  `src/tabdat/formatter.py`
- `tests/test_parser.py`, `tests/test_executor.py`, `tests/test_cli.py`
- `SPEC.md`, `ARCHITECTURE.md`, `CHANGELOG.md`
- `_workspace/00_input/request-summary.md`, `_workspace/01_product_command-contract.md`

## Implementation Notes

- Kept `save` Parquet-only and added suffix-driven `.parquet`, `.csv`, and `.feather` `export`.
- Added a distinct `ExportResult` / `Exported:` user-facing result path.
- Added a bounded Polars lazy backend state for local Parquet loads.
- Preserved lazy state through column projection, row filtering, describe/count/head/tail, and
  export/save.
- Added explicit eager fallback for unsupported commands before they enter the existing DuckDB
  execution path.
- Kept named-table, SQL, reshape, panel, and plotting behavior on the eager DuckDB path.

## Validation

- `uv run pytest tests/test_parser.py tests/test_executor.py tests/test_cli.py`
- `uv run pytest` passed with 319 tests.
- `uv run pyright`
- `uv run ruff check .`
- `uv run ruff format --check .`

## Known Gaps

- `engine=polars` remains intentionally bounded to local Parquet plus projection/filter/count and
  preview operations.
- Unsupported Polars-lazy commands materialize eagerly instead of attempting broad native parity.
- Remote Parquet still belongs to the DuckDB path; Polars-lazy remote loading is not part of this
  slice.
