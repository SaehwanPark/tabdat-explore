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
- Implemented the fifth Phase 14 control-function core slice:
  - `cfregress <y> [exog_vars], endog(<var>) iv(<vars>)[, robust cluster(<var>) noconstant]`
  - bounded two-step residual-inclusion execution with deterministic result formatting
  - strict parser and executor preconditions aligned with existing IV command boundaries
  - focused parser, executor, CLI, and shell coverage
- Implemented the sixth Phase 14 control-function prediction slice:
  - `predict <newvar>[, xb residuals]` after successful `cfregress`
  - deterministic model-family routing across regress/cfregress prediction state
  - focused executor/backend and CLI coverage
- Implemented the seventh Phase 14 control-function diagnostics slice:
  - `estat endogenous` after successful `cfregress`
  - deterministic residual-inclusion diagnostic table output (`cf_residual` statistic and p-value)
  - focused parser, shell, executor/backend, and CLI coverage
- Implemented the eighth Phase 14 control-function diagnostics expansion slice:
  - expanded `estat endogenous` residual-inclusion output with `estimate` and `std_error`
  - preserved existing `estat endogenous` command surface and precondition behavior
  - focused executor/backend and CLI coverage
- Implemented the ninth Phase 14 control-function diagnostics expansion slice:
  - expanded `estat endogenous` residual-inclusion output with
    `ci_level`, `ci_lower`, `ci_upper`, `distribution`, and `df`
  - preserved existing `estat endogenous` command surface and precondition behavior
  - focused executor/backend and CLI coverage
- Implemented the tenth Phase 14 IV estimator expansion slice:
  - `ivregress gmm <y> [exog_vars], endog(<var>) iv(<vars>)`
  - preserved covariance options (`robust`, `cluster(<var>)`, `noconstant`) and deterministic
    formatter output across `2sls` and `gmm`
  - deterministic `estat overid` support for both IV estimators:
    `sargan`/`wooldridge_overid` rows for `2sls` and `gmm_j` rows for `gmm`
  - focused parser, executor/backend, CLI, and shell coverage
- Implemented the eleventh Phase 14 IV endogenous diagnostics slice:
  - `estat endogenous` after `ivregress 2sls`
  - deterministic Durbin and Wu-Hausman output rows (`statistic`, `p_value`, `df`, `distribution`)
  - preserved existing control-function `estat endogenous` behavior after `cfregress`
  - explicit guard that IV endogenous diagnostics are not available after `ivregress gmm`
  - focused executor/backend and CLI coverage
- Implemented the twelfth Phase 14 control-function diagnostics extension slice:
  - `estat firststage` after successful `cfregress`
  - deterministic first-stage coefficient and fit-summary output (`coefficient`, `std_error`,
    `statistic`, `p_value`, `observation_count`, `r_squared`)
  - preserved existing IV `estat firststage` behavior and prerequisite errors
  - focused executor and CLI coverage
- Implemented the thirteenth Phase 14 panel semantics extension slice:
  - expanded `panel` report output with deterministic structure metrics
  - panel report now includes `observation_count`, `entity_count`, `time_count`,
    per-entity min/max observation counts, and balancedness (`yes`/`no`)
  - preserved existing `panel set`, `panel clear`, and metadata-validation behavior
  - focused backend, executor, formatter, and CLI coverage
- Implemented the first Phase 15 nonlinear estimation core slice:
  - `logit <y> <xvars>[, robust cluster(<var>) noconstant]`
  - Python-first `statsmodels` logit fitting with nonrobust, robust, and clustered covariance
    modes
  - deterministic logit result formatting with pseudo R-squared and coefficient output
  - focused parser, executor, CLI, and shell coverage
- Implemented the second Phase 15 nonlinear estimation core slice:
  - `probit <y> <xvars>[, robust cluster(<var>) noconstant]`
  - Python-first `statsmodels` probit fitting with nonrobust, robust, and clustered covariance
    modes
  - deterministic probit result formatting with pseudo R-squared and coefficient output
  - focused parser, executor, CLI, and shell coverage
- Implemented the third Phase 15 nonlinear estimation core slice:
  - `estat margins` after successful `logit` or `probit`
  - deterministic predictor-level marginal-effects table output
    (`dy_dx`, `std_error`, `statistic`, `p_value`, `ci_lower`, `ci_upper`)
  - strict prerequisite guard requiring prior binary-choice model state
  - focused parser, executor, CLI, and shell coverage
