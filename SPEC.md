# TabDat-Explore Spec

This file tracks feature state for spec-driven development. Product intent lives in
`docs/project_proposal.md`; roadmap order lives in `docs/dev_phase.md`. Present should stay small
and describe the active work with concise verification criteria.

## Past

- Created the initial project proposal and development roadmap.
- Added the repository development harness and agent workflows.
- Established Phase 0 product guardrails:
  - project name: TabDat-Explore
  - CLI command: `tabdat`
  - command language: Stata-inspired, not Stata-compatible
  - MVP model: single active dataset
  - backend direction: DuckDB primary, Parquet first
  - contributor style: 2-space tab size and proactive linting/formatting
- Defined the v0 command glossary with 12 initial commands.
- Implemented the Phase 1 core skeleton:
  - `tabdat` console script and basic shell
  - minimal parser for `use`, `describe`, `summarize`, `exit`, and `quit`
  - executor with one active dataset
  - DuckDB-backed local Parquet loading and summaries
  - focused parser, executor/backend, and CLI smoke tests
- Implemented the Phase 2 parser foundation:
  - structured parser models for future command forms
  - command varlists, comma options, `if` clauses, and expression ASTs
  - expression parsing for identifiers, literals, arithmetic, comparisons, grouping, unary minus,
    and function calls
  - user-facing parse diagnostics for malformed Phase 2 syntax
  - focused parser coverage while preserving Phase 1 executable behavior
- Implemented the full Phase 3 core EDA command surface:
  - `codebook [varlist]` compact column profiling
  - `count` active dataset row counts
  - `head [n]` and `tail [n]` row previews
  - `keep`, `drop`, and `select` column projection and row filtering
  - `rename`, `generate`, and `replace` session-local transformations
  - `tabulate` one-way and two-way frequency tables
  - `collapse` grouped aggregate datasets
  - `by group_vars: summarize` and `by group_vars: count`
  - DuckDB-backed active relation execution, deterministic terminal formatting, and focused
    parser/executor/CLI tests
- Implemented Phase 4 SQL integration:
  - `sql <select-or-with-query>` as an escape hatch over the active dataset exposed as `active`
  - `sql """..."""` multiline query parsing and minimal shell continuation
  - `into <table>` support that replaces the active dataset with the SQL result
  - focused parser, executor/backend, and CLI smoke tests
- Implemented Phase 5 CLI UX:
  - prompt-toolkit interactive shell
  - syntax highlighting for command-oriented input
  - context-aware completions for commands, active dataset columns, options, `by:` forms, and SQL
    helpers
  - persistent command history and inline history suggestions
  - focused shell UX tests while preserving `-c` command mode
- Implemented Phase 6 artifact-based visualization:
  - `histogram`, `scatter`, and `bar` plot commands
  - Altair-backed SVG/PNG artifact rendering
  - default artifact output under `artifacts/plots/`
  - `saving(...)`, `noopen`, `bins=`, and `missing` plot options
  - interactive auto-open behavior while preserving deterministic `-c` batch output
  - focused parser, executor, CLI, and shell UX tests
- Implemented Phase 7 lazy execution entrypoint:
  - `use <path>, lazy` opt-in loading while preserving eager `use <path>` defaults
  - `engine=duckdb|polars` lazy engine selection with DuckDB as the default
  - DuckDB `read_parquet` scan views for lazy load-time pushdown
  - typed dataset execution-mode metadata and CLI output for lazy sessions
  - focused parser, executor, and CLI tests for lazy command flows
- Replaced the external PyMonad dependency with local typed monad helpers for parser failure
  composition and future pure-core absence handling.
- Implemented Phase 8 scripting and reproducibility:
  - script execution from files via `tabdat -f <script>` and `tabdat <script>`
  - interactive and nested `run <script>` with relative nested path resolution
  - whole-line script comments, blank-line skipping, and multiline `sql """..."""` blocks
  - deterministic script metadata and command transcripts
  - fail-fast script errors with file and line number diagnostics
  - script-mode plot auto-open suppression and golden mini-session coverage
  - lazy-mode documentation for materialization limits and experimental Polars selection
