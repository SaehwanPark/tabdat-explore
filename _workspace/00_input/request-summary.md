# Request Summary: Phase 24 Reshape Row-Order Contract

## Goal

Define and verify how existing `reshape long` and `reshape wide` commands order their result rows
without adding syntax.

## Phase Fit

Phase 24 P0 language semantics. This follows the completed active, SQL/named-table, append, and join
order slices and closes the remaining relation-changing row-order boundary before categorical order.

## Touched Surfaces

- `docs/language-semantics.md`: durable long/wide result-sequence policy
- `src/tabdat/help/topics/reshape.md`, `docs/command-reference.md`: user guidance
- `src/tabdat/backend.py`, `src/tabdat/executor.py`: collision-safe ordinals and pre-materialized
  long/wide validation
- `tests/test_executor.py`, `tests/test_cli.py`, `tests/test_help.py`: non-sorted source,
  collision, null/duplicate-cell, failure-state, and cross-engine regressions
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`: roadmap and handoff state

## Assumptions

- `reshape long` preserves current active-row order; for each source row, generated rows follow the
  established wide-column j-value sequence.
- `reshape wide` emits one row per identifier group in the order of the first active row belonging
  to each group; existing generated-column and duplicate-cell behavior remains unchanged.
- Eager, DuckDB-lazy, and Polars-lazy inputs produce the same result sequence after the existing
  reshape materialization boundary.
- Append/join order, categorical order, and a new sort command remain separate contracts.

## Non-Goals

- Adding row IDs, sort syntax, a `sort` command, SQL rewriting, append/join order, categorical order,
  duplicate-cell aggregation changes, or estimator behavior.