- Implemented the fourth Phase 15 nonlinear estimation core slice:
  - bounded binary-choice `predict` routing with `predict <newvar>[, xb residuals pr]`
  - `pr` support after successful `logit`/`probit` plus deterministic guards for unsupported
    binary residual prediction
  - preserved existing linear/control-function `predict` behavior
  - focused parser, executor, backend, CLI, and shell coverage
- Implemented the fifth Phase 15 nonlinear estimation core slice:
  - `tobit <y> <xvars>, ll(<num>) [ul(<num>) robust cluster(<var>) noconstant]`
  - bounded deterministic Tobit execution with required lower censoring limit and optional upper
    limit
  - Python-first policy preserved by using R fallback (`survival::survreg` via `rpy2`) only where
    direct Python support is insufficient
  - focused parser, executor, CLI, and shell coverage
- Implemented the sixth Phase 15 nonlinear estimation core slice:
  - `heckman <y> <xvars>, selectdep(<var>) select(<vars>) [robust cluster(<var>) noconstant]`
  - deterministic bounded sample-selection execution with explicit covariance labels and
    deterministic guard behavior
  - deterministic typed/formatted output for outcome and selection equations
  - focused parser, executor, CLI, and shell coverage
- Implemented the seventh Phase 15 nonlinear estimation core slice:
  - `nl <y> = <expr>, params(<params>) start(<values>) [robust noconstant]`
  - bounded nonlinear least-squares execution with deterministic nonrobust/robust covariance labels
  - deterministic typed/formatted output and `predict <newvar>[, xb residuals]` routing after `nl`
  - focused parser, executor, CLI, and shell coverage
- Implemented the first Phase 16 specialized likelihood-model slice:
  - `poisson <y> <xvars>[, robust cluster(<var>) noconstant]`
  - bounded count-model execution with deterministic nonrobust/robust/cluster covariance labels
  - deterministic `predict <newvar>[, xb residuals]` routing after `poisson`
  - deterministic `estat gof` diagnostics after `poisson`
  - focused parser, executor, CLI, shell, and help coverage
- Implemented the second Phase 16 specialized likelihood-model slice:
  - `nbreg <y> <xvars>[, robust cluster(<var>) noconstant]`
  - bounded count-model execution with deterministic nonrobust/robust/cluster covariance labels
  - deterministic `predict <newvar>[, xb residuals]` routing after `nbreg`
  - deterministic `estat gof` diagnostics after `nbreg`
  - focused parser, executor, CLI, shell, and help coverage
- Implemented the third Phase 16 specialized likelihood-model slice:
  - `zip <y> <xvars>, inflate(<zvars>) [robust cluster(<var>) noconstant]`
  - `zinb <y> <xvars>, inflate(<zvars>) [robust cluster(<var>) noconstant]`
  - bounded zero-inflated count-model execution with deterministic nonrobust/robust/cluster
    covariance labels
  - deterministic `predict <newvar>[, xb residuals]` routing after `zip` and `zinb`
  - deterministic `estat gof` diagnostics after `zip` and `zinb`
  - focused parser, executor, CLI, shell, and help coverage
- Implemented the fourth Phase 16 specialized likelihood-model slice:
  - `streg <time_var> <xvars>, failure(<event_var>) dist(weibull|exponential)
    [robust cluster(<var>) noconstant]`
  - bounded parametric duration/survival execution with deterministic nonrobust/robust/cluster
    covariance labels
  - deterministic typed/formatted output plus focused parser, executor, CLI, shell, and help
    coverage
- Implemented the first Phase 17 advanced empirical-methods slice:
  - `qreg <y> <xvars>[, quantile(<0,1>) robust noconstant]`
  - bounded quantile-regression execution with deterministic nonrobust/robust covariance labels
  - deterministic `predict <newvar>[, xb residuals]` routing after `qreg`
  - deterministic `estat residuals` diagnostics after `qreg` while preserving `ovtest`/`vif`
    as regress-only diagnostics
  - focused parser, executor, CLI, shell, and help coverage
- Implemented the second Phase 17 advanced empirical-methods slice:
  - `did <y> [controls], treat(<var>) post(<var>) [robust]` with required prior
    `panel <id_var> <time_var>`
  - bounded two-way fixed-effects execution through `linearmodels.PanelOLS` with deterministic
    nonrobust/robust covariance labels
  - deterministic `predict <newvar>[, xb]` routing after `did`
  - focused parser, executor, CLI, shell, and help coverage