- Implemented Phase 9 configuration and persistence:
  - startup config precedence via explicit `--config <path>`, project-local `.tabdat.toml`, and
    XDG user config
  - runtime `set graph_format`, `set artifact_dir`, and `set graph_open`
  - config-aware plot artifact defaults with interactive-shell collision-avoiding suffixes
  - live row counting for `count` and unknown initial row counts for lazy loads
  - Parquet-only `save` plus `.parquet`, `.csv`, and `.feather` `export` for session-local
    transformations
- Completed the integrated public-dataset E2E checkpoint:
  - reusable harness for the Titanic, shell, NYC taxi lazy-scale, and Penguins script scenarios
  - captured deterministic stdout/stderr, exit-code, artifact, plot, and Parquet checks
  - fixed interactive shell Ctrl-C handling during prompt-toolkit completion
- Implemented Phase 10 execution and state foundations:
  - lightweight session-local named table registry
  - `sql ... into <table>` named table creation and activation
  - `use <table>` named table reactivation
  - executor state-handler extraction for state-changing commands
  - specific execution error subclasses for missing active data, missing variables, type
    mismatches, missing tables, reserved names, and backend failures
  - named table shell completions
  - bounded real Polars lazy execution for projection, row filtering, describe/count/head/tail,
    and explicit eager fallback for unsupported commands
- Adopted `comp-builders` behind the local `tabdat.monads` boundary:
  - `Result`, `Option`, and `Validation` are now imported through `tabdat.monads`
  - parser recoverable failures compose with a `@result.block`
  - edge helpers convert functional values back to public parser exceptions or plain values
- Implemented the first Phase 11 data workflow primitive:
  - `join <table> on <keylist>` over session-local named tables
  - `how=inner|left` join kinds with `inner` as the default
  - `suffix(<suffix>)` for right-side non-key column collisions
  - active dataset replacement with deterministic DuckDB materialization
  - focused parser, executor/backend, and CLI coverage
- Implemented the second Phase 11 data workflow primitive:
  - `append <table>` over session-local named tables
  - strict same-column schema validation with compatible DuckDB types
  - active-dataset column order preservation
  - active dataset replacement with deterministic DuckDB materialization
  - focused parser, executor/backend, CLI, and shell coverage
- Implemented the third Phase 11 data workflow primitive:
  - `reshape long <stublist>, i(<id_vars>) j(<name_var>)`
  - `reshape wide <value_vars>, i(<id_vars>) j(<name_var>)`
  - active-dataset wide-to-long and long-to-wide DuckDB materialization
  - deterministic active dataset replacement and terminal output
  - focused parser, executor/backend, CLI, and shell coverage
- Implemented Phase 11 panel metadata:
  - `panel <id_var> <time_var>` session-local panel identifier metadata
  - `panel` reporting and `panel clear`
  - DuckDB validation for missing id/time values and duplicate id/time pairs
  - deterministic metadata preservation, renaming, revalidation, and clearing across existing
    state-changing commands
  - focused parser, executor/backend, CLI, and shell coverage
- Implemented Phase 11 script reproducibility primitives:
  - script-only `seed <integer>` metadata
  - script-only `let <name> = <value>` macros
  - `$name` macro expansion for later script entries and nested `run` scripts
  - top-level script-scoped macro and seed state with line-numbered diagnostics
  - focused script parser/helper and CLI coverage
- Completed the remaining Phase 11 prerequisites:
  - minimal script-only `if` / `else` / `end` control flow with literal and token-comparison
    conditions
  - branch skipping without command echo or execution for inactive script branches
  - narrow remote Parquet loading for `http://`, `https://`, and `s3://` URIs through DuckDB
  - focused script helper, CLI, parser, backend classification, model, and validation coverage
- Completed an SDD documentation compliance pass:
  - confirmed root `SPEC.md`, `ARCHITECTURE.md`, and `CHANGELOG.md` coverage
  - recorded that Phase 12 estimation substrate has been implemented as the internal
    econometrics foundation
  - preserved the local `tabdat.monads` boundary as an active contributor invariant
