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
- session-local panel metadata with `panel <id_var> <time_var>`, `panel`, and `panel clear`
- artifact plots with `histogram`, `scatter`, and `bar`
- opt-in lazy Parquet loading with `use data.parquet, lazy`
- script execution with `tabdat -f analysis.td`, `tabdat analysis.td`, and `run analysis.td`
- script-only `seed` metadata and `let` macros for reproducible scripts
- project-local or explicit config for graph defaults
- runtime settings with `set graph_format`, `set artifact_dir`, and `set graph_open`
- Parquet persistence with `save` and `export`
- linear regression with
  `regress <y> <xvars>[, robust cluster(<var>) noconstant wls(<weight_var>) gls(<sigma_var>)]`
- quantile regression with
  `qreg <y> <xvars>[, quantile(<0,1>) robust noconstant]`
- bounded panel-metadata DID with
  `did <y> [controls], treat(<var>) post(<var>) [robust]` after `panel <id_var> <time_var>`
- bounded dynamic-panel GMM starter with
  `xtabond <y> [xvars] [, robust]` after `panel <id_var> <time_var>`
- binary-choice logistic regression with
  `logit <y> <xvars>[, robust cluster(<var>) noconstant]`
- binary-choice probit regression with
  `probit <y> <xvars>[, robust cluster(<var>) noconstant]`
- limited-dependent Tobit regression with
  `tobit <y> <xvars>, ll(<num>) [ul(<num>) robust cluster(<var>) noconstant]`
- sample-selection Heckman-style regression with
  `heckman <y> <xvars>, selectdep(<var>) select(<vars>) [robust cluster(<var>) noconstant]`
- bounded nonlinear least-squares regression with
  `nl <y> = <expr>, params(<params>) start(<values>) [robust noconstant]`
- Poisson count regression with
  `poisson <y> <xvars>[, robust cluster(<var>) noconstant]`
- negative-binomial count regression with
  `nbreg <y> <xvars>[, robust cluster(<var>) noconstant]`
- zero-inflated Poisson count regression with
  `zip <y> <xvars>, inflate(<zvars>) [robust cluster(<var>) noconstant]`
- zero-inflated negative-binomial count regression with
  `zinb <y> <xvars>, inflate(<zvars>) [robust cluster(<var>) noconstant]`
- bounded parametric survival regression with
  `streg <time_var> <xvars>, failure(<event_var>) dist(weibull|exponential) [robust cluster(<var>) noconstant]`
- instrumental-variables regression with
  `ivregress 2sls|gmm <y> [exog_vars], endog(<var>) iv(<vars>)[, robust cluster(<var>) noconstant]`
- control-function regression with
  `cfregress <y> [exog_vars], endog(<var>) iv(<vars>)[, robust cluster(<var>) noconstant]`
- panel regression with
  `xtreg <y> <xvars>, fe|re[, robust cluster(<var>)]` after `panel <id_var> <time_var>`
- panel-data transforms with
  `xtdata <varlist>, within|between` after `panel <id_var> <time_var>`
- prediction workflows with `predict <newvar>[, xb residuals pr]`
- post-estimation diagnostics with
  `estat <residuals|ovtest|vif|firststage|overid|hausman|endogenous|margins|gof|did>`
- interactive shell UX with command history, inline history suggestions, syntax highlighting, and
  context-aware autocomplete

The repository has completed the first three Phase 13 linear-econometrics slices on top of the
Phase 12 estimation substrate, completed thirteen Phase 14 slices, and delivered seven bounded
Phase 15 slices (`logit`, `probit`, `estat margins`, binary `predict` routing, `tobit`, `heckman`,
and `nl`), plus four bounded Phase 16 slices: count-model workflows (`poisson`, `nbreg`, `zip`,
`zinb`) and the first duration/survival workflow (`streg`).

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

   Script files use one command per non-empty line. Whole-line `#` comments are ignored,
   multiline `sql """..."""` blocks are supported, and script-local `seed <integer>` plus
   `let <name> = <value>` directives can make runs easier to reproduce.

   ```stata
   seed 123
   let data = patients.parquet
   use $data
   ```

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

tabdat> panel sex age
Panel set: id=sex, time=age