- Implemented the third Phase 17 advanced empirical-methods slice:
  - `xtabond <y> [xvars] [, robust]` with required prior `panel <id_var> <time_var>`
  - bounded dynamic-panel AR(1) GMM starter with Python-first IVGMM execution and R fallback
  - deterministic `estat did` diagnostics after `did`
  - focused parser, executor, CLI, shell, and help coverage
- Implemented the fourth Phase 17 advanced empirical-methods slice:
  - `xtabond <y> [xvars] [, robust lags(#) instlag(#)]` with strict lag/instrument guards
  - bounded dynamic-panel execution now supports configurable lag depth and instrument lag starts
    while preserving Python-first IVGMM execution and R fallback behavior
  - expanded deterministic `estat did` diagnostics with DID cell counts, cell means, and raw
    diff-in-diff contrasts in addition to interaction coefficient metrics
  - focused parser, executor, CLI, shell, and help coverage
- Implemented the fifth Phase 17 advanced empirical-methods slice:
  - deterministic `estat overid` diagnostics after successful `xtabond`
  - deterministic `predict <newvar>[, xb residuals]` routing after successful `xtabond`
  - strict prediction guards for panel-metadata and variable compatibility
  - focused parser, executor, CLI, shell, and help coverage
- Implemented the sixth Phase 17 advanced empirical-methods slice:
  - `xtlogit <y> <xvars>, fe [robust]` with required prior `panel <id_var> <time_var>`
  - bounded nonlinear panel fixed-effects binary-choice execution via Python-first
    `statsmodels.discrete.conditional_models.ConditionalLogit`
  - deterministic typed/formatted output with focused parser, executor, CLI, shell, and help
    coverage
- Implemented the seventh Phase 17 advanced empirical-methods slice:
  - `lowess <y> <x>, gen(<newvar>) [bandwidth=<0,1>]`
  - bounded semiparametric/nonparametric smoothing workflow via Python-first
    `statsmodels.nonparametric.smoothers_lowess.lowess`
  - deterministic active-dataset transform output with focused parser, executor, CLI, shell, and
    help coverage
- Implemented the second Phase 18 ingestion slice:
  - eager `use` now accepts local and HTTP/HTTPS Stata `.dta` files through `pandas.read_stata`
  - `use ..., lazy` remains Parquet-only
  - focused backend, fixture, and executor coverage
- Implemented the third Phase 18 advanced econometrics replication demo slice:
  - added remote Stata URL loader bypass in `inspect_parquet` via custom User-Agent and tempfiles to resolve HTTP 403 Forbidden server blocks
  - added support for linear prediction (`predict ..., xb|residuals`) after `heckman` selection estimation
  - created three classic Stata-based advanced econometrics replication scripts under `demos/`: Heckman sample selection correction (`heckman_mroz.td`), Card returns to education IV/2SLS (`ivregress_card.td`), and NLSY wages panel Fixed/Random Effects with Hausman specification test (`panel_union.td`)
  - added automated test suite `tests/test_demos.py` to verify demo parser and executor flows via the CLI
- Implemented the fourth Phase 18 extension-governance slice:
  - added an internal typed extension registry contract for ingestion and estimator adapters
  - centralized ingestion adapter capability metadata for local/remote format support and lazy-engine constraints
  - centralized estimator adapter backend metadata for Python-first and R-fallback execution boundaries
  - preserved command surface/output behavior while adding focused registry contract tests
- Completed a Railroad-Oriented Programming dependency and parser checkpoint:
  - moved `comp-builders` from the previous Git direct reference to the published PyPI package
  - expanded the local `tabdat.monads` boundary to include async result helpers
  - centralized parser `Result` flow so public `ParseError` conversion stays at the parser edge
  - preserved existing command syntax and parser diagnostics
- Implemented the first Phase 19 modern-extensions slice:
  - `lasso linear <y> <xvars>[, alpha(<num>) noconstant]` bounded ML starter via
    Python-first `scikit-learn` `Lasso`
  - deterministic lasso result formatting and typed estimator adapter metadata
  - `predict <newvar>[, xb]` support after successful lasso with strict guards for
    unsupported `residuals`/`pr` modes
  - focused parser, executor, CLI, shell, help, and extension-registry coverage
- Implemented the second Phase 19 modern-extensions slice:
  - `bayes linear <y> <xvars>[, n_iter(<int>) tol(<num>) noconstant]` Bayesian ML starter
    via Python-first `scikit-learn` `BayesianRidge`
  - deterministic bayes result formatting and typed estimator adapter metadata
  - `predict <newvar>[, xb residuals]` support after successful bayes with strict guards
    for unsupported `pr` prediction mode
  - focused parser, executor, CLI, shell, help, and extension-registry coverage