- Implemented the first Phase 13 core linear econometrics slice:
  - `regress <y> <xvars>[, robust cluster(<var>) noconstant]` with Python-first `statsmodels`
    OLS fitting
  - covariance selection for non-robust, HC1 robust, and clustered standard errors
  - `predict <newvar>[, xb residuals]` active-dataset column generation using the latest
    regression model state
  - deterministic regression result formatting and focused parser, executor/backend, CLI, and
    shell coverage
- Implemented the second Phase 13 core linear econometrics slice:
  - `regress <y> <xvars>, wls(<weight_var>)` and `regress <y> <xvars>, gls(<sigma_var>)`
  - covariance combinations for weighted estimators with `robust` and `cluster(<var>)`
  - positive-value validation for retained WLS weights and GLS sigma values
  - deterministic estimator metadata output plus focused parser, executor/backend, CLI, and shell
    coverage
- Implemented the third Phase 13 core linear econometrics slice:
  - `estat <residuals|ovtest|vif>` post-estimation diagnostics over the latest regression state
  - residual analysis summaries plus Ramsey RESET (`ovtest`) and VIF multicollinearity checks
  - best-effort diagnostics compatibility across OLS, WLS, and GLS regression states
  - focused parser, executor/backend, CLI, and shell coverage
- Completed Phase 13 linear econometrics hardening:
  - integrated public-dataset E2E coverage now includes a dedicated
    `s5_titanic_phase13_dogfood` scenario for `regress`, `predict`, and `estat`
  - script reproducibility harness assertions align with current `export` wording
    (`Exported:`)
  - full project validation and integrated E2E harness pass with the updated scenario set
- Implemented the first Phase 14 endogeneity foundations slice:
  - `ivregress 2sls <y> [exog_vars], endog(<var>) iv(<vars>)`
  - covariance options `robust` and `cluster(<var>)`, plus `noconstant`
  - Python-first `linearmodels` IV2SLS execution with deterministic CLI formatting
  - focused parser, executor/backend, CLI, and shell coverage
- Implemented the second Phase 14 endogeneity diagnostics slice:
  - `estat firststage` and `estat overid` after `ivregress`
  - weak-instrument first-stage diagnostics plus deterministic overidentification output
    (`sargan` and `wooldridge_overid`)
  - strict `estat` family routing so IV diagnostics require prior `ivregress`
  - focused parser, executor/backend, CLI, and shell coverage
- Implemented the third Phase 14 panel-model starter slice:
  - `xtreg <y> <xvars>, fe|re[, robust cluster(<var>)]`
  - `estat hausman` for matching FE/RE fits with non-cluster covariance
  - required panel metadata precondition via `panel <id_var> <time_var>`
  - strict estimation-state invalidation across `regress`, `ivregress`, and `xtreg`
  - focused parser, executor/backend, CLI, and shell coverage
- Implemented the fourth Phase 14 panel-indexing slice:
  - `xtdata <varlist>, within|between` after `panel <id_var> <time_var>`
  - deterministic `<var>_within` and `<var>_between` transformed numeric columns
  - strict panel-metadata and numeric-variable preconditions with deterministic errors
  - focused parser, executor/backend, CLI, and shell coverage

## Present

- Feature: Phase 14 endogeneity and panel foundations
  Status: Active
  Started: 2026-05-12
  Branch: codex/tmp-phase14-slice4-xtdata

  Summary:
  Continue from implemented `ivregress`, IV diagnostics, panel FE/RE/Hausman starter, and
  `xtdata` within/between transforms to fill the remaining Phase 14 control-function prerequisites.

  Verification:
  - Full quality checks pass (`ruff`, `pyright`, `mypy`, `pytest`)
  - Integrated E2E scenarios `s1` through `s5` pass
  - `ivregress 2sls` works with nonrobust, robust, and clustered covariance modes
  - `estat firststage|overid` works after `ivregress`
  - `xtreg` FE/RE and `estat hausman` work with required panel metadata
  - `xtdata ... , within|between` works with required panel metadata

  Out of Scope:
  - Broad panel workflow redesign
  - Nonlinear estimators
  - R fallback adapters while Python-first coverage is available

