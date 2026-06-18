# Command Contract: Phase 23 — Data Recoding & Ingestion Expansion

## Request Summary

Implement the data transformation command `recode` and expand file loading format support in the `use` command to include CSV, Feather, and Arrow formats.

## Roadmap Phase

Phase 23: Data Recoding & Ingestion Expansion.

## Command Syntax

### 1. `recode` Command
```stata
recode <varlist> (<rule>) [ (<rule>) ...] [, generate(<new_varlist>) replace]
```

Where:
- `<varlist>` is a list of existing numeric or categorical variables in the active dataset.
- Each `(<rule>)` is in the format: `(inputs = output)`.
  - Inputs can be single values (e.g. `1`), space-separated lists of values (e.g. `1 2 3`), ranges (e.g. `1/5`), or special keywords (`min`, `max`, `missing`, `nonmissing`, `else`).
  - Examples of rule inputs:
    - `1 = 0`
    - `1 2 3 = 4`
    - `1/5 = 10`
    - `min/17 = 0`
    - `18/max = 1`
    - `missing = -1`
    - `nonmissing = 1`
    - `else = 99`
- Options:
  - `generate(<new_varlist>)`: Specifies a list of new variables to create. Must have the exact same number of variables as `<varlist>`.
  - `replace`: Recodes the variables in-place.
  - Exactly one of `generate()` or `replace` must be specified.

### 2. `use` Command Options
```stata
use <path> [, lazy engine(duckdb|polars) delimiter(<char>) has_header(true|false)]
```
- `<path>` can end with `.csv`, `.feather`, `.arrow`, in addition to `.parquet` and `.dta`.
- `delimiter(<char>)` and `has_header(...)` are only supported when `<path>` ends with `.csv`.

## Examples

- `recode age (min/17 = 0) (18/max = 1), generate(adult)`
- `recode score (90/100 = 4) (80/89 = 3) (70/79 = 2) (else = 1), replace`
- `use survey.csv, delimiter(",") has_header(true)`
- `use remote_dataset.feather`

## Data Assumptions

- Variables in `recode` must exist in the active dataset.
- Target columns in `generate` must not already exist in the active dataset (collision check).
- Lazy loading is still restricted to Parquet. E.g., `use dataset.csv, lazy` raises `ExecutionError`.

## Execution Semantics

### `recode` Command
- Translates the user-specified rules into a SQL `CASE WHEN` expression:
  - `(1 = 2)` -> `WHEN col = 1 THEN 2`
  - `(1 2 3 = 4)` -> `WHEN col IN (1, 2, 3) THEN 4`
  - `(1/5 = 10)` -> `WHEN col >= 1 AND col <= 5 THEN 10`
  - `(min/17 = 0)` -> `WHEN col <= 17 THEN 0`
  - `(18/max = 1)` -> `WHEN col >= 18 THEN 1`
  - `(missing = -1)` -> `WHEN col IS NULL THEN -1`
  - `(nonmissing = 1)` -> `WHEN col IS NOT NULL THEN 1`
  - `(else = 99)` -> `ELSE 99`
- Rules are evaluated sequentially in the order specified.
- For categoricals / strings, range-based rules (`/`) are not allowed and will raise an error.
- Updates the active dataset in DuckDB.

### `use` Command Expansion
- Resolves file extension of `<path>`.
- For `.csv` files:
  - Passes delimiter and header options directly to DuckDB's `read_csv_auto`.
- For `.feather` and `.arrow` files:
  - Reads using PyArrow or Pandas, registers the resulting structure as a DuckDB temporary view/table.

## Acceptance Criteria

- [ ] `recode` correctly performs transformations on active datasets.
- [ ] Variables list and generated list match in size.
- [ ] In-place `replace` updates the existing columns.
- [ ] `use` successfully loads CSV, Feather, and Arrow files (both local and remote HTTP/HTTPS).
- [ ] Mismatched options or formats raise clear `ExecutionError` messages.
