# TabDat User Guide

This guide explains how TabDat behaves in everyday use: sessions, data loading, scripts,
configuration, plots, and estimation workflows. For a categorized command list, see
[command-reference.md](command-reference.md). For implementation boundaries, see
[ARCHITECTURE.md](../ARCHITECTURE.md).

## Sessions and the data model

TabDat works with **one active dataset** at a time. Most commands read from and write to that
dataset.

You can also keep **session-local named tables** in memory. When SQL creates a result with
`into <table>`, that table becomes active and can be reactivated later with `use <table>`.
Named tables do not persist across CLI sessions — use `save` or `export` for durable output.

**Panel metadata** (`panel <id_var> <time_var>`) is also session-local. It is not written into
saved Parquet files. The id/time pair must have no missing values and must uniquely identify rows.
Panel-aware commands such as `xtreg`, `did`, and `xtabond` require panel metadata first.

## Loading data

### Supported formats

`use` loads local or remote datasets:

- **Parquet** (primary format)
- **Stata `.dta`** (including HTTP/HTTPS URLs)
- **CSV** with `delimiter(<char>)` and `has_header(true|false)`
- **Feather** and **Arrow**

### Eager vs lazy loading

- `use data.parquet` loads eagerly and reports row counts immediately.
- `use data.parquet, lazy` creates a scan view without counting rows at load time. Run `count`
  when you need a live row count.
- Lazy mode is Parquet-only. After the first transformation on a lazy dataset, the active relation
  is materialized.
- `engine=duckdb|polars` can be supplied with lazy loading. The Polars selector is experimental;
  command execution still runs through the DuckDB relation boundary.

### Inspecting execution state

Use `status` to inspect the current execution boundary without running a data operation:

```text
tabdat> use data.parquet, lazy engine=duckdb
tabdat> status
Backend: duckdb
Source: data.parquet
Active table: none
Last operation: use
Execution mode: lazy
Lazy engine: duckdb
Materialization: deferred
Last materialization reason: none
Rows: unknown
Columns: 4
```

The command is read-only. After `count`, the known row count and `Last operation: count` are
reflected in a later `status`; repeated `status` calls leave the last operation unchanged. If an
unsupported Polars-lazy command falls back to eager execution, status reports
`Last materialization reason: polars fallback`; a successful `use`, named-table activation, or
`sql ... into <table>` resets it to `none`. Full DuckDB-lazy operations that become eager report
`Last materialization reason: eager operation`.
Full operation lineage, active-operation progress, and retained estimation samples remain planned
for later transparency work.

### Named tables

```text
sql select sex, avg(bmi) as mean_bmi from active group by sex into summary
use summary
```

`sql ... into <table>` creates a session-local named table, makes it active, and does not write a
file. An explicit `order by` sequence is preserved; `use <table>` restores that sequence. Add
tie-breaker keys when ordered values can tie.

## Scripts

TabDat scripts use the `.td` extension. Run them with:

```bash
uv run tabdat -f analysis.td
uv run tabdat analysis.td
```

Or from the interactive shell:

```text
run analysis.td
```

### Script rules

- One command per non-empty line.
- Whole-line `#` comments are ignored.
- Multiline `sql """..."""` blocks are supported.
- Scripts print deterministic run metadata, echo each expanded command as `. <command>`, and
  fail fast on the first error with file and line number diagnostics.
- Script-level `if` / `else` / `end` conditionals are supported. Loops and inline comments are
  not yet available.

For automation, add `--json` to non-interactive execution:

```bash
uv run tabdat --json -c "use data.parquet" -c "count"
uv run tabdat --json -f analysis.td
```

This writes one versioned JSON object per successful result, one per line, and suppresses script
metadata and command echoes. Missing values are `null`; exact decimal values are lossless strings;
non-finite floats are `null`; bytes are `base64:<payload>` strings; and errors keep the existing stderr
text and nonzero exit status while adding one error envelope with a stable type/message and script
location when available. Interactive sessions remain terminal-only.

### Canonical Parquet-first workflow

The repository includes a complete first-pass EDA journey in
[`demos/canonical_parquet_eda.td`](../demos/canonical_parquet_eda.td). It expects a Titanic-shaped
Parquet file with `age`, `fare`, `sibsp`, `parch`, and `class` columns, then lazily loads the data,
inspects structure and missingness, filters and derives a variable, summarizes overall and by
class, collapses to class-level means, and exports a Parquet summary.