## Future

- Phase 13+ statistical/econometric implementation policy:
  - approach order:
    1. use well-established Python libraries first when the method is directly supported or can be
       orchestrated with limited glue
    2. if Python coverage is missing or workaround-heavy, use well-established R packages through
       `rpy2` adapters
    3. only then add focused lower-level implementations on top of `numpy`/`scipy` and the Phase 12
       estimation substrate
  - keep commands as thin wrappers over library backends while normalizing outputs into the shared
    Phase 12 estimation result contract
- Phase 14 endogeneity and panel foundations:
  - complete the remaining Phase 14 scope beyond implemented `ivregress`, IV diagnostics,
    FE/RE/Hausman, and `xtdata` within/between transforms:
    control-function entry points and any additional panel-indexing semantics beyond current slice
  - library strategy:
    - approach (1): `linearmodels` for IV/2SLS, IV-GMM, and panel FE/RE; supplement with
      `statsmodels` diagnostics when needed
    - approach (2): `AER` (`ivreg`), `plm`, and `fixest` via `rpy2` for panel/IV gaps
    - approach (3): targeted `numpy`/`scipy` implementations over the shared GMM substrate
- Phase 15 nonlinear estimation core:
  - add binary-choice models, marginal effects, nonlinear regression, and limited dependent
    variable models such as Tobit, truncated regression, and sample selection
  - library strategy:
    - approach (1): `statsmodels` for logit/probit workflows, marginal effects, and core nonlinear
      likelihood models
    - approach (2): `sampleSelection`, `censReg`, and `truncreg` via `rpy2` for Heckman-style,
      censored, and truncated models
    - approach (3): targeted `scipy.optimize` + `numpy` MLE implementations only when necessary
- Phase 16 specialized likelihood models:
  - add discrete-choice systems, count models, mixture/hurdle/zero-inflated models, and
    duration/survival models
  - library strategy:
    - approach (1): `statsmodels` for multinomial/count/zero-inflated families and `lifelines` for
      duration/survival workflows
    - approach (2): `mlogit`, `glmmTMB`, and `survival` via `rpy2` for model families not covered
      cleanly in Python
    - approach (3): targeted `scipy.optimize` + `numpy` likelihood implementations only when needed
- Phase 17 advanced empirical methods:
  - add dynamic and advanced panel GMM, nonlinear panel models, quantile/distributional methods,
    semiparametric/nonparametric methods, and causal-inference workflows
  - library strategy:
    - approach (1): `linearmodels`/`statsmodels` where available for panel-GMM, quantile, and
      semiparametric building blocks
    - approach (2): `fixest`, `did`, `MatchIt`, `Synth`, and `quantreg` via `rpy2` for mature
      causal and distributional workflows
    - approach (3): targeted `numpy`/`scipy` implementations only when the first two layers are
      insufficient
- Phase 18 ecosystem and extension layer:
  - add a plugin system, broader remote connectors, and formalized R adapter governance once command
    and analytical result interfaces are stable
  - library strategy:
    - approach (1): stabilize Python adapter layers for adopted libraries (`statsmodels`,
      `linearmodels`, `lifelines`, and related dependencies)
    - approach (2): harden `rpy2` adapter boundaries and package management for approved R
      dependencies such as `fixest`, `plm`, and `lme4`
    - approach (3): keep lower-level code limited to compatibility glue and performance-critical
      kernels
- Phase 19 modern extensions:
  - add machine-learning integration, Bayesian workflows, and spatial models as explicitly
    late-stage extensions
  - library strategy:
    - approach (1): `scikit-learn` for ML workflows, `pymc`/`bambi` for Bayesian workflows, and
      `pysal` (`spreg`) for spatial econometrics
    - approach (2): `brms`/`rstanarm` and `spdep`/`spatialreg` via `rpy2` where R has stronger
      coverage
    - approach (3): narrow `numpy`/`scipy` custom implementations only when no mature backend fits
