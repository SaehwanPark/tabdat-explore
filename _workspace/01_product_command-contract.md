# Product Contract: Phase 24 P0 — Append Row Order

## Request Summary

Make existing `append table_name` behavior sequence-preserving and predictable without adding new
syntax.

## Roadmap Phase

Phase 24 P0: stable language semantics before broader command and estimator expansion.

## Roadmap Fit

This is a bounded follow-up to SQL/named-table order. It covers vertical stacking while leaving join,
reshape, and categorical order decisions for later.

## Existing Syntax

Valid forms retain the current grammar:

- `sql select value, label from active order by value desc nulls last into followup`
- `use source.parquet`
- `append followup`
- `head 5`
- `tail 3`

No new options, commands, or output fields are introduced.

## Append-Order Rules

- The active dataset is the left input. `append name` emits every active row first, then every row
  from named table `name` in its stored sequence.
- Append does not sort, deduplicate, or interleave rows. The combined sequence is consumed by
  `head`/`tail` using the active row-order contract.
- Eager, DuckDB-lazy, and Polars-lazy inputs produce the same combined row sequence. Append crosses
  the existing eager boundary for relation combination and preserves its current state reporting.

## Data And Execution Assumptions

- The active dataset and named table must exist, and current append schema compatibility checks remain
  unchanged.
- Both inputs use their already established sequences; SQL source creation should use explicit order
  and tie-breakers when a reproducible named-table sequence is required.
- Join/reshape order, unordered SQL, categorical order, and a new sort command remain outside this
  slice.

## Acceptance Criteria

- [x] Append emits active rows before named-table rows across supported execution paths.
- [x] Head/tail of the combined sequence preserve left-then-right order.
- [x] Append does not sort, deduplicate, or interleave inputs.
- [x] CLI/help/docs, full tests, type/lint/format checks, and integrated workflow checks pass.

## Non-Goals For This Slice

- New sort syntax or commands, row-ID persistence, join/reshape ordering, unordered SQL guarantees,
  categorical ordering, or estimators.
