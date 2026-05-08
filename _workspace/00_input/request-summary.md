# Phase 11 Panel Metadata Request Summary

## Goal

Implement the next unfinished Phase 11 prerequisite before moving to Phase 12: session-local panel
identifier metadata for estimation-ready data workflows.

## Phase Fit

Roadmap Phase 11: Data Workflow & Reproducibility Primitives.

Prior phases and completed Phase 11 slices were validated before implementation:

- `uv run pytest`
- `uv run mypy`
- `uv run ruff check .`
- `uv run ruff format --check .`

## Scope

- Add `panel <id_var> <time_var>`, `panel`, and `panel clear`.
- Store panel metadata on the active dataset and named-table snapshots where applicable.
- Validate active data, variable existence, missing values, and duplicate id/time pairs.
- Preserve or clear metadata deterministically across existing transformations.
- Update parser, executor, backend validation helpers, formatter, shell completions, focused tests,
  and durable docs.

## Non-Goals

- No durable metadata persistence in Parquet output.
- No estimation commands.
- No `xtset` compatibility alias.
- No script macros, seeding, control flow, or remote access.