- Implemented the third Phase 19 modern-extensions slice:
  - `spregress <y> <xvars>, coord(<lat> <lon>) [model(lag|error) knn(<k>) robust]` command
  - Construct row-standardized K-Nearest Neighbors (KNN) spatial weights matrices on the fly from coordinate columns
  - ML lag/error estimation (`spreg.ML_Lag`/`spreg.ML_Error`) and GMM-based heteroskedasticity-robust estimators (`spreg.GM_Lag`/`spreg.GM_Error_Het`)
  - Bounded exogenous linear prediction (`predict <newvar>, xb`) using fitted spatial state
  - Fully integrated in-app help topic, autocomplete interactive shell, extension registry, and comprehensive tests
- Implemented the fourth Phase 19 modern-extensions slice:
  - `ridge linear <y> <xvars>[, alpha(<num>) noconstant]` bounded ML regularization via
    Python-first `scikit-learn` `Ridge`
  - `elasticnet linear <y> <xvars>[, alpha(<num>) l1_ratio(<num>) noconstant]` bounded ML
    regularization via Python-first `scikit-learn` `ElasticNet`
  - deterministic ridge/elasticnet result formatting and typed estimator adapter metadata
  - `predict <newvar>[, xb]` support after successful ridge/elasticnet with strict guards
    for unsupported `residuals`/`pr` modes
- Implemented the fifth Phase 19 modern-extensions slice:
  - cross-validation wrappers `cvlasso`, `cvridge`, and `cvelasticnet` that automatically perform K-fold cross-validation to select optimal hyperparameters using custom grid search on scikit-learn estimators
  - save structured CV reports in the active `artifact_dir` without filename collisions
  - support prediction (`predict <newvar>, xb`) after cross-validation estimation
  - focused parser, executor/backend, CLI, shell, help, and extension-registry coverage
- Implemented Phase 20 doubly robust DID:
  - `drdid <y> [covariates], treat(<var>) post(<var>) [method(or|ipw|aipw) robust bootstrap(<n>) seed(<n>)]` command with Python-first outcome regression (OR), inverse probability weighting (IPW), and augmented doubly robust (AIPW) ATT estimators.
  - post-estimation diagnostics: `estat drdid` prints treated/control cell counts, propensity score summaries, and overlap checks.
  - robust and bootstrap standard error estimation with explicit seed support.
  - mocked R fallback calling CRAN `DRDID` R package via `rpy2` on error.
  - visible notes when otherwise eligible units are dropped because covariates have missing or non-finite values.
  - interactive shell autocompletions, in-app help topic, and comprehensive integration tests.
- Implemented the sixth Phase 19 modern-extensions slice:
  - added `predict <newvar>, spatial_lag` after successful `spregress ... model(lag)` fits
  - preserved existing `predict <newvar>, xb` support after `spregress`
  - bounded the new mode to the same active-dataset sample used during spatial fitting
  - deterministic executor guards now reject `spatial_lag` after `spregress ... model(error)` or
    mismatched active samples
  - focused parser, executor, CLI, shell, and help coverage
- Implemented the seventh Phase 19 modern-extensions slice:
  - `postlasso linear <y> <xvars>[, alpha(<num>) robust noconstant]`
  - Lasso-based candidate predictor selection followed by OLS refit on selected predictors
  - deterministic no-selection behavior: intercept-only refit by default and explicit
    `noconstant` guard
  - deterministic post-selection inference formatting, shell autocomplete, help, and extension
    registry metadata
  - focused parser, executor, CLI, shell, help, and extension-registry coverage
- Implemented the eighth Phase 19 modern-extensions slice:
  - `dml linear <y> <controls>, treat(<tvar>) [folds(<int>) alpha(<num>) robust seed(<int>) noconstant]`
  - partial-linear cross-fitted average treatment effect estimation for binary treatments under
    high-dimensional controls via Python-first `scikit-learn` Lasso nuisances and `statsmodels` OLS
    final stage
  - `estat dml` post-estimation diagnostics with fold count, treated/control counts, nuisance
    treatment-fit summaries, and overlap checks
  - focused parser, executor, CLI, shell, help, and extension-registry coverage
