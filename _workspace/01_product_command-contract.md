# Full Phase 3 Command Contract

## Request Summary

Complete the full roadmap Phase 3 core EDA surface over the active local Parquet dataset. Existing
Phase 1, Phase 2, and Phase 3 inspection behavior must continue to work.

## Roadmap Phase

Phase 3: Core EDA Functionality.

## Existing Inspection Syntax

- `codebook [varlist]`
- `count`
- `head [n]`
- `tail [n]`

Existing output and error behavior are preserved.

## Transformation Syntax

```text
keep varlist
keep if <expr>
drop varlist
drop if <expr>
select varlist
rename old new
generate new = <expr>
replace existing = <expr> [if <expr>]
```

- `keep varlist`, `drop varlist`, and `select varlist` update the active columns.
- `keep if <expr>` and `drop if <expr>` filter active rows.
- `rename old new` renames one column while preserving values and type.
- `generate` adds a new column and rejects existing column names.
- `replace` updates an existing column. With `if`, nonmatching rows keep the old value.

## Grouping And Tabulation Syntax

```text
tabulate var
tabulate var1 var2 [, row col missing]
collapse stat varlist, by(group_vars)
by group_vars: summarize [varlist]
by group_vars: count
```

- One-way `tabulate` outputs `Value`, `Count`, and `Percent`.
- Two-way `tabulate` outputs long-form rows with `var1`, `var2`, `Count`, and optional `Row %` or
  `Col %` columns.
- `missing` includes null values; otherwise null values are excluded.
- `collapse` replaces the active dataset with grouped aggregate output. Supported stats are
  `count`, `mean`, `sum`, `min`, and `max`. Aggregate columns are named `<stat>_<variable>`.
- `by:` grouped commands do not change the active dataset.

## Error Behavior

- All active-data commands require an active dataset and should say to run `use <path>` first.
- Commands reject unknown columns, duplicate output names, malformed arity, unsupported options, and
  unsupported expressions with user-facing errors.
- `generate` rejects existing target columns; `replace` rejects missing target columns.
- `collapse` requires exactly one supported stat and a nonempty `by(...)` option.
- `by:` supports `summarize` and `count` in this phase; other child commands are rejected.

## Data Assumptions

- The active dataset starts as a single local `.parquet` file loaded by `use`.
- Backend operations use DuckDB SQL over the current active relation query.
- Transformations are session-local and do not write a new file.
- Formatter renders null as `.`.

## Non-Goals

- No SQL command, scripting, visualization, prompt-toolkit UX, config, remote paths, non-Parquet
  loading, or persistent writes.
- No Phase 7 lazy execution optimization beyond DuckDB query composition.
- No full Stata compatibility.

## Acceptance Criteria

- Parser tests cover valid and invalid forms for all new Phase 3 commands.
- Executor/backend tests cover command sequencing after transformations, grouped summaries,
  tabulations, collapse, and failure cases.
- CLI smoke tests show a first-pass EDA flow after `use`.
- Existing Phase 1/2/inspection tests continue to pass.
- Validation passes:
  - `uv run pytest`
  - `uv run ruff check .`
  - `uv run ruff format --check .`
