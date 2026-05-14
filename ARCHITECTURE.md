# TabDat-Explore Architecture

TabDat-Explore has completed roadmap Phase 12 estimation substrate work, completed Phase 13 core
linear econometrics with three `regress`/`predict`/`estat` slices, implemented thirteen Phase 14
slices (`ivregress` `2sls`/`gmm`, IV diagnostics including `estat endogenous` after `2sls`, panel
FE/RE starter, `xtdata` transforms, `cfregress` core, and `predict` plus `estat endogenous`
support after `cfregress`, plus `estat firststage` after `cfregress` and expanded panel report
semantics), and delivered three bounded Phase 15 slices (`logit`, `probit`, and `estat margins`).
This document records the
implemented shell UX, script
runner, command-language model, active DuckDB relation model, session-local named table registry,
lazy and remote load boundary, runtime configuration, plot artifact boundary, persistence boundary,
join, append, reshape, panel metadata, and script primitive boundaries, and the boundaries future
phases should preserve.

## Runtime Flow

```text
CLI Shell / prompt-toolkit UX
  -> Script Runner when executing files
  -> Command Parser
  -> Executor
  -> DuckDB Backend / Lazy Scan Boundary
  -> Visualization Artifact Renderer
  -> Formatter
  -> Terminal Output
```

## Component Responsibilities

### CLI Shell

Owns user interaction, command input, script entry points, and terminal output formatting.
Interactive shell UX lives in `src/tabdat/shell.py` and uses prompt-toolkit for history, inline
history suggestions, syntax highlighting, and context-aware completions. Repeated `-c` commands
bypass prompt-toolkit and remain the smoke-testable batch workflow. Script execution is available
through `tabdat -f <script>`, `tabdat <script>`, and `run <script>`. Config loading happens at
CLI startup from `--config <path>`, otherwise project-local `.tabdat.toml`, otherwise XDG user
config at `~/.config/tabdat/config.toml` or `$XDG_CONFIG_HOME/tabdat/config.toml`.

### Script Runner

Owns UTF-8 script file reads, line-oriented script parsing, script-local directive state,
deterministic metadata output, command echoes, nested `run` path resolution, recursion rejection,
and file/line diagnostics. Script files support whole-line `#` comments, blank lines, one command
per line, multiline SQL blocks, script-only `seed <integer>` metadata, script-only
`let <name> = <value>` macros, and minimal non-nested `if` / `else` / `end` conditionals. `$name`
macro expansion happens at the script edge before command parsing, condition evaluation, or
execution. Nested `run` scripts share the parent script's macro and seed state, while each
top-level script run starts with empty directive state. Script execution shares one executor state
and disables plot auto-open so runs are reproducible in batch contexts.

### Command Parser

Converts command text into internal command objects. The parser owns tokenization, varlist and
option parsing, `if` clauses, expression AST construction, and `run <script>` commands. `use
<path>, lazy` and `use <path>, lazy engine=duckdb|polars` are parsed into typed load-mode fields.
Phase 13 slices 1-3 add parsed command forms for `regress`, `predict`, and `estat` with
constrained option sets (`robust`, `cluster(...)`, `noconstant`, `wls(...)`, `gls(...)`, `xb`,
`residuals`, `residuals|ovtest|vif`). Current Phase 14 parsing adds
`ivregress 2sls|gmm ... endog(...) iv(...)`, `estat firststage|overid|hausman|endogenous`,
`xtreg <y> <xvars>, fe|re[, robust cluster(...)]`,
`xtdata <varlist>, within|between`, and
`cfregress <y> [exog_vars], endog(...) iv(...)[, robust cluster(...) noconstant]`.
Phase 15 parsing adds
`logit|probit <y> <xvars>[, robust cluster(...) noconstant]` plus `estat margins`.
It may represent parsed-only future commands, but execution remains an executor or CLI-edge
responsibility. Recoverable parser failures compose through `comp-builders` `Result` values exposed
by the local `tabdat.monads` boundary. Parser internals convert those values back to user-facing
`ParseError` exceptions only at the public parser edge.

### Executor