- Implemented Phase 19 spatial weight matrix configuration and GIS file ingestion:
  - `spregress <y> <xvars>, weights(<path>) id(<id_var>) [contiguity(queen|rook)]` command support
  - loaded pre-computed spatial weights from standard `.gal`, `.gwt`, and `.shp` files
  - case-insensitive attribute column resolution and dynamic matrix subsetting/reordering
  - predict `xb` and `spatial_lag` support after weights-file-based estimation
  - focused parser, executor/backend, CLI, autocomplete, and help topic coverage
- Implemented the tenth Phase 19 modern-extensions slice:
  - `bayes [, options]: <regress|logit>` general MCMC prefix command using Python-first `bambi` as the MCMC backend
  - MCMC chain option specifications (`draws`, `burnin`/`tune`, `chains`, `thin`, `seed`/`rseed`)
  - support custom priors (`prior(variable, distribution)`) for normal and uniform distributions
  - MCMC stats formatting (`Mean`, `Std. Dev.`, `MCSE`, `Cred. Interval`)
  - focused parser, executor/backend, autocomplete, help topic, and CLI coverage
- Implemented the eleventh Phase 19 modern-extensions slice:
  - `predict <newvar>, posterior_predictive` after successful `bayes:` MCMC fits
  - row-wise posterior predictive means through the retained Bambi model and ArviZ
    `InferenceData`
  - support after both `bayes: regress` and `bayes: logit`, with deterministic guards for
    unsupported prediction modes and missing prerequisite state
  - focused parser, executor/backend, autocomplete, help topic, and CLI coverage
- Implemented the twelfth Phase 19 modern-extensions slice:
  - `estat bayes` after successful `bayes:` MCMC fits
  - deterministic MCMC diagnostics tables over retained ArviZ posterior state for
    `ess_bulk`, `ess_tail`, `r_hat`, `mcse_mean`, `mcse_sd`, and sampler divergence counts
  - support after both `bayes: regress` and `bayes: logit`, with deterministic
    `not_available` formatting for unavailable diagnostics and strict guards against legacy
    `bayes linear` state reuse
  - focused parser, executor/backend, autocomplete, help topic, and CLI coverage
- Implemented the thirteenth Phase 19 modern-extensions slice:
  - `bayesplot <trace|density|autocorrelation>` after successful `bayes:` MCMC fits
  - artifact-based Bayesian MCMC diagnostic plots using retained posterior draws
  - support for existing plot artifact options and config behavior: `saving(<path>)`, `noopen`,
    `artifact_dir`, `graph_format`, and `graph_open`
  - deterministic guards against missing `bayes:` state and legacy `bayes linear` state reuse
  - focused parser, executor/backend, CLI, shell, and help coverage
- Enhanced the Phase 3 `tabulate` command surface:
  - preserved legacy one-way and two-way frequency forms
  - added explicit multi-level `rows()` and `columns()` crosstab syntax
  - added command-level `if`, `by: tabulate`, sorted wide matrix output, and `missing` handling
  - added single-value aggregate cells through `values()` plus `stat(count|mean|sum|min|max)`
  - focused parser, executor/backend, CLI, shell, help, and docs coverage
- Extended the Phase 19 Bayesian posterior predictive workflow:
  - `predict <newvar>, posterior_predictive interval [level(<num>)]` after `bayes:` MCMC fits
  - deterministic mean, `<newvar>_lower`, and `<newvar>_upper` active-dataset columns
  - preserved mean-only `posterior_predictive` behavior and missing-row propagation
  - focused parser, executor/backend, CLI, shell, help, and docs coverage
- Implemented standard spatial autocorrelation diagnostics on OLS residuals:
  - `estat spatial, weights(<path>) id(<id_var>) [contiguity(queen|rook)]` and `estat spatial, coord(<lat_var> <lon_var>) [knn(<k>)]` after OLS `regress`
  - computes Moran's I test (`MoranRes`) and Lagrange Multiplier tests (`LMtests` for simple and robust lag/error and SARMA)
  - robust sample alignment and size validation between regression estimation sample and spatial weights
  - focused parser, executor/backend, shell completion, help, and docs coverage
- Implemented Phase 21 — Classical Statistical & Hypothesis Testing:
  - `test` command: performs Wald/F tests of linear restrictions ($R \beta = r$) or joint significance tests over model parameters.
  - `lincom` command: estimates and computes standard errors, t/z stats, p-values, and confidence intervals for linear combinations of coefficients.
  - `ttest` command: conducts one-sample, two-sample (equal/unequal variance), and paired t-tests on active variables.
  - focused parser, executor, formatter, autocompletions, help topic, and CLI integration tests.
