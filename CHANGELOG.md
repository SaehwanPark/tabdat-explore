# Changelog

All notable project changes are tracked here.

## Unreleased

### Added

- Added the thirteenth Phase 14 panel semantics extension slice with deterministic `panel` report
  metrics (`observation_count`, `entity_count`, `time_count`, per-entity min/max observations, and
  balancedness), with focused backend/executor/formatter/CLI coverage.
- Added the twelfth Phase 14 control-function diagnostics extension slice with
  `estat firststage` support after `cfregress`, including deterministic first-stage coefficient and
  fit-summary output plus focused executor/CLI coverage.
- Added the eleventh Phase 14 IV endogenous diagnostics slice with `estat endogenous` support after
  `ivregress 2sls`, deterministic Durbin/Wu-Hausman output rows, and focused executor/CLI
  coverage while preserving existing `cfregress` endogenous diagnostics behavior.
- Added the tenth Phase 14 IV estimator expansion slice with
  `ivregress gmm <y> [exog_vars], endog(<var>) iv(<vars>)[, robust cluster(<var>) noconstant]`,
  deterministic estimator output across `2sls` and `gmm`, and focused parser/executor/CLI/shell
  coverage.
- Added deterministic `estat overid` compatibility across IV estimators: `sargan` and
  `wooldridge_overid` rows after `2sls` plus `gmm_j` rows after `gmm`.
- Added the ninth Phase 14 control-function diagnostics expansion slice with `estat endogenous`
  output rows for `ci_level`, `ci_lower`, `ci_upper`, `distribution`, and `df` (in addition to
  `test`, `estimate`, `std_error`, `statistic`, and `p_value`) after `cfregress`, with focused
  executor/CLI coverage.
- Added the eighth Phase 14 control-function diagnostics expansion slice with `estat endogenous`
  output rows for `estimate` and `std_error` (in addition to `test`, `statistic`, and `p_value`)
  after `cfregress`, with focused executor/CLI coverage.
- Added the seventh Phase 14 control-function diagnostics slice with `estat endogenous` support
  after `cfregress`, deterministic residual-inclusion diagnostic output, and focused
  parser/shell/executor/CLI coverage.
- Added the sixth Phase 14 control-function prediction slice with `predict <newvar>[, xb residuals]`
  support after `cfregress`, deterministic `predict` model-family routing, and focused
  executor/backend/CLI coverage.
- Added the fifth Phase 14 control-function core slice with
  `cfregress <y> [exog_vars], endog(<var>) iv(<vars>)[, robust cluster(<var>) noconstant]`,
  bounded two-step residual-inclusion execution, deterministic formatter output, and focused
  parser/executor/CLI/shell coverage.
- Added the fourth Phase 14 panel-indexing slice with
  `xtdata <varlist>, within|between`, panel-metadata preconditions, deterministic
  `_within`/`_between` transformed columns, and focused parser/executor/CLI/shell coverage.
- Added the second Phase 14 diagnostics slice with `estat firststage` and `estat overid` over
  `ivregress` model state, deterministic Sargan/Wooldridge overidentification output, and focused
  parser/executor/CLI/shell coverage.
- Added the third Phase 14 panel-model starter slice with
  `xtreg <y> <xvars>, fe|re[, robust cluster(<var>)]`, required `panel` metadata preconditions,
  `estat hausman` for matching FE/RE fits, deterministic formatter output, and focused
  parser/executor/CLI/shell coverage.
- Added the first Phase 14 endogeneity foundations slice with
  `ivregress 2sls <y> [exog_vars], endog(<var>) iv(<vars>)[, robust cluster(<var>) noconstant]`,
  Python-first `linearmodels` IV2SLS execution, deterministic formatter output, and focused
  parser/executor/CLI/shell coverage.
- Added `linearmodels` as the Phase 14 Python-first IV/2SLS backend dependency.
- Added integrated E2E scenario `s5_titanic_phase13_dogfood` to exercise real-dataset
  `regress`/`predict`/`estat` flows as a Phase 13 hardening gate.
