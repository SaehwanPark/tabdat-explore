# Command Contract: `missing`

## Product and roadmap fit

`missing` is a compact, TabDat-native data-quality report inspired by Stata's `misstable summarize`
and the missingness/frequency workflows analysts use in SAS and SPSS. It is a bounded terminal-EDA
feature, not a native compatibility layer.

## Syntax

```text
missing [varlist]
```

With no varlist, all active dataset columns are reported in schema order. With a varlist, columns are
reported in exactly the order requested. The command accepts no options, conditions, or assignment
syntax.

## Semantics

- Requires an active dataset.
- A missing value is an explicit null under TabDat's existing missingness policy; empty strings and
  user-defined numeric sentinel codes are not treated as missing by this command.
- Each requested column reports total rows, missing rows, nonmissing rows, and missing percentage.
- `missing percentage = missing / total * 100`; an empty dataset reports `0.0` percent rather than
  dividing by zero.
- Unknown variables fail before any result is returned and leave active data/session state unchanged.
- The result preserves requested/schema column order and is deterministic for a fixed active relation.
- DuckDB eager/lazy and Polars-lazy execution return the same rows. Polars-lazy computes the aggregate
  without switching execution mode or replacing the lazy frame; the command may scan source data but
  does not force materialization into eager state.
- Existing `codebook`, filtering, and estimator missingness behavior is unchanged.

## Structured result

Human output is a table with these columns:

```text
Variable  Type  Total  Missing  Nonmissing  Missing %
```

JSON emits a versioned `MissingResult` envelope whose rows contain:

```json
{
  "variable": "age",
  "data_type": "INTEGER",
  "total": 5,
  "missing": 1,
  "nonmissing": 4,
  "missing_percent": 20.0
}
```

## Examples

```text
use survey.parquet, lazy engine=polars
missing
missing age income
```

## Invalid forms

- `missing, ...` or `missing if ...`: parse error.
- `missing age, ...`: parse error.
- `missing unknown_column`: execution error.
- `missing` without an active dataset: execution error.

## Acceptance

- Parser tests cover no varlist, ordered varlists, and rejected options/conditions.
- Backend/executor tests cover eager results, empty datasets, unknown variables, DuckDB-lazy and
  Polars-lazy execution, and unchanged lazy execution state.
- CLI tests cover human output, JSON result envelopes, and error behavior.
- Help, command reference/navigation, command schema, shell completion, and declared read effect are
  aligned.
- Validate with focused tests, full `pytest`, docs alignment, Ruff, formatting, basedpyright, and
  hosted CI.
