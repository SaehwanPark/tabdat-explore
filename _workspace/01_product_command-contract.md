# Product Contract: Phase 24 P0 — Active Row Order

## Request Summary

Make the current active row sequence observable and consistent for previews and row filters without
adding a sorting command or new syntax.

## Roadmap Phase

Phase 24 P0: stable language semantics before broader command and estimator expansion.

## Roadmap Fit

This is a bounded follow-up to grouped-result ordering. It covers the existing preview and filter
commands while leaving relation-combination and user-SQL order decisions for later.

## Existing Syntax

Valid forms retain the current grammar:

- `head 2`
- `tail 2`
- `keep if value != 1`
- `drop if value == 1`

No new options, commands, or output fields are introduced.

## Row-Order Rules

- The active dataset exposes one current row sequence. Source order is the initial sequence.
- `head n` returns the first `n` rows in sequence order; `tail n` returns the last `n` rows in
  sequence order, restored to their original relative order. `head 0` and `tail 0` return no rows.
- `keep if` retains matching rows in their prior relative order. `drop if` removes matching rows and
  retains the rest in their prior relative order.
- False and missing filter results follow the existing predicate contract and never reorder retained
  rows.
- `select`, `keep`/`drop` column projection, `rename`, `generate`, `replace`, and `recode` preserve
  the current row sequence when they succeed.
- Grouped or relation-changing commands such as `collapse`, append, join, and reshape establish
  their own result sequence; this slice does not redefine their later preview order.
- Eager, DuckDB-lazy, and Polars-lazy paths produce the same row sequence for this supported surface.

## Data And Execution Assumptions

- The active dataset must exist and referenced variables must exist, following current errors.
- DuckDB explicitly enables insertion-order preservation for preview/filter queries; Polars lazy
  frames use their native sequence-preserving `head`, `tail`, and `filter` operations.
- Missing conditions use the already defined keep/drop behavior; no additional missing syntax is
  introduced.
- Collapse, append/join/reshape order, named-table storage order, arbitrary SQL `order by`,
  categorical order, and a new sort command remain outside this slice.

## Acceptance Criteria

- [x] Unsorted fixtures return identical head/tail rows across all three execution paths.
- [x] Keep/drop filters retain relative order and treat missing conditions consistently across paths.
- [x] Successful row-preserving transformations retain sequence order.
- [x] CLI/help/docs, full tests, type/lint/format checks, and integrated workflow checks pass.

## Non-Goals For This Slice

- New sort syntax or commands, row-ID persistence, append/join/reshape ordering, named-table order,
  arbitrary SQL ordering, categorical ordering, or estimators.
