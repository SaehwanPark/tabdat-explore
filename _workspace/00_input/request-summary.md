# Phase 9-10 Future Items Request Summary

## Goal

Finish the remaining documented future items for Phase 9 and Phase 10 in one branch.

## Phase Fit

- Phase 9: Configuration & Environment
- Phase 10: Execution & State Foundations

Current repo state already covers the first slices for both phases:

- Phase 9 config, runtime `set`, plot defaults, and Parquet `save` / `export`
- Phase 10 named tables, specific execution errors, and executor state handling

## Scope

- Keep `save` Parquet-only.
- Extend `export` to write `.parquet`, `.csv`, and `.feather` based on output suffix.
- Turn `use <path>, lazy engine=polars` into a real bounded Polars lazy path for a small command
  subset.
- Preserve the existing DuckDB eager path, named-table behavior, CLI surface, and docs discipline.
- Update tests, `_workspace/` handoff artifacts, and durable docs.
- Commit meaningful checkpoints, push the temp branch, open the PR, and mark it ready for review.

## Non-Goals

- No new import formats for `use`.
- No `format(...)`, delimiter, compression, or config additions for export.
- No broad Polars parity across SQL, plots, named tables, joins, append, reshape, panel, or later
  phases.
- No Phase 11+ command work in this branch.