- Implemented Phase 22 — Advanced Spatial Autoregressive Models:
  - `spregress` command supports `model(sarar)` for GMM Combo estimation.
  - Computes and prints spatial lag `rho` and spatial error `lambda` coefficients.
  - Supported out-of-sample prediction workflow for `spatial_lag` by dynamically constructing weight matrices ($W_{\text{new}}$).
  - focused parser, executor, formatter, CLI, shell autocomplete, and integration tests.
- Implemented Phase 23 — Data Recoding & Ingestion Expansion:
  - `recode` command: recodes numeric and categorical variable values/ranges using a sequence of rules (`inputs = output`).
    - Supports exact values, value lists, ranges (`min/max` keywords), and special cases (`missing`, `nonmissing`, `else`).
    - Supports writing to new variables via `generate(<new_varlist>)` or replacing in-place via `replace`.
    - Implemented typecast safety to prevent DuckDB binder errors during string recodes or mixed type coercions.
  - Expanded `use` command ingestion format support:
    - Loads `.csv` datasets with `delimiter(<char>)` and `has_header(true|false)` option parameters.
    - Loads `.feather` and `.arrow` datasets by registering them as temporary views via PyArrow.
  - focused parser, executor, backend, CLI autocomplete, help topics, and integration tests.
- Implemented Phase 13 slice 4 — Interactive HTML regression summaries & diagnostic plots:
  - `estat report` command generates a self-contained, responsive HTML file containing regression stats (outcome, predictors, estimator, covariance method, observations, R-squared, adjusted R-squared, root MSE).
  - Styled parameter estimates table with coefficients, standard errors, t-statistics, p-values, and 95% confidence intervals.
  - Interactive diagnostic plots (Residuals vs Fitted, Normal Q-Q, and Actual vs Fitted) rendered with Altair and embedded via Vega-Embed.
  - Supports `saving(path)` to customize the output location and `noopen` to disable automatic browser opening.
  - Robust validations (HTML/JS escaping, minimum sample size $N \ge 2$, and deterministic random downsampling for $N > 5000$ to prevent browser freezing).
  - focused parser, executor, autocompletions, help topic, and integration tests.

- Implemented Phase 24 P0 canonical Parquet-first workflow:
  - published `demos/canonical_parquet_eda.td` covering lazy load, inspection, missingness,
    transformation, grouped summaries, collapse, and Parquet export
  - added exact two-process script replay and exported-table equivalence checks
  - added observational wall-clock benchmark metrics to the integrated E2E reports
  - hardened HTML regression-report downsampling coverage against Altair dataset ordering and
    verified both sampled observations and the one-row reference line
- Implemented Phase 24 P0 read-only status transparency:
  - added `status` output for backend, source, active table, eager/lazy mode, materialization state,
    lazy engine, row-count knowledge, and column count
  - preserved lazy state for status inspection and recorded explicit `count` metadata
  - covered parser, executor, CLI/script, shell completion, help, and documentation contracts
- Implemented Phase 24 P0 materialization reason transparency:
  - reports the last tracked Polars lazy fallback in `status`
  - resets the reason when a new source or named table becomes active
  - rejects unsupported nested `by ...: status` before lazy materialization
- Implemented Phase 24 P0 last-operation transparency:
  - reports the last successfully executed command family in `status`
  - keeps `status` read-only and preserves the prior operation across failures
  - covers interactive shell, `-c`, and script state transitions
- Implemented Phase 24 P0 materialization-reason taxonomy:
  - distinguishes `eager operation` from the specific `polars fallback` reason
  - restricts generic eager-transition detection to DuckDB-lazy state
  - preserves source/table reset and success-only reason semantics
- Implemented Phase 24 P0 identifier overwrite and atomic error semantics:
  - defined generate, rename, replace, and recode-generated target rules
  - preserved active schema, rows, execution metadata, and success-only transparency metadata on
    validation failures across eager, DuckDB-lazy, and Polars-lazy paths
  - rejected duplicate recode-generated identifiers and preflighted Polars-lazy write validation
- Implemented Phase 24 P0 identifier spelling and quoted identifiers:
  - defined exact case-sensitive bare identifiers and backtick quoting
  - preserved quoted names through command wrappers, control-word parsing, CLI/script paths, and
    Bayes formula construction
- Implemented Phase 24 P0 missing predicate semantics:
  - defined SQL NULL/Python None behavior for keep, drop, replace, summarize, codebook, tabulate,
    and bar
  - aligned eager, DuckDB-lazy, and Polars-lazy keep/drop filtering for missing predicate results
  - documented and regression-tested aggregate missingness and stable missing bar rendering
