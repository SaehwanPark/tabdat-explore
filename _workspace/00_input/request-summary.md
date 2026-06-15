# Request Summary: Enhanced `tabulate`

## Goal

Implement enhanced tabulation for one-way and two-way use cases, multi-level row/index and column
dimensions, command-level `if`, `by:` grouping, and cells populated by a single aggregate of a
value variable instead of only frequencies.

## Selected Scope

- Preserve existing `tabulate sex` and `tabulate sex outcome` syntax.
- Add explicit `rows()` and `columns()` syntax for multi-level crosstabs.
- Add `values(<var>) stat(count|mean|sum|min|max)` for aggregate cells.
- Support `if`, `missing`, row/column percentages for frequency tabulations, and
  `by <vars>: tabulate ...`.

## Non-Goals

- No `by(...)` option form.
- No multiple value variables or multiple statistics.
- No margins, totals, weights, statistical tests, plotting, or export-specific formatting.