Dispatches executable commands, maintains session state, and coordinates with the backend. For the
MVP, session state contains one active dataset, a session-local named table registry, and one typed
runtime config. Parsed-only Phase 2 command forms must fail with an unsupported-command execution
error until a later command contract defines execution. Runtime `set` commands update session config
and affect later commands in the same shell, command sequence, or script. `join` and `append`
validate active state and named-table lookup at the executor boundary before asking the backend to
materialize the next active relation. `reshape` validates active state at the executor boundary and
delegates active-dataset wide/long materialization to the backend. `panel` stores session-local
panel id/time metadata on active dataset snapshots, asks the backend to validate active rows, and
preserves or clears metadata across state-changing commands according to the command contract.
Phase 13 slices 1-3 add session-local regression state for the latest fitted linear model, extend
`regress` execution from OLS to WLS/GLS estimator modes through `statsmodels`, keep `predict` as a
deterministic dataset-transform command over that state, and expose post-estimation diagnostics via
`estat residuals|ovtest|vif`. Phase 14 adds `ivregress 2sls|gmm` execution through `linearmodels`,
IV-focused `estat firststage|overid` plus `estat endogenous` after `2sls`, panel `xtreg` FE/RE plus
`estat hausman` with bounded covariance constraints, bounded `cfregress` control-function execution
through Python-first two-stage OLS residual inclusion plus `estat endogenous` over
residual-inclusion statistics, `estat firststage` after `cfregress`, and panel report structure
metrics (including balancedness).
Phase 15 adds bounded binary-choice `logit` and `probit` execution through `statsmodels` with
nonrobust, HC1 robust, and clustered covariance modes plus deterministic pseudo R-squared output.
`estat margins` routes to deterministic predictor-level marginal-effects output after the latest
binary-choice model state.
Estimation-family state is explicit: running one family clears stale state from the others to
prevent cross-family `estat` reuse.

### DuckDB Backend

Owns data access and query execution. Parquet is the primary initial format. Eager loading creates
a session-local active DuckDB table. Lazy loading creates a DuckDB `read_parquet(...)` scan view so
load-time projection, filtering, grouping, and terminal query operations can be pushed into DuckDB.
Local paths and `http://`, `https://`, or `s3://` Parquet URIs share this DuckDB loading boundary;
remote credentials and non-Parquet remote formats are not part of the current contract.
Session transformations replace the active relation for later commands. The optional `polars`
engine selector now has a bounded real execution slice for local Parquet paths: projection,
row-filtering, and preview/count commands can stay in a Polars `LazyFrame` boundary while later
unsupported commands materialize once back into the eager DuckDB relation path. Remote Parquet
URIs stay on the DuckDB boundary in the current contract. A session-local named table registry
stores SQL `into` results under safe internal DuckDB relation names; `use <table>` reactivates a
registered table, while the active relation remains the default target for non-SQL commands.
`join <table> on <keylist>` joins the active relation to a registered named table using same-name
equality keys, supports `inner` and `left` joins, suffixes right-side non-key column collisions,
and materializes the result as the new eager active relation.
`save` stays Parquet-only, while `export` persists the active dataset to local `.parquet`, `.csv`,
or `.feather` paths without mutating session state.
`append <table>` vertically stacks a registered named table under the active relation after strict
same-column and compatible-type validation, preserving active-dataset column order and
materializing the result as the new eager active relation. `reshape long <stublist>, i(...) j(...)`
converts active wide columns named `<stub>_<j_value>` into long rows, while
`reshape wide <value_vars>, i(...) j(...)` pivots long rows into `<value_var>_<j_value>` columns;
both replace the active relation with an eager materialized result. `panel <id_var> <time_var>`
validates that id/time variables exist, contain no missing values, and uniquely identify active
rows with DuckDB checks. Panel metadata is session-local, stored on `DatasetInfo`, restored through
named-table activation when the snapshot carries it, and not persisted into Parquet files. No
persistent registry exists, but `save` / `export` can persist the active relation to local Parquet.
SQL commands bind the active relation as the user-facing DuckDB view `active`. Initial lazy loads
report an unknown row count until a live count or materializing operation runs.
For Phase 13 prediction workflows, the backend materializes linear `xb` or residual expressions into
new active-dataset columns through the existing active-relation replacement path.

For visualization commands, the backend extracts typed rows or frequency counts from the active
table. It does not construct charts or write artifact files.

### Visualization Artifact Renderer

