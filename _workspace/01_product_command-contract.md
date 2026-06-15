# Command Contract: Enhanced `tabulate`

## Roadmap Phase

- Core EDA refinement.
- Expands the existing Phase 3 `tabulate` command without adding a new command family.

## Syntax

```stata
tabulate <row_var> [column_var] [if <expr>] [, row col missing]
tabulate [if <expr>], rows(<row_vars>) [columns(<column_vars>)] [row col missing]
tabulate [if <expr>], rows(<row_vars>) [columns(<column_vars>)] values(<var>) stat(count|mean|sum|min|max) [missing]
by <group_vars>: tabulate ...
```

## Behavior

- Legacy one-way and two-way frequency forms remain valid.
- `rows()` and `columns()` support multi-level row/index and column dimensions.
- `if` filters rows before counting or aggregation.
- `missing` includes null row and column dimension values; null dimensions are excluded by default.
- `values()` and `stat()` must appear together and support exactly one value variable and one stat.
- Frequency is the default when `values()` is omitted.
- `stat(count)` with `values(x)` counts non-null `x`; `mean`, `sum`, `min`, and `max` require a
  numeric value variable.
- `row` and `col` percentages apply only to frequency tabulations with column variables.
- Wide output uses row/index variables on the left and sorted observed column-category
  combinations as flattened headers.
- `by:` prepends by variables and scopes frequency percentages within each by group.

## Non-Goals

- No `by(...)` option form.
- No multiple value variables or multiple stats per command.
- No margins, totals, weights, statistical tests, plotting, or export-specific formatting.

## Acceptance Criteria

- Existing `tabulate sex` and `tabulate sex outcome` still parse and execute.
- `tabulate sex if age >= 18` filters before tabulating.
- `tabulate, rows(region sex) columns(outcome year), row col` renders a wide frequency matrix.
- `tabulate, rows(region) columns(sex) values(cost) stat(mean)` renders mean `cost` per cell.
- `by region: tabulate, rows(sex) columns(outcome) values(cost) stat(sum)` executes without
  mutating the active dataset.
- Parser, executor/backend, CLI/help, shell completion, `basedpyright`, and `ruff` checks pass.
