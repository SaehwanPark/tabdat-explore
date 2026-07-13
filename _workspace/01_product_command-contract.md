# Product Contract: Phase 24 P0 — Join Row Order

## Request Summary

Make existing `join table_name on keyvars` result ordering sequence-preserving and predictable
without adding new syntax.

## Roadmap Phase

Phase 24 P0: stable language semantics before broader command and estimator expansion.

## Roadmap Fit

This is a bounded follow-up to the completed active, SQL/named-table, and append order contracts. It
covers keyed relation combination while leaving reshape and categorical order decisions for later.

## Existing Syntax

Valid forms retain the current grammar:

- `sql select value, label from active order by value desc nulls last into followup`
- `use source.parquet`
- `sql select key, label from active order by key, label into lookup`
- `use source.parquet`
- `join lookup on key, how=left`
- `head 5`

No new options, commands, or output fields are introduced.

## Join-Order Rules

- The active dataset is the left input. For each active row, `join name on keys` emits matching rows
  from named table `name` in that table's stored sequence.
- Output is grouped by active-row sequence. A later active row never appears before an earlier active
  row's matches, and duplicate right-side matches are preserved.
- An `inner` join omits active rows with no match. A `left` join emits one row with missing right-side
  values for each active row with no match.
- Eager, DuckDB-lazy, and Polars-lazy inputs produce the same join result sequence. Join crosses the
  existing eager boundary where required and preserves current state reporting.

## Data And Execution Assumptions

- The active dataset and named table must exist. Existing key validation, equality behavior, suffixing,
  and output-column rules remain unchanged.
- Both inputs use their already established sequences; SQL source creation should use explicit order
  and tie-breakers when a reproducible named-table sequence is required.
- Append, reshape order, unordered SQL, categorical order, and a new sort command remain outside this
  slice.

## Acceptance Criteria

- [x] Join groups results by active-row order and preserves named-table match order.
- [x] Duplicate right-side matches remain present for inner and left joins.
- [x] Inner and left unmatched-row behavior remains unchanged and ordered.
- [x] Eager, DuckDB-lazy, and Polars-lazy result previews agree.
- [x] CLI/help/docs, focused tests, full tests, type/lint/format checks, and integrated workflow
  checks pass.

## Non-Goals For This Slice

- New sort syntax or commands, row-ID persistence, append/reshape ordering, unordered SQL guarantees,
  categorical ordering, or estimators.
