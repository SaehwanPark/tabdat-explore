# TabDat-Explore

TabDat-Explore is a terminal-native exploratory data analysis tool for modern tabular data.
It is Stata-inspired in feel, but not Stata-compatible. The current implementation uses one active
dataset, a session-local named table registry, DuckDB for execution, and Parquet as the primary
input format.

## What It Does

TabDat-Explore is built for quick inspection and transformation of local datasets from the
command line. The current CLI supports:

- loading a local `.parquet` file with `use`
- inspecting structure with `describe`
- computing summaries with `summarize`
- column profiling with `codebook`
- row counts with `count`
- row previews with `head` and `tail`
- column selection and row filtering with `keep`, `drop`, and `select`
- renaming and deriving columns with `rename`, `generate`, and `replace`
- frequency tables with `tabulate`
- grouped aggregation with `collapse`
- grouped commands with `by <vars>: summarize ...` and `by <vars>: count`
- SQL escape-hatch queries with `sql`, where the active dataset is available as `active`
- session-local named tables with `sql ... into <table>` and `use <table>`
- artifact plots with `histogram`, `scatter`, and `bar`
- opt-in lazy Parquet loading with `use data.parquet, lazy`
- script execution with `tabdat -f analysis.td`, `tabdat analysis.td`, and `run analysis.td`
- project-local or explicit config for graph defaults
- runtime settings with `set graph_format`, `set artifact_dir`, and `set graph_open`
- Parquet persistence with `save` and `export`
- interactive shell UX with command history, inline history suggestions, syntax highlighting, and
  context-aware autocomplete

The repository has completed the first execution and state foundations slice of the roadmap.

## Quickstart

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Run the CLI against a Parquet file:

   ```bash
   uv run tabdat -c "use data.parquet" -c "describe" -c "summarize age bmi"
   ```

   For larger Parquet workflows, opt into lazy loading:

   ```bash
   uv run tabdat -c "use data.parquet, lazy" -c "keep if age >= 18" -c "summarize age bmi"
   ```

   `engine=polars` is currently accepted as an experimental metadata selector. Command execution
   still runs through the DuckDB relation boundary.

3. Run a script:

   ```bash
   uv run tabdat -f analysis.td
   uv run tabdat analysis.td
   ```

   Script files use one command per non-empty line. Whole-line `#` comments are ignored, and
   multiline `sql """..."""` blocks are supported.

4. Configure plot defaults when needed:

   ```toml
   # .tabdat.toml
   graph_format = "png"
   artifact_dir = "artifacts"
   graph_open = false
   ```

   Or load an explicit config:

   ```bash
   uv run tabdat --config project.tabdat.toml -f analysis.td
   ```

5. Persist a transformed dataset:

   ```bash
   uv run tabdat -c "use data.parquet" -c "keep if age >= 18" -c "save adults.parquet"
   ```

6. Start the interactive shell:

   ```bash
   uv run tabdat
   ```

   Then enter commands at the `tabdat>` prompt.

   The interactive shell uses command history at `~/.tabdat_history`, suggests prior commands
   inline, and completes command names, active dataset column names, common options, and lightweight
   SQL helpers.

## Example Session

```text
tabdat> use data.parquet
Loaded: data.parquet (3 rows, 4 columns)

tabdat> describe
Dataset: data.parquet
Rows: 3
Columns: 4

Variable  Type
age       INTEGER
bmi       DOUBLE
sex       VARCHAR
cost      DOUBLE

tabdat> summarize age bmi
Variable  Count  Mean  Std Dev  Min  Max
age       3      42    12       30   54
bmi       3      25    2.5      22.5  27.5

tabdat> sql select sex, avg(bmi) as mean_bmi from active group by sex order by sex
sex  mean_bmi
F    25
M    25

tabdat> sql select sex, count(*) as n from active group by sex into summary
Created summary: 2 rows, 2 columns

tabdat> use summary
Activated: summary (2 rows, 2 columns)

tabdat> histogram age
Saved plot: artifacts/plots/histogram-age.svg

tabdat> set graph_format png
Set graph_format: png

tabdat> save transformed.parquet
Saved: transformed.parquet (3 rows, 4 columns)

tabdat> run analysis.td
```

## Design Notes

- One active dataset remains the default command target, while session-local named tables let SQL
  `into` results be reactivated later with `use <table>`.
- DuckDB is the primary execution engine.
- Parquet is the primary data format.
- `use data.parquet` remains eager. `use data.parquet, lazy` creates a DuckDB Parquet scan view and
  reports the active lazy engine; `engine=duckdb|polars` can be supplied for explicit lazy-engine
  selection. The Polars selector is experimental until Polars-native command execution is designed.
- Lazy `use` validates readability and schema through DuckDB, but does not count rows at load time.
  Run `count` for a live row count. Transformations currently materialize the active relation after
  the first lazy transformation.
- SQL is an escape hatch, not the main interface. `sql ... into <table>` creates a session-local
  named table, makes it active, and does not persist a file.
- Plots are saved artifacts. Interactive sessions open generated plot files by default; batch
  `-c` and script runs only print the saved path.
- Default plot paths use `<artifact_dir>/plots/<command>-<vars>.<graph_format>`. Generated names
  are stable and may overwrite prior outputs; use `saving(...)` for explicit artifact paths.
- Runtime settings apply for the current session only. `.tabdat.toml` and `--config <path>` support
  `graph_format`, `artifact_dir`, and `graph_open`.
- `save <path>[, replace]` and `export <path>[, replace]` persist the active dataset as local
  Parquet. Existing files require `replace`.
- Scripts print deterministic run metadata, echo each command as `. <command>`, fail fast on the
  first error, and include file and line number diagnostics. Macros, loops, inline comments, and
  script-level conditionals are deferred.
- Named table registries are not persisted across CLI sessions; use `save` or `export` for durable
  Parquet output.
- Autocomplete is best-effort UX help. The parser and executor remain authoritative for validation
  and error messages.
- The terminal experience is part of the product, not an afterthought.

## Project Docs

- [Project proposal](docs/project_proposal.md)
- [Development roadmap](docs/dev_phase.md)
- [Phase 0 product guardrails](docs/phase0_product_guardrails.md)
- [Command glossary v0](docs/command_glossary_v0.md)
- [Architecture notes](ARCHITECTURE.md)
- [Spec status](SPEC.md)

## Validation

This repository uses `uv` for commands, `pytest` for tests, `mypy` for type checking, and `ruff`
for linting and formatting.

```bash
uv run mypy
uv run pytest
uv run ruff check .
uv run ruff format --check .
```
