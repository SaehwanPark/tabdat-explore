# Command Contract: `sort`

## Product and roadmap fit

`sort` is a stable, ascending active-row ordering command inspired by Stata `sort`, SAS `PROC SORT`,
and SPSS `SORT CASES BY`. It is TabDat-native and intentionally does not promise native compatibility.

## Syntax

```text
sort <varlist>
```

At least one existing column is required. Columns are sorted ascending in the order listed. The
command accepts no options, conditions, expressions, or assignment syntax.

## Semantics

- Requires an active dataset and at least one variable.
- Each sort key uses native scalar ordering: numeric values numerically, strings lexicographically,
  and booleans false before true. Nulls sort last for every key.
- Ties preserve the prior active row order (stable sort), including rows tied on all requested keys.
- Sorting does not change columns or values. Variable/value labels, panel metadata, and internal
  estimation-sample state remain attached to the active dataset.
- DuckDB eager/lazy and Polars-lazy execution agree on output order. Polars-lazy updates the lazy
  plan without converting the session to eager state.
- Unknown variables fail before the active dataset or metadata changes.
- A successful sort records `sort` as the last operation and reports the resulting dataset.

## Output

Human output:

```text
Sorted by: group age
Rows: 3, Columns: 4
```

The structured result is the existing `TransformResult` with message `Sorted by: <varlist>` and the
updated `DatasetInfo`; JSON therefore uses the existing transform result envelope.

## Examples

```text
use survey.parquet, lazy engine=polars
sort treatment age
head
```

## Invalid forms

- `sort`: parse error; a varlist is required.
- `sort age, stable` or `sort age if age > 0`: parse error.
- `sort missing_column`: execution error; active state is unchanged.

## Acceptance

- Parser tests cover ordered varlists, required arguments, and rejected options/conditions.
- Backend/executor tests cover numeric/text/boolean/null ordering, stable ties, metadata preservation,
  unknown-variable atomicity, and DuckDB/Polars-lazy behavior.
- CLI tests cover human output, JSON transform envelopes, and errors.
- Help, command reference/navigation, language semantics, command schema/effects, and shell completion
  are aligned.
- Validate with focused tests, full `pytest`, docs alignment, Ruff, formatting, basedpyright, and
  hosted CI.