- Implemented Phase 24 P0 explicit missing predicates:
  - added a case-insensitive unquoted `null` literal while preserving quoted `` `null` `` identifiers
  - defined null-aware equality/inequality, direct all-missing assignment, and cross-engine filters
  - rejected unsupported null arithmetic/functions and preserved Polars-lazy state on invalid tabulate
    conditions
- Implemented Phase 24 P0 expression coercion:
  - defined numeric, string, boolean, other, and null expression domains
  - allowed numeric-family compatibility while rejecting mixed-domain comparisons, arithmetic, and
    functions with deterministic diagnostics
  - required boolean or missing predicates and same-domain/null replacement targets
  - validated Polars-lazy writes and tabulates before fallback materialization
- Implemented Phase 24 P0 arithmetic result and non-finite-value policy:
  - defined missing propagation, row-level zero-denominator and invalid numeric-function behavior,
    and computed NaN/infinity normalization
  - preserved direct source non-finite values while rejecting unsigned subtraction/unary minus
  - aligned eager, DuckDB-lazy, and Polars-lazy arithmetic predicates, including Decimal operands
  - explicitly deferred exact arithmetic widths, overflow diagnostics, active row order, and
    broader ordering policy
- Implemented Phase 24 P0 grouped-result ordering:
  - defined native numeric/text/boolean ordering, missing-last behavior, and deterministic bar ties
  - preserved exact integer/Decimal keys and canonicalized NaN keys in wide tabulate assembly
  - kept visualization category order aligned with backend output across eager and lazy paths
  - explicitly deferred active row order, arbitrary SQL ordering, and categorical ordering
- Implemented Phase 24 P0 active row-order semantics:
  - defined current sequence for head/tail, keep/drop filters, zero limits, and missing predicates
  - explicitly enabled DuckDB insertion-order preservation for sequence-sensitive operations
  - isolated cross-engine projection/value-transform coverage and routed Polars-lazy recode through
    validated fallback
  - explicitly deferred relation-changing order, unordered SQL, and categorical ordering
- Implemented Phase 24 P0 SQL and named-table order semantics:
  - defined explicit `order by` result sequences, tie-breaker requirements, and `sql ... into` storage
  - preserved ordered sequences through isolated named-table reactivation and existing state resets
  - added multiline parser, exact CLI, help, and eager/lazy SQL regressions
  - explicitly deferred unordered SQL, append/join/reshape order, and categorical ordering
- Implemented Phase 24 P0 append row-order semantics:
  - explicitly snapshot each input sequence and order active rows before named-table rows
  - preserved duplicate rows and made head/tail consume the combined sequence deterministically
  - validated append table/schema failures before Polars fallback materialization
  - explicitly deferred join/reshape and categorical ordering
- Implemented Phase 24 P0 join row-order semantics:
  - explicitly preserved active-row order and named-table match order for inner and left joins
  - preserved duplicate right-side matches without global sorting or deduplication
  - kept append, reshape, and categorical ordering as separate contracts
- Implemented Phase 24 P0 reshape row-order semantics:
  - preserved source-row and exact j-value discovery order for long expansion
  - preserved first-appearance identifier-group order for wide output
  - prevalidated long/wide failures before Polars fallback and reserved public output names
  - explicitly deferred categorical ordering
- Implemented Phase 24 P0 categorical ordering semantics:
  - defined native numeric, text, and boolean category order independently of rendered text
  - defined tabulate missing omission/inclusion and bar descending-count/tie order
  - added collision-safe rendering for missing/reserved-looking labels and multi-key headers
  - verified fresh eager, DuckDB-lazy, and Polars-lazy bar artifacts plus CLI/help/docs coverage
  - explicitly deferred exact arithmetic result widths and overflow policy

## Present

- Feature: Phase 24 P0 exact integer arithmetic result widths
  Status: Active
  Started: 2026-07-13
  Branch: feat/phase24-exact-arithmetic

  Summary:
  Define exact result widths and deterministic overflow behavior for integral arithmetic in existing
  expressions without adding command syntax.

  Verification:
  - integral `+`, `-`, `*`, and unary minus results use exact `DECIMAL(38,0)` storage
  - representable signed and unsigned integer results preserve their exact values across eager,
    DuckDB-lazy, and Polars-lazy write paths
  - results outside the bounded exact width become missing rather than wrapping or failing the whole
    row-preserving transformation
  - real division, floating arithmetic, decimal-scale arithmetic, and invalid-function behavior keep
    their existing contracts
  - CLI, help, docs, full tests, and type/lint checks pass

  Out of Scope:
  - stable overflow error/warning output, arbitrary-precision arithmetic, decimal-scale/precision
    redesign, float-width guarantees, new operators or functions, randomness, estimation samples,
    operation lineage, machine output, and exit-code redesign
  - new commands, new backends, estimators, connectors, or plugins