Owns Altair chart construction and SVG/PNG artifact writes. Default plot artifacts are written
under `<artifact_dir>/plots/` using `graph_format`, and explicit `saving(...)` paths create parent
directories as needed. Interactive shell default plot saves avoid overwriting existing artifacts by
adding `-2`, `-3`, and later suffixes, while batch and script defaults keep the stable unsuffixed
path for reproducibility. Interactive shell auto-open is a CLI-edge behavior controlled by
`graph_open`; batch `-c` and script execution only print the artifact path.

### Formatter

Converts structured command results into deterministic terminal text. The backend should not own
display formatting.

## Current Repository State

- Product docs are in `docs/project_proposal.md`, `docs/dev_phase.md`, and `docs/phase0_product_guardrails.md`.
- Initial command scope is in `docs/command_glossary_v0.md`.
- Package metadata is in `pyproject.toml`.
- Phase handoff artifacts live under `_workspace/`.
- Integrated public-dataset E2E tooling lives under `integrated_testing/`; generated datasets,
  run logs, plots, and Parquet outputs are ignored.
- Runtime modules live under `src/tabdat/`.
- Functional helper imports live in `src/tabdat/monads.py`, which re-exports the project-approved
  `comp-builders` primitives and small edge conversion helpers.
- Focused tests live under `tests/`.
- The installed console script is `tabdat`.
- Phase 2 expression ASTs now compile to DuckDB SQL for Phase 3 transformations.
- Phase 3 commands are executable: `codebook`, `count`, `head`, `tail`, `keep`, `drop`, `select`,
  `rename`, `generate`, `replace`, `tabulate`, `collapse`, and supported `by:` forms.
- The supported `by:` child commands are `summarize` and `count`.
- Phase 4 SQL is executable for result-producing `select` and `with` queries through `sql`.
- Multiline SQL can be entered with `sql """..."""`.
- `sql ... into <table>` creates a session-local named table and makes it active.
- `use <table>` reactivates a registered named table; `use <path>` remains local Parquet loading.
- `join <table> on <keylist>` joins the active dataset with a registered named table and replaces
  the active dataset with the joined result.
- `append <table>` appends a registered named table to the active dataset and replaces the active
  dataset with the appended result.
- `reshape long <stublist>, i(<id_vars>) j(<name_var>)` and
  `reshape wide <value_vars>, i(<id_vars>) j(<name_var>)` reshape only the active dataset and
  replace it with an eager materialized result.
- `panel <id_var> <time_var>`, `panel`, and `panel clear` manage session-local panel metadata for
  the active dataset.
- Phase 5 prompt-toolkit UX is available for interactive sessions.
- Phase 6 plot commands are executable: `histogram`, `scatter`, and `bar`.
- Phase 7 lazy loading is executable through `use <path>, lazy` and
  `use <path>, lazy engine=duckdb|polars`; plain `use <path>` remains eager.
- Phase 8 scripting is executable through `tabdat -f <script>`, `tabdat <script>`, and
  `run <script>`.
- Script-only `seed <integer>` and `let <name> = <value>` directives are available in script files;
  `$name` macro references expand in later script entries and nested `run` scripts.
- Script-only non-nested `if` / `else` / `end` conditionals are available in script files.
- `use` can load local Parquet paths or DuckDB-readable `http://`, `https://`, and `s3://` Parquet
  URIs.
- Phase 9 config is executable through project-local `.tabdat.toml`, XDG user config,
  `--config <path>`, and runtime `set` commands.
- Phase 9 persistence is executable through `save <path>[, replace]` and
  `export <path>[, replace]` for local `.parquet`, `.csv`, and `.feather` files.
- Phase 13 slices 1-3 are executable through
  `regress <y> <xvars>[, robust cluster(<var>) noconstant wls(<weight_var>) gls(<sigma_var>)]`
  plus `predict <newvar>[, xb residuals]` and `estat <residuals|ovtest|vif>`.
- Phase 14 IV slices are executable through
  `ivregress 2sls|gmm <y> [exog_vars], endog(<var>) iv(<vars>)[, robust cluster(<var>) noconstant]`.
- Phase 14 IV diagnostics are executable through `estat firststage` and `estat overid` after
  successful `ivregress`, plus `estat endogenous` after successful `ivregress 2sls`.
