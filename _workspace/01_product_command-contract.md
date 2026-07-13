# Product Contract: Phase 24 P0 — SQL and Named-Table Order

## Request Summary

Make explicit SQL result order observable and preservable through `sql ... into` and named-table
activation without adding new syntax.

## Roadmap Phase

Phase 24 P0: stable language semantics before broader command and estimator expansion.

## Roadmap Fit

This is a bounded follow-up to active row order. It covers the existing SQL escape hatch and named
tables while leaving unordered SQL and relation-combination order decisions for later.

## Existing Syntax

Valid forms retain the current grammar:

- `sql select value, label from active order by value desc nulls last`
- `sql select value, label from active order by value desc nulls last into ordered`
- `use ordered`
- `head 2`
- `tail 2`

No new options, commands, or output fields are introduced.

## SQL-Order Rules

- A SQL result follows the row sequence produced by its query. An explicit `order by` defines the
  listed-key order; reproducible total order requires tie-breaker keys that distinguish tied rows.
  SQL without `order by` remains unspecified here.
- A successful `sql ... into name` stores and activates the result without reordering its rows.
- `use name` restores the named table's stored row sequence. `head` and `tail` then consume it using
  the existing active-row contract, including tail relative order.
- A direct SQL result without `into` preserves the query's returned row sequence in its table output.
- Eager, DuckDB-lazy, and Polars-lazy loads agree for ordered SQL; SQL remains an eager boundary for
  named-table creation, and successful named-table activation resets materialization reason as an
  active-table boundary.

## Data And Execution Assumptions

- The active dataset must exist, the query must be a supported `select`/`with` result query, and
  referenced variables/tables must follow current SQL errors.
- DuckDB explicitly enables insertion-order preservation when materializing ordered query results;
  Polars lazy input crosses the existing eager fallback boundary before SQL execution.
- Named-table activation remains eager and rejects lazy `use` options as it does today.
- Append/join/reshape order, unordered SQL, categorical order, and a new sort command remain outside
  this slice.

## Acceptance Criteria

- [x] Direct ordered SQL results retain query order across supported execution paths.
- [x] Tied SQL keys require an explicit tie-breaker for reproducible total order.
- [x] `sql ... into` followed by `head`/`tail` preserves the ordered result sequence.
- [x] Named-table reactivation restores the stored sequence without reordering.
- [x] Named-table creation preserves the existing activation-boundary materialization semantics.
- [x] CLI/help/parser/docs, full tests, type/lint/format checks, and integrated workflow checks pass.

## Non-Goals For This Slice

- New sort syntax or commands, row-ID persistence, append/join/reshape ordering, unordered SQL
  guarantees, categorical ordering, or estimators.