## Future

- **P0 — Phase 24 product-center stabilization and public-preview gate**
  - pause net-new estimator families until the Phase 24 exit gate in `docs/dev_phase.md` is met
  - define stable cross-command semantics for identifiers, missing values, coercion, arithmetic,
    categories, ordering, overwrite behavior, estimation samples, randomness, errors, and exits
  - extend execution transparency with full operation lineage, retained estimation samples, and
    backend-internal materialization traces after this bounded reason taxonomy
  - verification:
    - the canonical workflow passes from a clean install in interactive and script modes
    - documented semantics have focused parser/executor/backend/CLI tests
    - transparency output is deterministic and does not trigger hidden materialization
  - out of scope: new estimator families, broad remote connectors, or public plugin APIs
- **P1 — Agent and automation interface**
  - specify JSON or JSON Lines output, schema/result metadata, stable exit codes, structured command
    discovery, dry-run/explain behavior, and repair-oriented diagnostics
  - verification:
    - representative EDA commands have versioned, snapshot-tested machine-readable envelopes
    - interactive, script, and `-c` execution produce equivalent state transitions
- **P1 — Differential and statistical assurance**
  - add DuckDB/Polars and eager/lazy equivalence fixtures for their shared supported surface
  - cover quoting, Unicode, paths, missingness, type edges, and terminal golden output
  - create an estimator support matrix with options, sample rules, covariance conventions,
    prediction semantics, trusted references, and tolerated numerical differences
  - verification:
    - every advertised estimator family has a trusted differential fixture or an explicit
      unsupported/unverified label
    - estimation-family invalidation and post-estimation compatibility are tested
- **P1 — Layered dependency and extension architecture**
  - formalize `tabdat-core`, `tabdat-stats`, and specialized Bayes/spatial/R/ML capability layers
    using the existing typed adapter registry
  - measure install size, cold startup, portability, and failure behavior before choosing optional
    dependency groups or separate distributions
  - verification:
    - core EDA runs without importing or requiring specialized runtimes
    - missing optional capabilities fail with concise installation guidance
  - out of scope: separate repositories or a packaging split without measurements and an ADR
- **P2 — Public identity, documentation separation, and validation**
  - settle Product/Repository/PyPI/Python-package/CLI naming after availability research
  - separate durable architecture and invariants from capability status and release history; record
    DuckDB-primary, Polars fallback, R adapters, estimator-state invalidation, and dependency
    layering as ADRs
  - run release-readiness checks for installation, portability, startup latency, walkthroughs,
    examples, compatibility, and external user feedback before choosing a preview version
  - verification:
    - naming and versioning decisions have migration plans and ADRs
    - architecture has no cumulative phase ledger; capability and history have named homes

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
- Deferred Phase 19 modern extensions:
  - Richer Bayesian posterior predictive workflows: add explicit out-of-sample Bayesian prediction workflows beyond the current active-dataset posterior predictive mean and interval columns.
  - library strategy:
    - approach (1): `scikit-learn` for ML workflows, `pymc`/`bambi` for Bayesian workflows, and `pysal` (`spreg`) for spatial econometrics
    - approach (2): `brms`/`rstanarm` and `spdep`/`spatialreg` via `rpy2` where R has stronger coverage
    - approach (3): narrow `numpy`/`scipy` custom implementations only when no mature backend fits
- Remaining & Deferred Roadmap Items:
  - **Dynamic / Custom User Plugins**: Exposing command and result interfaces as public APIs for third-party extension packages, instead of just the internal extension registry (Phase 18).
  - **Broader Remote Connectors**: Database connectors (e.g. Postgres, Snowflake, BigQuery) and remote object storage credentials management (Phase 11 / Phase 18).
  - **Full Polars-Native Execution Backend**: Deep lazy execution optimizations completely within Polars instead of materializing to DuckDB for unsupported commands (Phase 7 / Phase 10).
  - **Advanced dynamic panel GMM / structural estimators**: Fuller dynamic panel model GMM and structural model replication tools (Phase 17).
