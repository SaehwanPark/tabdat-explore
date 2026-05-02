# Phase 1 Command Contract

## Request Summary

Implement the Phase 1 core skeleton: a minimal `tabdat` CLI that supports loading one local
Parquet dataset and running `describe` and `summarize` through the CLI -> parser -> executor ->
DuckDB pipeline.

## Roadmap Phase

Phase 1: Core Skeleton (Vertical Slice).

## Commands

### `use`

Syntax:

```text
use <path>
```

Behavior:

- Loads a local `.parquet` file into the single active dataset slot.
- Replaces any previously active dataset.
- Prints a confirmation with path, row count, and column count.
- Errors when the path is missing, the file extension is not `.parquet`, or DuckDB cannot read
  the file.

Example:

```text
tabdat> use patients.parquet
Loaded: patients.parquet (3 rows, 4 columns)
```

### `describe`

Syntax:

```text
describe
```

Behavior:

- Requires an active dataset.
- Prints dataset path, row count, column count, and one line per column with the DuckDB type name.
- Does not accept a varlist or options in Phase 1.

Example:

```text
tabdat> describe
Dataset: patients.parquet
Rows: 3
Columns: 4

Variable  Type
age       BIGINT
bmi       DOUBLE
sex       VARCHAR
cost      DOUBLE
```

### `summarize`

Syntax:

```text
summarize [varlist]
```

Behavior:

- Requires an active dataset.
- With no varlist, summarizes all numeric columns.
- With a varlist, summarizes exactly the requested columns.
- Prints variable, non-null count, mean, standard deviation, minimum, and maximum.
- Errors when any requested column is missing or non-numeric.
- Errors when no numeric columns are available for the no-varlist form.

Example:

```text
tabdat> summarize age bmi
Variable  Count  Mean  Std Dev  Min  Max
age       3      42.0  12.0     30   54
bmi       3      25.1  2.1      22.8 27.0
```

## Parser Rules

- Parse only whitespace-separated Phase 1 commands.
- Supported commands are `use`, `describe`, `summarize`, `exit`, and `quit`.
- Reject unknown commands with a command-level error.
- Reject unsupported extra arguments for `describe`, `exit`, and `quit`.
- Options, quoted paths with spaces, `if` clauses, and comma syntax are future work.

## Data Assumptions

- The active dataset is a local Parquet file.
- DuckDB is the primary execution backend.
- Column types use DuckDB names in Phase 1 output.
- Numeric summaries include DuckDB numeric type families: integer, decimal, floating point, and
  unsigned integer types.

## Non-Goals

- No CSV, Feather, Arrow IPC, remote paths, object storage, SQL command, visualization, transforms,
  autocomplete, history, or syntax highlighting.
- No Stata-compatible edge behavior.
- No custom pretty table library in Phase 1.

## Acceptance Criteria

- `tabdat` is installed as a console script by the package.
- Parser tests cover valid and invalid Phase 1 command strings.
- Backend/executor tests cover loading, description, summaries, missing active dataset, missing
  columns, and non-numeric column errors.
- CLI smoke tests exercise user-visible command execution.
- Validation passes:
  - `uv run pytest`
  - `uv run ruff check .`
  - `uv run ruff format --check .`
