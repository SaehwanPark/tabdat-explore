# Loading Data & Diagnostics

TabDat is format-agnostic and Parquet-first, supporting both eager in-memory loading and lazy scan execution.

---

## Supported Formats

| Format | Syntax Example | Notes |
|---|---|---|
| **Parquet** | `use data.parquet` | Native primary format; supports lazy execution. |
| **Stata `.dta`** | `use auto.dta` | Reads Stata 13-118 `.dta` files (local or remote `https://...`). |
| **CSV** | `use data.csv, delimiter(",") has_header(true)` | Configurable delimiters, headers, and type inference. |
| **Feather** | `use data.feather` | Fast Arrow IPC format. |
| **Arrow** | `use data.arrow` | Apache Arrow streaming format. |

---

## Eager vs. Lazy Loading

### Eager Loading (Default)
`use data.parquet` loads the dataset immediately into memory, scans rows, and displays the exact row and column count.

### Lazy Loading
`use data.parquet, lazy` establishes a deferred query plan over the Parquet file without scanning all rows upfront:

```text
tabdat> use large_dataset.parquet, lazy engine=duckdb
Active dataset: large_dataset.parquet (lazy scan)
```

- In lazy mode, row count computation is deferred until `count` or an explicit materializing operation is run.
- The first transformation or estimation command automatically materializes the required relation.

---

## Missingness Overview (`missing`)

Use `missing` for a compact null-missingness scan before filtering or modeling:

```text
tabdat> missing age income
Variable  Type     Total  Missing  Nonmissing  Missing %
age       INTEGER  100    4        96          4
income    DOUBLE   100    12       88          12
```

With no varlist, every active column is reported in schema order. The command treats explicit nulls
as missing; empty strings and user-defined sentinel values remain nonmissing. A Polars-lazy session
stays lazy while the aggregate scan runs. Use `codebook` for distinct counts and examples.

## Quality Gates (`assert`)

Use `assert` to validate a boolean condition across every active row without changing the dataset:

```text
tabdat> assert age >= 0
assertion passed: 100 rows
```

False or missing predicate results fail the check with deterministic checked/failed counts. Empty
active datasets pass; options, `if` clauses, assignment, and row-level diagnostics are intentionally
not supported. Aggregate checks preserve Polars-lazy execution.

## Ordering Rows (`sort`)

Arrange the active rows by stable ascending native keys before previewing or exporting:

```text
tabdat> sort treatment age
Sorted by: treatment age
```

Nulls sort last and ties preserve their previous row order. The command preserves labels and panel
metadata; descending or expression-based ordering remains available through SQL.

## Inspecting Execution State (`status`)

Run `status` at any time to inspect backend execution mode, materialization status, and active relation details without triggering computation:

```text
tabdat> status
Backend: duckdb
Source: large_dataset.parquet
Active table: none
Last operation: use
Execution mode: lazy
Lazy engine: duckdb
Materialization: deferred
Last materialization reason: none
Rows: unknown
Columns: 14
```

---

## Capability Diagnostics (`doctor`)

Run `doctor` to check installed optional libraries, engine versions, and environment capability:

```text
tabdat> doctor
TabDat 0.24.1 Environment Diagnostics

Core Capabilities:
  DuckDB        ✓ duckdb 1.4.3
  PyArrow       ✓ pyarrow 24.0.0
  Polars        ✓ polars 1.36.1
  Plotting      ✓ altair 6.1.0, matplotlib 3.10.9

Statistics:
  statsmodels   ✓ statsmodels 0.14.6
  linearmodels  ✓ linearmodels 7.0
  scipy         ✓ scipy 1.15.0

Optional Capabilities:
  ML            ✓ sklearn 1.7.0
  Bayesian      ✓ bambi 0.18.0
  Spatial       ✓ spreg 1.4.0, libpysal 4.14.1
  R             ✓ rpy2 3.6.4, R binary at /opt/homebrew/bin/R

System:
  Python        ✓ 3.13.2
  Platform      ✓ Darwin (arm64)
```

In automated CI/CD pipelines, `tabdat --json doctor` produces machine-readable diagnostic envelopes.