- Added the third Phase 13 linear econometrics slice with `estat <residuals|ovtest|vif>`
  post-estimation diagnostics, residual-analysis summaries, Ramsey RESET specification testing,
  VIF multicollinearity checks, best-effort OLS/WLS/GLS compatibility, and focused
  parser/executor/backend/CLI/shell coverage.
- Added the second Phase 13 linear econometrics slice with
  `regress <y> <xvars>, wls(<weight_var>)` and `regress <y> <xvars>, gls(<sigma_var>)`,
  weighted-estimator covariance combinations (`robust` and `cluster(<var>)`), positive
  weight/sigma validation for retained rows, deterministic estimator metadata output, and focused
  parser/executor/backend/CLI/shell coverage.
- Added the first Phase 13 linear econometrics slice with
  `regress <y> <xvars>[, robust cluster(<var>) noconstant]` and
  `predict <newvar>[, xb residuals]`, including Python-first `statsmodels` OLS fitting,
  regression-result formatting, and focused parser/executor/backend/CLI/shell coverage.
- Added Phase 9 export widening with suffix-driven local `.parquet`, `.csv`, and `.feather`
  `export`, distinct `Exported:` CLI output, and focused parser, executor, and CLI coverage.
- Added a bounded real Phase 10 Polars lazy execution slice for local Parquet projection,
  row-filtering, count, and preview commands, plus explicit eager fallback for unsupported
  commands.
- Added Phase 9 startup config fallback through XDG user config at
  `$XDG_CONFIG_HOME/tabdat/config.toml` or `~/.config/tabdat/config.toml` when no explicit
  `--config` or project-local `.tabdat.toml` is present.
- Added Phase 12 estimation substrate with reusable statistical primitives, bootstrap resampling,
  least-squares contracts, and shared MLE/GMM estimation interfaces plus focused tests.

- Completed the remaining Phase 11 prerequisites with script-only non-nested `if` / `else` / `end`
  conditionals, macro-expanded condition evaluation, inactive branch skipping, and narrow
  DuckDB-backed remote Parquet loading for `http://`, `https://`, and `s3://` URIs.
- Added Phase 11 script reproducibility primitives with script-only `seed <integer>` metadata,
  script-only `let <name> = <value>` macros, `$name` expansion in later script entries and nested
  `run` scripts, deterministic expanded command transcripts, line-numbered script diagnostics, and
  focused script helper and CLI coverage.
- Added Phase 11 panel metadata with `panel <id_var> <time_var>`, `panel`, and `panel clear`,
  DuckDB-backed missing-value and duplicate id/time validation, session-local metadata
  preservation/clearing across state-changing commands, deterministic CLI output, and focused
  parser, executor/backend, CLI, and shell coverage.
- Added the third Phase 11 data workflow primitive with `reshape long` and `reshape wide` over the
  active dataset, required `i(...)` and `j(...)` options, eager DuckDB materialization, active
  dataset replacement, deterministic output, and focused parser, executor/backend, CLI, and shell
  coverage.
- Added the second Phase 11 data workflow primitive with `append <table>`, strict same-column
  schema validation, active-dataset column order preservation, active dataset replacement, and
  focused parser, executor/backend, CLI, and shell coverage.
- Added the first Phase 11 data workflow primitive with `join <table> on <keylist>`, `how=inner|left`,
  right-side collision suffixing, active dataset replacement, and focused parser, executor/backend,
  and CLI coverage.
- Added Phase 10 execution and state foundations with a lightweight session-local named table
  registry, `use <table>` activation, typed execution error subclasses, executor state-handler
  extraction, and named table shell completions.
- Added `comp-builders` as the functional helper implementation behind `tabdat.monads`, including
  `Result`, `Option`, `Validation`, builder re-exports, and small edge conversion helpers.
- Reorganized the post-Phase-9 roadmap across `docs/dev_phase.md` and `SPEC.md` into an
  interleaved Phase 10-19 sequence that stages execution/state foundations, reproducibility and
  data-workflow primitives, core econometrics coverage, advanced empirical methods, and late
  ecosystem extensions coherently.
- Added an integrated public-dataset E2E harness and run documentation for the Titanic batch,
  interactive shell, NYC taxi lazy-scale, and Penguins script reproducibility scenarios.
