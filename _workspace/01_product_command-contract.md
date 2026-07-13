# Product Contract: Phase 24 P0 — Grouped-Result Ordering

## Request Summary

Make existing grouped outputs deterministic and type-aware without adding ordering syntax or a new
command.

## Roadmap Phase

Phase 24 P0: stable language semantics before broader command and estimator expansion.

## Roadmap Fit

This is a bounded ordering increment after the identifier, missing-value, coercion, arithmetic-result,
and overwrite contracts. It fixes display ordering where the current implementation can stringify
numeric keys and sort `10` before `2`.

## Existing Syntax

Valid forms retain the current grammar:

- `tabulate, rows(region) columns(code)`
- `by region: count`
- `collapse mean value, by(region)`
- `bar code`

No new options, commands, or output fields are introduced.

## Ordering Rules

- Grouping dimensions in `by summarize`, `by count`, `collapse`, and long-form `tabulate` are sorted
  ascending in their native scalar domain; missing values sort last.
- Wide-form `tabulate` preserves that same native order for row keys and column headers. Numeric keys
  are ordered numerically, not by their rendered text labels.
- `bar` nonmissing categories are ordered by descending count; equal-count categories use native
  scalar order, and the missing category is always last.
- String values use lexicographic order. Boolean values use false before true. Numeric values use
  numeric order.
- Row-preserving active-dataset order, `head`/`tail`, arbitrary SQL `order by`, and categorical
  ordering remain outside this slice.

## Data And Execution Assumptions

- The active dataset must exist and referenced grouping/category variables must exist, following
  existing command validation and error wording.
- Eager and DuckDB-lazy grouped commands use the existing DuckDB `ORDER BY` boundary.
- Polars-lazy `tabulate` validation still occurs before fallback; supported grouped output uses the
  same DuckDB ordering boundary after fallback.
- The pure wide-result assembly preserves the already ordered long-form key stream instead of
  re-sorting rendered labels.

## Acceptance Criteria

- [x] Numeric tabulate keys appear in numeric order (`2`, then `10`) in both long and wide output.
- [x] Text keys remain lexicographic and missing keys are last in grouped outputs.
- [x] Bar ties use native category order and missing categories remain last.
- [x] Eager, DuckDB-lazy, and Polars-lazy tabulate outputs agree for mixed numeric/missing fixtures.
- [x] CLI/help/docs, full tests, type/lint/format checks, and integrated workflow checks pass.

## Non-Goals For This Slice

- New sort syntax or commands, active row-order guarantees, `head`/`tail` ordering, arbitrary SQL
  ordering, categorical ordering, exact arithmetic storage widths, overflow reporting, or estimators.
