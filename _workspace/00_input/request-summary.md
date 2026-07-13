# Request Summary: Phase 24 Join Row-Order Contract

## Goal

Define and verify how `join table_name on keyvars` orders rows when active rows match zero, one, or
multiple rows in a named table.

## Phase Fit

Phase 24 P0 language semantics. This follows the completed active, SQL/named-table, and append order
slices and bounds the first keyed relation-combination result without adding syntax.

## Touched Surfaces

- `docs/language-semantics.md`: durable join result-sequence policy
- `docs/command-reference.md`, `src/tabdat/help/topics/join.md`: user-facing join syntax and order
- `src/tabdat/backend.py`, `src/tabdat/executor.py`: collision-safe join ordinals and pre-materialized
  key/table validation
- `tests/test_executor.py`, `tests/test_cli.py`, `tests/test_help.py`: duplicate-match, unmatched-row,
  collision, failure-state, and cross-engine regressions
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`: roadmap and handoff state

## Assumptions

- The active dataset is the left input and has a current row sequence; the named table is the right
  input and has a stored row sequence.
- For each active row, matching right rows are emitted in the named table's stored order. Output is
  grouped by active-row order; duplicate matches remain present.
- `inner` omits active rows with no match. `left` emits one missing-right row for each active row
  with no match.
- Existing key equality, suffixing, schema, and missing-key behavior remain unchanged.
- Append, reshape, categorical ordering, and a new sort command remain separate contracts.

## Non-Goals

- Adding row IDs, sort syntax, a `sort` command, SQL rewriting, append/reshape order,
  categorical order, or estimator behavior.
