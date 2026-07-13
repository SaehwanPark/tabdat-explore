# Request Summary: Phase 24 Active Row-Order Contract

## Goal

Define and verify the active dataset's row sequence for `head`, `tail`, `keep if`, and `drop if`
across eager, DuckDB-lazy, and Polars-lazy execution.

## Phase Fit

Phase 24 P0 language semantics. This follows grouped-result ordering and bounds the next observable
ordering boundary without adding sort syntax or relation metadata.

## Touched Surfaces

- `docs/language-semantics.md`: durable active row-order policy
- `src/tabdat/help/topics/head.md`, `tail.md`, `keep.md`, `drop.md`: user guidance
- `tests/test_executor.py`, `tests/test_cli.py`, `tests/test_help.py`: cross-engine and CLI regressions
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`: roadmap and handoff state

## Assumptions

- The active dataset has a stable current row sequence established by its source or prior supported
  transformation.
- `head n` returns the first `n` rows and `tail n` returns the last `n` rows in that sequence; `0`
  returns no rows.
- Row filters preserve the relative order of retained rows. Missing filter results follow the
  existing keep/drop truth policy and do not reorder surviving rows.
- Row-preserving column and value transformations retain row order; grouped commands use their
  separate grouped-result ordering contract.
- Append/join/reshape ordering, arbitrary SQL ordering, named-table storage order, and a new sort
  command remain separate contracts.

## Non-Goals

- Adding row IDs, sort syntax, a `sort` command, arbitrary SQL rewriting, append/join/reshape order,
  categorical order, or estimator behavior.
