# Phase 3 Inspection Command Contract

## Request Summary

Implement the first Phase 3 core EDA slice: executable inspection commands over the active local
Parquet dataset. Existing Phase 1 and Phase 2 parser behavior must continue to work.

## Roadmap Phase

Phase 3: Core EDA Functionality.

## Command Syntax

### `codebook`

```text
codebook [varlist]
```

Shows compact column-level profiling for the active dataset. With no varlist, profile every column.
With a varlist, profile only the requested columns in requested order.

Output columns:

- `Variable`
- `Type`
- `Nonmissing`
- `Missing`
- `Distinct`
- `Examples`

Examples should be deterministic, non-null values from the dataset scan order, limited to a compact
display string.

### `count`

```text
count
```

Shows the number of rows in the active dataset.

### `head`

```text
head [n]
```

Shows the first `n` rows from the active dataset. `n` defaults to 5 and must be a non-negative
integer.

### `tail`

```text
tail [n]
```

Shows the last `n` rows from the active dataset using the backend's stable row-number ordering for
the active local Parquet scan. `n` defaults to 5 and must be a non-negative integer.

## Error Behavior

- All commands require an active dataset and should say to run `use <path>` first.
- `codebook` rejects unknown variables.
- `count` rejects arguments, `if` clauses, and options.
- `head` and `tail` reject more than one argument, non-integer limits, negative limits, `if`
  clauses, and options.
- `codebook`, `head`, and `tail` do not support filters or comma options in this slice.

## Data Assumptions

- The active dataset remains a single local `.parquet` file loaded by `use`.
- Backend operations use DuckDB queries over `read_parquet(?)`.
- Preview rows may contain scalars, strings, or nulls; formatter renders null as `.`.

## Non-Goals

- No row filters for `count`, `head`, `tail`, or `codebook`.
- No transformations, grouping, SQL, scripting, visualization, prompt-toolkit UX, non-Parquet
  loading, remote paths, or lazy execution optimization.
- No full Stata compatibility.

## Acceptance Criteria

- Parser tests cover valid and invalid forms for `codebook`, `count`, `head`, and `tail`.
- Executor/backend tests cover successful command execution and missing-dataset or missing-column
  failures.
- CLI smoke tests show the new commands running after `use`.
- Existing Phase 1/2 tests continue to pass.
- Validation passes:
  - `uv run pytest`
  - `uv run ruff check .`
  - `uv run ruff format --check .`
