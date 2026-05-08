# Phase 11 Join/Merge Command Contract

## Roadmap Phase

Phase 11: Data Workflow & Reproducibility Primitives.

## Command Syntax

```text
join <table> on <keylist>
join <table> on <keylist>, how=inner|left
join <table> on <keylist>, suffix(<suffix>)
```

- `<table>` must name an existing session-local named table created by `sql ... into <table>`.
- `<keylist>` is one or more same-name equality keys present on both the active dataset and the
  named table.
- `how=inner` is the default join kind.
- `how=left` preserves all active-dataset rows.
- `suffix(<suffix>)` renames colliding right-side non-key columns; the default suffix is `_right`.
- Duplicate key names are rejected.

## Examples

```text
use patients.parquet
sql select patient_id, clinic from active into clinics
use visits.parquet
join clinics on patient_id
```

Expected output:

```text
Joined clinics: N rows, M columns
```

```text
join lookup on id, how=left suffix(_lookup)
```

Expected behavior: all active rows are retained; right-side non-key column collisions are suffixed
with `_lookup`.

## Execution Semantics

- `join` requires an active dataset and a registered named table.
- The join result replaces the active dataset.
- Named tables remain session-local and unchanged by the join.
- SQL generation happens inside the DuckDB backend. The executor owns session-state lookup and
  active dataset replacement.
- The current active dataset remains the default command target after the join.
- Joined results are materialized as eager DuckDB temp tables, even if either input originated from
  a lazy load.

## User-Facing Errors

- Missing active dataset: `join requires an active dataset; run use <path> first`.
- Unknown named table: `unknown table: <table>`.
- Missing active-side key: `join unknown variable: <key>`.
- Missing right-side key: `join unknown variable in <table>: <key>`.
- Invalid table name: `invalid table name: <table>`.
- Reserved table name: `reserved table name: <table>`.
- Unsupported syntax, options, join kinds, empty suffixes, or duplicate keys are parse errors.

## Non-Goals

- No Stata-compatible `_merge` indicator or cardinality validation.
- No right/full/cross joins.
- No different-name key mapping.
- No arbitrary SQL access to all registered named tables.
- No append/stack, reshape, panel metadata, remote data access, or script-level reproducibility
  primitives in this slice.

## Acceptance Criteria

- Parser tests cover valid join forms and malformed syntax/options.
- Executor/backend tests cover inner joins, left joins, multi-key joins, collision suffixing,
  unknown tables, missing keys, and missing active datasets.
- CLI smoke tests cover a repeated `-c` named-table join workflow and deterministic output.
- Documentation records the Phase 11 join boundary and remaining future Phase 11 work.
- Full validation passes:
  - `uv run pytest`
  - `uv run mypy`
  - `uv run ruff check .`
  - `uv run ruff format --check .`
