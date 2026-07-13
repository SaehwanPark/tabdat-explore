# Product Contract: Phase 24 P0 — Categorical Ordering

## Request Summary

Make existing `tabulate` and `bar` category ordering and missing-label behavior predictable without
adding category-management syntax.

## Roadmap Phase

Phase 24 P0: stable language semantics before broader command and estimator expansion.

## Roadmap Fit

This closes the basic label-order contract after grouped-result, active-row, SQL, append, join, and
reshape ordering. It does not introduce a categorical data model or user-defined levels.

## Existing Syntax

Valid forms retain the current grammar:

- `use source.parquet`
- `tabulate code, missing`
- `tabulate, rows(group_id) columns(code) missing`
- `bar code, missing noopen`

No new options, commands, result fields, or category metadata are introduced.

## Categorical-Order Rules

- Category labels use native scalar order: numeric values sort numerically, text values
  lexicographically, and booleans false before true. Numeric labels are not compared by rendered text.
- `tabulate` excludes missing categories by default. With `missing`, missing categories appear after
  all nonmissing categories in row keys and column headers.
- `bar` orders nonmissing categories by descending count, then native category order for ties. With
  `missing`, the missing category remains last and displays as `<missing>`.
- Source arrival order and user-defined category levels are not ordering contracts in this slice.
- Eager, DuckDB-lazy, and Polars-lazy tabulate/bar outputs agree; output formatting does not alter
  ordering.

## Data And Execution Assumptions

- Existing native type, missing-value, aggregate, percentage, and plotting behavior remains unchanged.
- Category labels are represented by existing scalar columns; no categorical metadata is persisted.
- Identifier spelling, expression coercion, active/reshape/relation order, and unordered SQL remain
  separate contracts.

## Acceptance Criteria

- [ ] Numeric, text, boolean, and missing category order follows the native policy.
- [ ] Tabulate missing omission/inclusion and missing-last placement are covered.
- [ ] Bar count/tie order and missing-last display are covered.
- [ ] Eager, DuckDB-lazy, and Polars-lazy outputs agree.
- [ ] CLI/help/docs, focused tests, full tests, type/lint/format checks, and integrated workflow
  checks pass.

## Non-Goals For This Slice

- New category metadata or level-management syntax, recoding changes, sort syntax, append/join/reshape
  ordering, unordered SQL guarantees, or estimators.
