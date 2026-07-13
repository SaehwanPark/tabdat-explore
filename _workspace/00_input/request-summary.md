# Request Summary: Phase 24 Append Row-Order Contract

## Goal

Define and verify how `append table_name` combines the current active sequence with a named table's
stored sequence.

## Phase Fit

Phase 24 P0 language semantics. This follows SQL/named-table order and bounds the first
relation-combination sequence without adding syntax.

## Touched Surfaces

- `docs/language-semantics.md`: durable append sequence policy
- `src/tabdat/help/topics/append.md`: user guidance for left-then-right row order
- `tests/test_executor.py`, `tests/test_cli.py`, `tests/test_help.py`: cross-engine and CLI regressions
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`: roadmap and handoff state

## Assumptions

- The active dataset has a current sequence, and a named table has its stored sequence.
- `append name` emits all active rows first, followed by all named-table rows in their stored order.
- Append does not sort, deduplicate, or interleave rows; `head` and `tail` consume the combined
  sequence using the active row-order contract.
- Join/reshape ordering, categorical ordering, and a new sort command remain separate contracts.

## Non-Goals

- Adding row IDs, sort syntax, a `sort` command, SQL rewriting, join/reshape order, categorical order,
  or estimator behavior.
