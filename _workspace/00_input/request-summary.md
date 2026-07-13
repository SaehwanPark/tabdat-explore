# Request Summary: Phase 24 SQL and Named-Table Order Contract

## Goal

Define and verify how an explicitly ordered SQL result becomes the active row sequence through
`sql ... into` and later named-table activation.

## Phase Fit

Phase 24 P0 language semantics. This follows active row order and makes the existing SQL escape hatch
compose predictably with previews and named tables without adding syntax.

## Touched Surfaces

- `docs/language-semantics.md`: durable SQL and named-table sequence policy
- `src/tabdat/help/topics/sql.md`, `src/tabdat/help/topics/use.md`, `docs/user-guide.md`: user
  guidance for explicit SQL ordering and named-table reactivation
- `tests/test_executor.py`, `tests/test_cli.py`, `tests/test_help.py`, `tests/test_parser.py`:
  cross-engine, parser, and CLI regressions
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`: roadmap and handoff state

## Assumptions

- An explicit SQL `order by` defines the result sequence returned by the SQL query.
- `sql ... into name` makes the query result the active dataset in that sequence, and `use name`
  restores the stored sequence.
- `head` and `tail` consume the restored active sequence; row-preserving transformations keep it.
- SQL without `order by` has no deterministic row-order guarantee from this slice.
- Append/join/reshape ordering, categorical ordering, and a new sort command remain separate
  contracts.

## Non-Goals

- Adding row IDs, sort syntax, a `sort` command, SQL rewriting, append/join/reshape order, categorical
  order, or estimator behavior.