- Added Phase 9 configuration and persistence with `.tabdat.toml`, `--config <path>`, runtime
  `set graph_format`, `set artifact_dir`, and `set graph_open`, config-aware plot defaults,
  live `count` execution for lazy datasets, Parquet `save`, and multi-format `export`.
- Added Phase 8 scripting and reproducibility with `tabdat -f <script>`, positional script
  execution, interactive and nested `run <script>`, deterministic script metadata, command
  transcripts, multiline SQL script blocks, line-numbered script errors, and script-mode plot
  auto-open suppression.
- Added local typed monad helpers for parser failure composition and pure-core absence handling.
- Added Phase 7 lazy execution entrypoint with `use <path>, lazy`, optional
  `engine=duckdb|polars` selection, DuckDB `read_parquet` scan views for lazy loading, typed
  execution-mode metadata, and CLI output that identifies lazy sessions.
- Added Phase 6 artifact-based visualization with `histogram`, `scatter`, and `bar` commands,
  Altair-backed SVG/PNG output, default `artifacts/plots/` paths, `saving(...)`, `noopen`, `bins=`,
  and `missing` options, plus interactive-only plot auto-open behavior.
- Added Phase 5 prompt-toolkit interactive shell UX with syntax highlighting, persistent command
  history, inline history suggestions, and context-aware autocomplete for commands, active dataset
  columns, common options, `by:` forms, and lightweight SQL helpers.
- Added Phase 4 SQL integration with `sql` queries over the active dataset exposed as `active`,
  multiline `sql """..."""` parsing, and `into <table>` active-dataset replacement.
- Completed the roadmap Phase 3 core EDA surface with executable transformations (`keep`, `drop`,
  `select`, `rename`, `generate`, `replace`), grouping (`by:` and `collapse`), and `tabulate`.
- Added session-local active DuckDB table state so transformations feed subsequent inspection and
  summary commands.
- Added the Phase 3 inspection slice with executable `codebook`, `count`, `head`, and `tail`
  commands over the active Parquet dataset.
- Added the Phase 2 parser foundation with structured command options, `if` clauses, expression
  ASTs, parsed-only future command forms, and focused diagnostics tests.
- Fixed Phase 2 parser regressions so `summarize` rejects assignment syntax and punctuated varlist
  names remain supported.
- Added Phase 1 `tabdat` CLI skeleton with `use`, `describe`, and `summarize`.
- Added DuckDB-backed local Parquet loading and numeric summary execution.
- Added focused parser, executor/backend, and CLI smoke tests.
- Added Phase 0 product guardrails for positioning, naming, MVP assumptions, non-goals, and contributor expectations.
- Added the v0 command glossary with the initial 12-command surface.
- Added SDD state files with feature status and planned architecture.
- Added repository guidance for 2-space tab size and proactive linting/formatting.

### Removed

- Removed the external PyMonad dependency in favor of local `tabdat.monads` helpers.

### Changed

- Changed estimation-state handling so `regress`, `ivregress`, and `xtreg` clear incompatible
  prior model-family state before later `predict`/`estat` usage.
- Updated script reproducibility integrated-E2E expectations to match current `export` output
  wording (`Exported:`).
- Updated SDD state (`SPEC.md`, `ARCHITECTURE.md`, and `README.md`) to record completed Phase 13
  hardening and the initial Phase 14 `ivregress 2sls` slice.
- Reworked `SPEC.md` to keep `Present` focused on the remaining Phase 13 hardening work and to
  move completed roadmap phases out of `Future`.
- Updated SDD state so `SPEC.md` records Phase 12 estimation substrate as implemented.
- Updated `SPEC.md`, `docs/dev_phase.md`, and `ARCHITECTURE.md` to define a Phase 13+ statistical
  implementation priority order: Python libraries first, R via `rpy2` second, and lower-level
  `numpy`/`scipy` implementations last.

- Changed structured parser failure composition from handwritten `Either` helpers to
  `comp-builders` `Result` values while preserving the public `ParseError` behavior.

### Fixed

- Fixed current Pyright type-check failures in parser option extraction, optional-value monad
  helpers, and integrated E2E PTY spawning.
- Fixed interactive shell Ctrl-C handling so prompt-toolkit completion interrupts return to the
  prompt instead of terminating with a traceback.