- Phase 14 panel starter commands are executable through
  `xtreg <y> <xvars>, fe|re[, robust cluster(<var>)]` and `estat hausman` after matching FE/RE
  fits with non-cluster covariance.
- Phase 14 panel-index transforms are executable through
  `xtdata <varlist>, within|between` after `panel <id_var> <time_var>`.
- Phase 14 control-function core is executable through
  `cfregress <y> [exog_vars], endog(<var>) iv(<vars>)[, robust cluster(<var>) noconstant]`.
- Phase 14 control-function prediction is executable through
  `predict <newvar>[, xb residuals]` after successful `cfregress`.
- Phase 14 control-function endogenous diagnostics are executable through
  `estat endogenous` after successful `cfregress`.
- Phase 14 control-function first-stage diagnostics are executable through
  `estat firststage` after successful `cfregress`.
- Phase 15 nonlinear estimation core currently includes
  `logit <y> <xvars>[, robust cluster(<var>) noconstant]`,
  `probit <y> <xvars>[, robust cluster(<var>) noconstant]`, and `estat margins`.
- `panel` report output includes deterministic panel-structure metrics when panel metadata is set:
  observation count, entity/time counts, per-entity min/max counts, and balancedness.
- Plot artifacts support SVG and PNG output through Altair and `vl-convert-python`.
- Autocomplete reads active dataset and named table metadata from executor state but does not
  validate or mutate session state.
- Inline suggestions are history-based and persisted via `~/.tabdat_history`.

## Development Boundaries

- Build vertical slices across parser, executor, backend, CLI output, tests, and docs.
- Do not add broad command grammar before a command contract needs it.
- Keep public behavior documented before implementation.
- For Phase 13+ statistical/econometric commands, use a library-first implementation order:
  Python libraries first, R libraries via `rpy2` second, and lower-level `numpy`/`scipy`
  implementations only as the last resort.
- Import `Result`, `Option`, and `Validation` through `tabdat.monads`; do not import
  `comp-builders` directly from feature modules unless a future design records a reason to bypass
  the local boundary.
- Keep transformation state session-local except for explicit `save` / `export`.
- Keep chart rendering separate from backend data extraction.
- Keep script orchestration at the CLI edge; command semantics should still enter through the
  parser/executor boundary.
- Keep `seed` and `let` script-only at the script runner edge until a future command contract
  defines interactive or executor-level semantics.
- Keep `if` / `else` / `end` script-only at the script runner edge until a future command contract
  defines richer scripting semantics.
- Keep remote loading scoped to DuckDB-readable Parquet URIs until credentials, DB connections, or
  broader remote data access are explicitly designed.
- Keep named tables session-local until a future persistence/catalog contract exists.
- Keep `ivregress` (`2sls|gmm`) scoped to one endogenous variable plus one-or-more instruments
  until broader endogeneity diagnostics and panel-estimation contracts are implemented.
- Keep `join` scoped to named-table inputs and same-name equality keys until a broader multi-table
  workflow contract is written.
- Keep `append` scoped to named-table inputs with strict same-column schemas until a broader stack
  or union contract is written.
- Keep `reshape` scoped to active-dataset wide/long forms with required `i(...)` and `j(...)`
  options until panel metadata, aliases, or broader reshape ergonomics are designed.
- Keep `panel` scoped to id/time metadata validation and bounded structure reporting
  (including balancedness summary) until broader estimation commands define additional panel
  semantics.
- Keep `xtreg` scoped to panel-metadata-backed FE/RE estimators and `estat hausman` for matching
  non-cluster model pairs until broader panel-indexing/transformation contracts are written.
- Keep `xtdata` scoped to deterministic within/between column transforms for numeric variables
  until broader panel-indexing/transformation contracts are written.
- Keep `cfregress` diagnostics scoped to bounded `estat endogenous` residual-inclusion output
  (`test`, `estimate`, `std_error`, `statistic`, `p_value`, `ci_level`, `ci_lower`, `ci_upper`,
  `distribution`, `df`) until broader control-function diagnostics contracts are written.
- Keep `engine=polars` bounded to local Parquet lazy projection/filter/count/preview plus explicit
  eager fallback until a broader Polars-native contract is written.
- Use 2-space tab size across project files.
- Run configured linting and formatting proactively before commits.