tabdat> panel
Panel: id=sex, time=age

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
- Panel metadata is session-local and data-only commands do not write it into saved Parquet files.
  The active id/time pair must have no missing values and must uniquely identify rows.
- Plots are saved artifacts. Interactive sessions open generated plot files by default; batch
  `-c` and script runs only print the saved path.
- Default plot paths use `<artifact_dir>/plots/<command>-<vars>.<graph_format>`. Interactive shell
  reruns avoid collisions with `-2`, `-3`, and later suffixes, while batch and script runs keep
  the stable unsuffixed default path. Use `saving(...)` for explicit artifact paths.
- Runtime settings apply for the current session only. Startup config precedence is
  `--config <path>`, then project-local `.tabdat.toml`, then XDG user config at
  `~/.config/tabdat/config.toml` or `$XDG_CONFIG_HOME/tabdat/config.toml`.
  These config files support `graph_format`, `artifact_dir`, and `graph_open`.
- `save <path>[, replace]` and `export <path>[, replace]` persist the active dataset as local
  Parquet. Existing files require `replace`.
- `regress` currently fits OLS/WLS/GLS through `statsmodels` and supports `robust`,
  `cluster(<var>)`, `noconstant`, `wls(<weight_var>)`, and `gls(<sigma_var>)`.
- `predict` writes fitted values (`xb`) or residuals into a new active-dataset column using the
  latest `regress`/`qreg`/`cfregress`/`nl` model state, supports `xb` after `did`, and supports
  `pr` (plus `xb`) after `logit`/`probit`.
- `tobit` currently provides a bounded limited-dependent path with required `ll(...)`, optional
  `ul(...)`, and covariance modes (`nonrobust`, `robust`, `cluster(...)`) through an R adapter
  boundary (`survival::survreg` via `rpy2`).
- `heckman` currently provides a bounded sample-selection path with required `selectdep(...)`,
  required `select(...)`, and covariance modes (`nonrobust`, `robust`, `cluster(...)`) with
  deterministic outcome/selection equation output.
- `estat` currently provides:
  - linear-model diagnostics (`residuals`, `ovtest`, `vif`) over the latest `regress` state
  - quantile residual diagnostics (`residuals`) over the latest `qreg` state
  - IV diagnostics (`firststage`, `overid`, `endogenous`) over the latest `ivregress` state
  - panel model comparison (`hausman`) over matching latest `xtreg` FE/RE states
  - control-function endogenous diagnostics (`endogenous`) over the latest `cfregress` state
    with deterministic residual-inclusion metrics:
    `test`, `estimate`, `std_error`, `statistic`, `p_value`, `ci_level`, `ci_lower`, `ci_upper`,
    `distribution`, and `df`
  - DID post-estimation interaction diagnostics (`did`) over the latest `did` state
- `ivregress` currently provides Python-first IV/2SLS and IV-GMM paths via `linearmodels` with
  `endog(...)`, `iv(...)`, `robust`, `cluster(...)`, and `noconstant`.
- `estat endogenous` after `ivregress` is currently scoped to prior `ivregress 2sls` fits and
  reports Durbin/Wu-Hausman diagnostics.
- `cfregress` currently provides a bounded two-step control-function path (first-stage endogenous
  fit plus second-stage outcome fit with residual inclusion) for one endogenous variable.
- `xtreg` currently provides Python-first `linearmodels` FE/RE estimation with `robust` and
  `cluster(...)` covariance options; `estat hausman` currently supports non-cluster FE/RE pairs.
- `xtdata` currently provides panel-index-aware within/between transforms for numeric variables and
  appends deterministic `<var>_within` or `<var>_between` columns.
- `xtabond` currently provides a bounded dynamic-panel AR(1) GMM starter with nonrobust/robust
  covariance modes. The Python IV-GMM path is primary; an R-backed fallback path is available when
  Python fitting fails.
- Scripts print deterministic run metadata, echo each expanded command as `. <command>`, fail fast
  on the first error, and include file and line number diagnostics. `seed <integer>` records
  script-run metadata, and `let <name> = <value>` defines plain text macros that expand as `$name`
  in later script entries and nested `run` scripts. Loops and inline comments are deferred, while
  script-level `if` / `else` / `end` conditionals are supported.
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
