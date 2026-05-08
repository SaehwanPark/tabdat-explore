# Phase 11 Append/Stack Command Contract

## Roadmap Phase

Phase 11: Data Workflow & Reproducibility Primitives.

## Command Syntax

```text
append <table>
```

- `<table>` must name an existing session-local named table created by `sql ... into <table>`.
- The active dataset and named table must have the same column names.
- Output column order follows the active dataset.
- Compatible DuckDB types are required for columns with the same name.
- No options are supported in this slice.

## Examples

```text
use baseline.parquet
sql select id, age, sex from active where age >= 65 into older
use baseline.parquet
keep if age < 65
append older
```

Expected output:

```text
Appended older: N rows, M columns
```

## Execution Semantics

- `append` requires an active dataset and a registered named table.
- The append result replaces the active dataset.
- Named tables remain session-local and unchanged by append.
- SQL generation happens inside the DuckDB backend. The executor owns session-state lookup and
  active dataset replacement.
- The current active dataset remains the default command target after append.
- Appended results are materialized as eager DuckDB temp tables, even if either input originated
  from a lazy load.

## User-Facing Errors

- Missing active dataset: `append requires an active dataset; run use <path> first`.
- Unknown named table: `unknown table: <table>`.
- Missing active-side column: `append unknown variable: <column>`.
- Missing named-table column: `append unknown variable in <table>: <column>`.
- Type mismatch: `append type mismatch for <column>: <left_type> vs <right_type>`.
- Invalid table name: `invalid table name: <table>`.
- Reserved table name: `reserved table name: <table>`.
- Unsupported syntax or options are parse errors.

## Non-Goals

- No `stack` alias in this first append slice.
- No source indicator column.
- No missing-column filling or permissive union-by-name mode.
- No type coercion policy beyond DuckDB-compatible strict validation.
- No file-path append inputs.
- No reshape, panel metadata, remote data access, or script-level reproducibility primitives in
  this slice.

## Acceptance Criteria

- Parser tests cover valid append syntax and malformed syntax/options.
- Executor/backend tests cover successful append, column-order alignment, missing active datasets,
  unknown tables, missing columns, and type mismatches.
- CLI smoke tests cover a repeated `-c` named-table append workflow and deterministic output.
- Documentation records the Phase 11 append boundary and remaining future Phase 11 work.
- Full validation passes:
  - `uv run pytest`
  - `uv run mypy`
  - `uv run ruff check .`
  - `uv run ruff format --check .`