The default source path is an ignored integrated-test fixture. From a clean checkout, prepare it
and run the complete replay benchmark with:

```bash
uv run python integrated_testing/run_e2e.py s6_canonical_parquet_workflow
```

Once the fixture exists, run the tracked script directly with `uv run tabdat -f
demos/canonical_parquet_eda.td`; edit its `source` macro for another local Parquet file with the
same five-column minimum schema.

The integrated acceptance harness prepares the public sample, runs this same script twice, compares
the transcripts and exported rows, and records wall-clock timings. Those timings are observations
for product-readiness work, not a portability guarantee.

### Reproducibility helpers

Script-only directives:

```stata
seed 123
let data = patients.parquet
use $data
```

- `seed <integer>` records script-run metadata.
- `let <name> = <value>` defines plain-text macros that expand as `$name` in later script lines
  and nested `run` scripts.

## Configuration

Runtime settings apply for the current session only:

```text
set graph_format png
set artifact_dir artifacts
set graph_open false
```

Startup config precedence:

1. `--config <path>`
2. Project-local `.tabdat.toml`
3. XDG user config at `~/.config/tabdat/config.toml` or `$XDG_CONFIG_HOME/tabdat/config.toml`

Supported config keys: `graph_format`, `artifact_dir`, and `graph_open`.

Example project config:

```toml
# .tabdat.toml
graph_format = "png"
artifact_dir = "artifacts"
graph_open = false
```

Load an explicit config when running scripts:

```bash
uv run tabdat --config project.tabdat.toml -f analysis.td
```

## Plots and artifacts

Plot commands (`histogram`, `scatter`, `bar`, `bayesplot`) save files rather than rendering inline
in the terminal.

- **Interactive shell**: generated plot files open by default (unless `graph_open` is false).
- **Batch `-c` and script runs**: only the saved path is printed.

Default paths follow `<artifact_dir>/plots/<command>-<vars>.<graph_format>`. Interactive reruns
avoid collisions with `-2`, `-3`, and later suffixes. Batch and script runs keep the stable
unsuffixed path. Use `saving(...)` for an explicit artifact path.

## SQL escape hatch

SQL is available when TabDat commands are not enough. The active dataset is exposed as `active`:

```text
sql select sex, avg(bmi) as mean_bmi from active group by sex order by sex
```

Prefer TabDat commands for routine EDA. Use SQL for ad hoc queries and aggregations that do not
yet have a dedicated command.

## Persistence

```text
save output.parquet
export output.parquet
```

Both write the active dataset as local Parquet. Existing files require the `replace` option.

## Estimation workflows

A typical modeling flow:

1. Load and prepare data (`use`, `keep`, `generate`, …).
2. Fit a model (`regress`, `logit`, `ivregress`, …).
3. Inspect fit (`estat vif`, `estat residuals`, …).
4. Generate predictions (`predict yhat, xb`).

### Post-estimation highlights

- `predict` writes fitted values (`xb`), residuals, probabilities (`pr`), spatial-lag values,
  or Bayesian posterior predictive draws depending on the latest model.
- `estat` subcommands vary by model type. Run `help estat` for the current list.
- `estat report` after `regress` produces a self-contained HTML report with coefficient tables
  and diagnostic plots.

### Panel workflows

```text
panel id year
xtreg y x, fe
estat hausman
```

Set panel metadata before `xtreg`, `xtdata`, `xtlogit`, `xtabond`, or panel-scoped `did`.

## Getting help

TabDat ships in-application help for each command:

```text
help use
help regress
help estat
```

In the interactive shell, run `help` with no arguments to browse topics when a name is ambiguous.
Outside the interactive shell, `help` requires a command name:

```bash
uv run tabdat -c "help summarize"
```

Autocomplete, command history (`~/.tabdat_history`), and inline history suggestions are
best-effort UX helpers. The parser and executor remain authoritative for validation and errors.

## Interactive shell

Start the shell with:

```bash
uv run tabdat
```

At the `tabdat>` prompt you get syntax highlighting, context-aware autocomplete (command names,
column names, common options), and command history.

## See also

- [Command reference](command-reference.md) — categorized command index
- [Language semantics](language-semantics.md) — stable identifiers, missing values, expression
  coercion and arithmetic results, write-target, and atomic-failure policy
- [Project proposal](project_proposal.md) — product vision and target users
- [CHANGELOG.md](../CHANGELOG.md) — release history
- [ARCHITECTURE.md](../ARCHITECTURE.md) — technical design for contributors
