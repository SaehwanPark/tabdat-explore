# Product Contract: Phase 24 P0 — Reshape Row Order

## Request Summary

Make existing `reshape long` and `reshape wide` result ordering sequence-preserving and predictable
without adding new syntax.

## Roadmap Phase

Phase 24 P0: stable language semantics before broader command and estimator expansion.

## Roadmap Fit

This is a bounded follow-up to the completed active, SQL/named-table, append, and join order
contracts. It defines the result sequence for wide/long layout changes while leaving categorical order
separate.

## Existing Syntax

Valid forms retain the current grammar:

- `use source.parquet`
- `reshape long income cost, i(id) j(year)`
- `reshape wide income cost, i(id) j(year)`
- `head 5`

No new options, commands, or output fields are introduced.

## Reshape-Order Rules

- `reshape long` preserves the active source-row sequence. For each source row, generated rows are
  emitted in the established wide-column j-value sequence.
- `reshape wide` emits one row per identifier group in the order of the first active row belonging to
  that group. Existing generated-column order and duplicate-cell aggregation remain unchanged.
- `head`/`tail` consume each reshape result using the active row-order contract.
- Eager, DuckDB-lazy, and Polars-lazy inputs produce the same reshape result sequence. Reshape crosses
  the existing eager boundary where required and preserves current state reporting.

## Data And Execution Assumptions

- Existing identifier, stub, j-value, output-column, and duplicate-cell validation remains unchanged.
- The source sequence is the current active sequence, not a newly sorted identifier or j-value order.
- Append/join order, unordered SQL, categorical order, and a new sort command remain outside this
  slice.

## Acceptance Criteria

- [ ] Long output follows source-row order and established j-value sequence.
- [ ] Wide output follows first-appearance order of identifier groups.
- [ ] Existing wide/long column layout and duplicate-cell behavior remain unchanged.
- [ ] Eager, DuckDB-lazy, and Polars-lazy result previews agree.
- [ ] CLI/help/docs, focused tests, full tests, type/lint/format checks, and integrated workflow
  checks pass.

## Non-Goals For This Slice

- New sort syntax or commands, row-ID persistence, append/join ordering, unordered SQL guarantees,
  categorical ordering, duplicate-cell aggregation changes, or estimators.
