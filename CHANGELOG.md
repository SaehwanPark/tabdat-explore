# Changelog

All notable project changes are tracked here.

## Unreleased

### Changed

- Reprioritized the SDD roadmap around a Phase 24 product-center stabilization and public-preview
  gate: canonical Parquet workflow, language semantics, execution transparency, automation output,
  differential assurance, measured dependency layering, naming, and external validation now
  precede new estimator-family expansion.
- Started the Phase 24 read-only `status` transparency slice on a dedicated feature branch; richer
  execution explanation and machine-readable output remain deferred.
- Started the Phase 24 materialization-reason transparency slice; it exposes the tracked Polars
  lazy-to-eager fallback cause while broader operation lineage remains deferred.
- Started the Phase 24 last-operation transparency slice; `status` will expose the last successful
  command while full operation lineage remains deferred.
- Started the Phase 24 materialization-reason taxonomy slice; successful eager transitions will be
  distinguished from Polars fallback and source/table resets.
- Started the Phase 24 identifier overwrite and atomic-error semantics slice; broader language
  policy remains queued behind this initial write-contract increment.
- Started the Phase 24 identifier spelling and quoted-identifier semantics slice; missingness,
  coercion, and broader language policy remain queued.
- Started the Phase 24 missing-predicate semantics slice; explicit missing predicates and coercion
  remain queued.
- Started the Phase 24 explicit missing-predicate slice; null-aware equality is bounded separately
  from coercion and broader arithmetic policy.
- Started the Phase 24 expression coercion contract slice; numeric-family compatibility and
  deterministic mixed-domain failures are bounded before broader arithmetic expansion.

### Added

- Added the Phase 24 canonical Parquet-first workflow:
  - `demos/canonical_parquet_eda.td` publishes a lazy-load, inspect, transform, group, collapse,
    and export journey over a Titanic-shaped Parquet file.
  - Integrated scenario `s6_canonical_parquet_workflow` replays the script twice, compares exact
    transcripts and exported tables, and records observational wall-clock timings.
- Hardened HTML regression-report downsampling coverage against Altair dataset ordering, verifying
  both sampled observations and the one-row reference line without changing report rendering.

- Added `estat report` post-estimation command for standard linear regressions (`regress`):
  - Generates a self-contained, beautiful, responsive HTML page with regression stats (Outcome, Predictors, Estimator, Covariance, Observations, R-squared, Adj R-squared, Root MSE).
  - Includes a styled coefficients table with standard error, t-stat, p-value, and 95% confidence intervals.
  - Embeds three interactive diagnostic plots (Residuals vs Fitted, Normal Q-Q, Actual vs Fitted) rendered with Altair and Vega-Lite/Vega-Embed.
  - Supports `saving(path)` option to specify output location, and `noopen` to disable automatic browser opening.
  - Implements HTML/JS escaping for special character safety, bounds validation for datasets with $N < 2$, and random downsampling to at most 5,000 points to prevent browser freeze.


## [0.23.0] — 2026-06-18

Phase 23 Data Recoding & Ingestion Expansion, Classical Hypothesis Testing, Advanced Spatial Models, and Bayesian Predictive Intervals.

### Added

- Added data value/range-based recoding via the `recode` command:
  - Supports exact values, value lists, numeric ranges, and special keywords (`min`, `max`, `missing`, `nonmissing`, `else`).
  - Supports writing outputs to new variables via `generate(<new_varlist>)` or replacing in-place via `replace`.
  - Implements typecast safety to prevent DuckDB binder errors during string recodes or mixed type coercions.
- Expanded `use` command ingestion format support:
  - Loads `.csv` datasets with `delimiter(<char>)` and `has_header(true|false)` option parameters.
  - Loads `.feather` and `.arrow` datasets by registering them as temporary views via PyArrow.
- Added out-of-sample prediction support for `predict ..., spatial_lag` after spatial regressions (`spregress`):
  - Dynamically builds a new $K$-Nearest Neighbors (KNN) weights matrix or subsets/aligns a pre-computed spatial weights file for the new active dataset sample.
  - Computes spatial lag reduced-form predictions via matrix solvers: $\hat{y}_{\text{new}} = (I - \hat{\rho} W_{\text{new}})^{-1} X_{\text{new}} \hat{\beta}$.
  - Gracefully handles missing values and preserves the existing same-sample prediction optimization.
- Added Classical Hypothesis Testing commands (`test`, `lincom`, `ttest`):
  - `test` performs Wald/F tests of linear restrictions ($R \beta = r$) or joint significance tests over parameters after active regressions (`regress` or `ivregress`).
  - `lincom` computes standard errors, stats, p-values, and confidence intervals for linear combinations of coefficients.
  - `ttest` conducts one-sample, two-sample (equal/unequal variance), and paired t-tests on active variables.
  - Formats all testing outputs into Stata-style aligned tables.
- Added standard spatial autocorrelation diagnostics on OLS residuals via `estat spatial`:
  - Supports both `estat spatial, weights(<path>) id(<id_var>) [contiguity(queen|rook)]` and
    `estat spatial, coord(<lat_var> <lon_var>) [knn(<k>)]` subcommands.
  - Computes Moran's I statistic, expectation, variance, z-statistic, and p-value.
  - Computes Lagrange Multiplier (LM) tests for simple and robust lag/error, plus spatial SARMA.
  - Validates and aligns spatial weight matrices with the regression estimation sample.
- Added Bayesian posterior predictive intervals for `bayes:` MCMC models:
  - `predict <newvar>, posterior_predictive interval [level(<num>)]` now adds mean, lower, and
    upper posterior predictive columns.
  - Existing `predict <newvar>, posterior_predictive` mean-only behavior is preserved.
  - Interval predictions validate target collisions atomically before replacing the active
    dataset.
- Enhanced `tabulate` with explicit `rows()`/`columns()` multi-level crosstabs, command-level `if`,
  `by:` support, and single-value cell aggregation through `values()` plus
  `stat(count|mean|sum|min|max)`.

---

## [0.22.0] — 2026-06-10

Phase 19 Bayesian MCMC diagnostic plot artifacts via `bayesplot`.

### Added

- Added `bayesplot <trace|density|autocorrelation>` after successful `bayes:` MCMC fits:
  - Saves deterministic `.svg`/`.png` plot artifacts through the existing plot artifact boundary.
  - Supports `saving(<path>)` and `noopen`, plus existing `artifact_dir`, `graph_format`, and
    `graph_open` configuration behavior.
  - Uses retained posterior draws from the existing Bambi/ArviZ state and rejects missing-prior
    or legacy `bayes linear` state with explicit guards.
  - Added parser, executor, CLI, shell-completion, and help coverage plus updated spec and
    architecture notes.

---

## [0.21.0] — 2026-06-10

Phase 19 Bayesian MCMC diagnostics via `estat bayes`.

### Added

- Added `estat bayes` after successful `bayes:` MCMC fits:
  - Supports both `bayes: regress` and `bayes: logit` using retained ArviZ posterior state.
  - Reports deterministic in-terminal diagnostics for `ess_bulk`, `ess_tail`, `r_hat`,
    `mcse_mean`, `mcse_sd`, and sampler `divergence_count`.
  - Normalizes unavailable diagnostics from small-chain runs to `not_available` instead of
    surfacing raw `nan`.
  - Rejects missing-prior and legacy `bayes linear` state with explicit guards.
  - Added parser, executor, CLI, shell-completion, and help coverage plus updated spec and
    architecture notes.

---

## [0.20.0] — 2026-06-10

Phase 19 Bayesian posterior predictive workflow support.

### Added

- Added `predict <newvar>, posterior_predictive` after successful `bayes:` MCMC fits:
  - Supports both `bayes: regress` and `bayes: logit` states through the retained Bambi model and
    ArviZ `InferenceData`.
  - Writes row-wise posterior predictive means into the active dataset while preserving active row
    order.
  - Emits deterministic guards for unsupported `predict` modes after `bayes:` and for
    `posterior_predictive` without a prior `bayes:` fit.
  - Added parser, executor, CLI, and shell-completion coverage plus updated help documentation.

---

## [0.19.0] — 2026-06-08

Phase 19 general Bayesian MCMC command prefix support.

### Added

- Added Phase 19 general Bayesian MCMC prefix command `bayes:`:
  - Supports `bayes [, options]: regress` and `bayes [, options]: logit` using Python-first `bambi` as the MCMC backend.
  - Implemented MCMC specification options: `draws`, `burnin`/`tune`, `chains`, `thin`, and `seed`/`rseed`.
  - Added support for custom prior distributions via `prior(variable, distribution)` with `normal(mu, sigma)` and `uniform(lower, upper)` distribution specifications.
  - Formatted MCMC posterior summary statistics in terminal tables with `Mean`, `Std. Dev.`, `MCSE`, and `Cred. Interval` headers.
  - Added autocompletions for prefix options and inner commands, help documentation topic, and focused integration tests.

---

## [0.18.0] — 2026-06-08

Phase 19 spatial weight matrix configuration and GIS file ingestion support.

### Added

- Added Phase 19 spatial weight matrix configuration and GIS file ingestion in `spregress` command:
  - Supports loading pre-computed spatial weight matrices from `.gal`, `.gwt`, and `.shp` files via `weights(path)` and `id(id_var)`.
  - Added Rook and Queen polygon contiguity weights from shapefiles via `contiguity(queen|rook)` option.
  - Implemented case-insensitive DBF column resolution and dynamic matrix subsetting and reordering to align with regression sample.
  - Updated predict `xb` and `spatial_lag` to support file-based weights estimations.
  - Added shell completions, help documentation, and comprehensive unit/integration test coverage.

---

## [0.17.0] — 2026-06-08

Phase 19 partial-linear DML treatment-effect estimation starter.

### Added

- Added the eighth Phase 19 modern-extensions slice with
  `dml linear <y> <controls>, treat(<tvar>) [folds(<int>) alpha(<num>) robust seed(<int>) noconstant]`,
  combining Python-first `scikit-learn` cross-fitted Lasso nuisances with a `statsmodels` OLS final
  stage for binary-treatment ATE estimation.
- Added `estat dml` post-estimation diagnostics with fold count, treated/control counts, nuisance
  treatment-fit summaries, and overlap checks.
- Added typed extension-registry estimator metadata for `dml`
  (`python:sklearn.linear_model.Lasso+statsmodels.OLS`) with focused registry tests.

---

## [0.16.0] — 2026-06-07

Phase 19 ML/spatial modern extensions and Phase 20 doubly robust DID; ROP
dependency cleanup, Basedpyright adoption, and monads boundary hardening.

### Added

- Added the seventh Phase 19 modern-extensions slice with
  `postlasso linear <y> <xvars>[, alpha(<num>) robust noconstant]`, combining Python-first
  `scikit-learn` Lasso predictor selection with `statsmodels` OLS refit inference, deterministic
  no-selection behavior, formatter output, shell autocomplete, help, extension-registry metadata,
  and focused parser/executor/CLI coverage.
- Added the sixth Phase 19 modern-extensions slice with same-sample
  `predict <newvar>, spatial_lag` support after `spregress ... model(lag)`, preserving existing
  `predict ..., xb` support and adding deterministic guards for incompatible spatial states.
- Added Phase 20: Doubly Robust Difference-in-Differences (`drdid`):
  - `drdid <y> [covariates], treat(<var>) post(<var>) [method(or|ipw|aipw) robust bootstrap(<n>) seed(<n>)]` command with Python-first outcome regression (OR), inverse probability weighting (IPW), and augmented doubly robust (AIPW) ATT estimators.
  - post-estimation diagnostics: `estat drdid` prints treated/control cell counts, propensity score summaries, and overlap checks.
  - robust and bootstrap standard error estimation with explicit seed support.
  - mocked R fallback calling CRAN `DRDID` R package via `rpy2` on error.
  - visible notes when otherwise eligible units are dropped because covariates have missing or non-finite values.
  - interactive shell autocompletions, in-app help topic, and comprehensive integration tests.
- Added the fifth Phase 19 modern-extensions slice: cross-validation wrappers `cvlasso`,
  `cvridge`, and `cvelasticnet` that automatically perform K-fold cross-validation to select
  optimal hyperparameters using custom grid search on scikit-learn estimators, saving structured
  CV reports to the artifact directory.
- Added prediction support (`predict <newvar>, xb`) after successful `cvlasso`, `cvridge`, and
  `cvelasticnet` models.
- Added the fourth Phase 19 modern-extensions slice with
  `ridge linear <y> <xvars>[, alpha(<num>) noconstant]` via Python-first `scikit-learn` `Ridge`
  L2-penalized linear estimation, and
  `elasticnet linear <y> <xvars>[, alpha(<num>) l1_ratio(<num>) noconstant]` via Python-first
  `scikit-learn` `ElasticNet` combined L1/L2-penalized linear estimation, deterministic formatter
  output, and focused parser/executor/CLI/shell/help/extension-registry coverage.
- Added deterministic `predict <newvar>[, xb]` routing after `ridge` and `elasticnet` with strict
  guards that reject `residuals` and `pr`.
- Added typed extension-registry estimator metadata for `ridge`
  (`python:sklearn.linear_model.Ridge`) and `elasticnet`
  (`python:sklearn.linear_model.ElasticNet`) with focused registry tests.
- Added the third Phase 19 modern-extensions slice with
  `spregress <y> <xvars>, coord(<lat> <lon>) [model(lag|error) knn(<k>) robust]` command,
  on-the-fly row-standardized KNN spatial weights matrices, ML lag/error and GMM-based
  heteroskedasticity-robust estimators (`spreg`), bounded exogenous linear prediction,
  integrated in-app help, autocomplete, extension registry, and comprehensive tests.
- Added the second Phase 19 modern-extensions slice with
  `bayes linear <y> <xvars>[, n_iter(<int>) tol(<num>) noconstant]` Bayesian ML starter via
  Python-first `scikit-learn` `BayesianRidge`, deterministic result formatting, and focused
  parser/executor/CLI/shell/help/extension-registry coverage.
- Added the first Phase 19 modern-extensions slice with
  `lasso linear <y> <xvars>[, alpha(<num>) noconstant]` via Python-first
  `scikit-learn` L1-penalized linear estimation, deterministic formatter output, and focused
  parser/executor/CLI/shell/help coverage.
- Added deterministic `predict <newvar>[, xb]` routing after `lasso` with strict guards that
  reject `residuals` and `pr`.
- Added `scikit-learn` as the Phase 19 Python-first ML starter dependency.
- Added typed extension-registry estimator metadata for `lasso`
  (`python:sklearn.linear_model.Lasso`) with focused registry tests.

### Changed

- Cleaned `SPEC.md` so completed work no longer appears in `Present` or `Future`, leaving only
  active guidance and genuinely unfinished future slices.
- Changed the shared `predict` command surface to accept `spatial_lag` as a bounded spatial-only
  mode after `spregress`.
- Replaced Pyright tooling with Basedpyright as a development dependency and configured scoped
  `src/tabdat` type checking.
- Changed `predict` prerequisite diagnostics to include lasso model-state routing.
- Moved `comp-builders` from the previous Git direct dependency to the published PyPI package,
  expanded the local `tabdat.monads` boundary with async-result helpers, and centralized parser
  `Result` flow while preserving public `ParseError` behavior.

### Fixed

- Fixed Pyright type-check failures in parser option extraction, optional-value monad helpers,
  and integrated E2E PTY spawning.
- Fixed interactive shell Ctrl-C handling so prompt-toolkit completion interrupts return to the
  prompt instead of terminating with a traceback.

---

## [0.15.0]

Phase 17 advanced empirical methods and Phase 18 ingestion, demos, and extension registry.

### Added

- Added the seventh Phase 17 advanced empirical-methods slice with
  `lowess <y> <x>, gen(<newvar>) [bandwidth=<0,1>]`, bounded semiparametric/nonparametric
  smoothing through Python-first `statsmodels.nonparametric.smoothers_lowess.lowess`,
  deterministic transform output, and focused parser/executor/CLI/shell/help coverage.
- Added the sixth Phase 17 advanced empirical-methods slice with
  `xtlogit <y> <xvars>, fe [robust]`, required prior panel metadata
  (`panel <id_var> <time_var>`), bounded fixed-effects nonlinear-panel execution through
  Python-first `statsmodels.discrete.conditional_models.ConditionalLogit`, deterministic output,
  and focused parser/executor/CLI/shell/help coverage.
- Added the fifth Phase 17 advanced empirical-methods slice with deterministic `estat overid`
  diagnostics after successful `xtabond`, deterministic `predict <newvar>[, xb residuals]` routing
  after `xtabond`, strict panel/variable compatibility guards, and focused
  parser/executor/CLI/shell/help coverage.
- Added the fourth Phase 17 advanced empirical-methods slice with
  `xtabond <y> [xvars] [, robust lags(#) instlag(#)]`, strict lag-depth/instrument-lag
  validation, bounded configurable dynamic-panel execution over Python-first `linearmodels.iv.IVGMM`
  with R fallback retained, and focused parser/executor/CLI/shell/help coverage.
- Added expanded deterministic `estat did` diagnostics after successful `did`, including DID cell
  counts, cell means, treated/untreated changes, and raw diff-in-diff contrasts in addition to
  interaction-coefficient metrics.
- Added the third Phase 17 advanced empirical-methods slice with
  `xtabond <y> [xvars] [, robust]`, required prior panel metadata
  (`panel <id_var> <time_var>`), bounded dynamic-panel AR(1) GMM starter execution through
  Python-first `linearmodels.iv.IVGMM` plus R fallback, deterministic nonrobust/robust covariance
  output, and focused parser/executor/CLI/shell/help coverage.
- Added deterministic `estat did` diagnostics after successful `did`.
- Added the second Phase 17 advanced empirical-methods slice with
  `did <y> [controls], treat(<var>) post(<var>) [robust]`, required prior panel metadata
  (`panel <id_var> <time_var>`), bounded two-way fixed-effects execution through
  `linearmodels.PanelOLS`, deterministic nonrobust/robust covariance output, and focused
  parser/executor/CLI/shell/help coverage.
- Added deterministic `predict <newvar>[, xb]` routing after `did`.
- Added the first Phase 17 advanced empirical-methods slice with
  `qreg <y> <xvars>[, quantile(<0,1>) robust noconstant]`, deterministic
  nonrobust/robust covariance output, `predict <newvar>[, xb residuals]` routing after `qreg`,
  `estat residuals` diagnostics after `qreg`, and focused parser/executor/CLI/shell/help coverage.
- Added the fourth Phase 18 ecosystem and extension-layer slice with a typed internal
  extension-registry contract (`src/tabdat/extension_registry.py`) for ingestion and estimator
  adapter boundaries, centralized local/remote lazy-ingestion capability metadata, centralized
  estimator backend metadata for `xtabond`/`tobit`/`heckman`, and focused registry contract tests.
- Added the third Phase 18 advanced econometrics replication demo slice with remote Stata URL
  loader bypass in `inspect_parquet`, linear prediction (`predict ..., xb|residuals`) after
  `heckman`, and three classic Stata-based demo scripts under `demos/`
  (`heckman_mroz.td`, `ivregress_card.td`, `panel_union.td`) with automated test coverage.
- Added eager `use` acceptance of local and HTTP/HTTPS Stata `.dta` files through
  `pandas.read_stata`; `use ..., lazy` remains Parquet-only.

### Changed

- Changed `predict` prerequisite diagnostics to include `did` model-state routing.
- Changed `predict` prerequisite diagnostics to include `qreg` model-state routing while
  preserving existing binary-choice and count-model boundaries.

---

## [0.14.0]

Phase 16 specialized likelihood models: count, zero-inflated, and parametric survival regression.

### Added

- Added the fourth Phase 16 specialized likelihood-model slice with
  `streg <time_var> <xvars>, failure(<event_var>) dist(weibull|exponential)
  [robust cluster(<var>) noconstant]`, bounded parametric duration/survival execution,
  deterministic nonrobust/robust/cluster covariance output, and focused
  parser/executor/CLI/shell/help coverage.
- Added the third Phase 16 specialized likelihood-model slice with
  `zip <y> <xvars>, inflate(<zvars>) [robust cluster(<var>) noconstant]` and
  `zinb <y> <xvars>, inflate(<zvars>) [robust cluster(<var>) noconstant]`,
  deterministic nonrobust/robust/cluster covariance output, `predict <newvar>[, xb residuals]`
  routing after `zip`/`zinb`, and `estat gof` post-estimation diagnostics with focused
  parser/executor/CLI/shell/help coverage.
- Added the second Phase 16 specialized likelihood-model slice with
  `nbreg <y> <xvars>[, robust cluster(<var>) noconstant]`, deterministic
  nonrobust/robust/cluster covariance output, `predict <newvar>[, xb residuals]` routing after
  `nbreg`, and `estat gof` post-estimation diagnostics with focused
  parser/executor/CLI/shell/help coverage.
- Added the first Phase 16 specialized likelihood-model slice with
  `poisson <y> <xvars>[, robust cluster(<var>) noconstant]`, deterministic nonrobust/robust/cluster
  covariance output, `predict <newvar>[, xb residuals]` routing after `poisson`, and `estat gof`
  post-estimation diagnostics with focused parser/executor/CLI/shell/help coverage.

---

## [0.13.0]

Phase 15 nonlinear estimation core: binary choice, censored, sample-selection, and NLS regression.

### Added

- Added the seventh Phase 15 nonlinear estimation core slice with
  `nl <y> = <expr>, params(<params>) start(<values>) [robust noconstant]`,
  bounded nonlinear least-squares estimation, deterministic nonrobust/robust covariance labels,
  `predict` support (`xb` and `residuals`) after `nl`, and focused parser/executor/CLI/shell
  coverage.
- Added the sixth Phase 15 nonlinear estimation core slice with
  `heckman <y> <xvars>, selectdep(<var>) select(<vars>) [robust cluster(<var>) noconstant]`,
  deterministic bounded sample-selection execution, and focused parser/executor/CLI/shell coverage.
- Added the fifth Phase 15 nonlinear estimation core slice with
  `tobit <y> <xvars>, ll(<num>) [ul(<num>) robust cluster(<var>) noconstant]`, deterministic
  bounded output/guards, and focused parser/executor/CLI/shell coverage.
- Added the fourth Phase 15 nonlinear estimation core slice with bounded binary-choice prediction
  routing via `predict <newvar>[, xb residuals pr]`, including `pr` support after `logit`/`probit`
  and focused parser/executor/CLI/shell coverage.
- Added the third Phase 15 nonlinear estimation core slice with `estat margins` after `logit` or
  `probit`, deterministic predictor-level marginal-effects output (`dy_dx`, `std_error`,
  `statistic`, `p_value`, `ci_lower`, `ci_upper`), and focused parser/executor/CLI/shell coverage.
- Added the second Phase 15 nonlinear estimation core slice with
  `probit <y> <xvars>[, robust cluster(<var>) noconstant]`, Python-first `statsmodels` probit
  execution, deterministic pseudo R-squared and coefficient output, and focused
  parser/executor/CLI/shell coverage.
- Added the first Phase 15 nonlinear estimation core slice with
  `logit <y> <xvars>[, robust cluster(<var>) noconstant]`, Python-first `statsmodels` logit
  execution, deterministic pseudo R-squared and coefficient output, and focused
  parser/executor/CLI/shell coverage.
- Added `rpy2` as the bounded Phase 15 adapter dependency for R-backed Tobit execution.

### Changed

- Changed `predict` routing so binary-model state (`logit`/`probit`) now supports `xb` and `pr`,
  while preserving existing linear/control-function prediction behavior and keeping binary
  residual prediction out of scope.
- Changed binary-choice estimation-state handling so `logit` and `probit` both register compatible
  post-estimation model state for `estat margins` while preserving existing `predict` and other
  `estat` family boundaries.
- Changed estimation-state handling so `logit` clears incompatible prior estimation family state
  (`regress`, `ivregress`, `cfregress`, and `xtreg`) before later post-estimation usage.

---

## [0.12.0]

Phase 14 endogeneity foundations and panel econometrics (thirteen slices covering IV, control-function, and panel methods).

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
- Added the third Phase 14 panel-model starter slice with
  `xtreg <y> <xvars>, fe|re[, robust cluster(<var>)]`, required `panel` metadata preconditions,
  `estat hausman` for matching FE/RE fits, deterministic formatter output, and focused
  parser/executor/CLI/shell coverage.
- Added the second Phase 14 diagnostics slice with `estat firststage` and `estat overid` over
  `ivregress` model state, deterministic Sargan/Wooldridge overidentification output, and focused
  parser/executor/CLI/shell coverage.
- Added the first Phase 14 endogeneity foundations slice with
  `ivregress 2sls <y> [exog_vars], endog(<var>) iv(<vars>)[, robust cluster(<var>) noconstant]`,
  Python-first `linearmodels` IV2SLS execution, deterministic formatter output, and focused
  parser/executor/CLI/shell coverage.
- Added `linearmodels` as the Phase 14 Python-first IV/2SLS backend dependency.

### Changed

- Changed estimation-state handling so `regress`, `ivregress`, and `xtreg` clear incompatible
  prior model-family state before later `predict`/`estat` usage.
- Updated SDD state (`SPEC.md`, `ARCHITECTURE.md`, and `README.md`) to record completed Phase 13
  hardening and the initial Phase 14 `ivregress 2sls` slice.

---

## [0.11.0]

Phase 12 estimation substrate and Phase 13 linear econometrics (`regress`, `predict`, `estat`).

### Added

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
- Added Phase 12 estimation substrate with reusable statistical primitives, bootstrap resampling,
  least-squares contracts, and shared MLE/GMM estimation interfaces plus focused tests.

### Changed

- Updated `SPEC.md`, `docs/dev_phase.md`, and `ARCHITECTURE.md` to define a Phase 13+
  statistical implementation priority order: Python libraries first, R via `rpy2` second, and
  lower-level `numpy`/`scipy` implementations last.
- Updated SDD state so `SPEC.md` records Phase 12 estimation substrate as implemented.

---

## [0.10.0]

Phase 10 execution and state foundations, Phase 11 data workflow primitives (join, append, reshape,
panel), script reproducibility (seed, let, if/else/end), remote Parquet, and monads boundary.

### Added

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

### Changed

- Reorganized the post-Phase-9 roadmap across `docs/dev_phase.md` and `SPEC.md` into an
  interleaved Phase 10–19 sequence that stages execution/state foundations, reproducibility and
  data-workflow primitives, core econometrics coverage, advanced empirical methods, and late
  ecosystem extensions coherently.
- Changed structured parser failure composition from handwritten `Either` helpers to
  `comp-builders` `Result` values while preserving the public `ParseError` behavior.

### Removed

- Removed the external PyMonad dependency in favor of local `tabdat.monads` helpers.

---

## [0.9.0]

Phase 9 configuration and persistence (`set`, `.tabdat.toml`, `save`, `export`).

### Added

- Added Phase 9 export widening with suffix-driven local `.parquet`, `.csv`, and `.feather`
  `export`, distinct `Exported:` CLI output, and focused parser, executor, and CLI coverage.
- Added a bounded real Phase 10 Polars lazy execution slice for local Parquet projection,
  row-filtering, count, and preview commands, plus explicit eager fallback for unsupported
  commands.
- Added Phase 9 startup config fallback through XDG user config at
  `$XDG_CONFIG_HOME/tabdat/config.toml` or `~/.config/tabdat/config.toml` when no explicit
  `--config` or project-local `.tabdat.toml` is present.
- Added an integrated public-dataset E2E harness and run documentation for the Titanic batch,
  interactive shell, NYC taxi lazy-scale, and Penguins script reproducibility scenarios.
- Added Phase 9 configuration and persistence with `.tabdat.toml`, `--config <path>`, runtime
  `set graph_format`, `set artifact_dir`, and `set graph_open`, config-aware plot defaults,
  live `count` execution for lazy datasets, Parquet `save`, and multi-format `export`.

### Changed

- Updated script reproducibility integrated-E2E expectations to match current `export` output
  wording (`Exported:`).

---

## [0.8.0]

Phase 8 scripting and reproducibility (`tabdat -f`, `run`, multiline SQL, script diagnostics).

### Added

- Added Phase 8 scripting and reproducibility with `tabdat -f <script>`, positional script
  execution, interactive and nested `run <script>`, deterministic script metadata, command
  transcripts, multiline SQL script blocks, line-numbered script errors, and script-mode plot
  auto-open suppression.

---

## [0.7.0]

Phase 7 lazy execution entrypoint and local typed monad helpers.

### Added

- Added local typed monad helpers for parser failure composition and pure-core absence handling.
- Added Phase 7 lazy execution entrypoint with `use <path>, lazy`, optional
  `engine=duckdb|polars` selection, DuckDB `read_parquet` scan views for lazy loading, typed
  execution-mode metadata, and CLI output that identifies lazy sessions.

---

## [0.6.0]

Phase 6 artifact-based visualization (`histogram`, `scatter`, `bar`; Altair-backed SVG/PNG).

### Added

- Added Phase 6 artifact-based visualization with `histogram`, `scatter`, and `bar` commands,
  Altair-backed SVG/PNG output, default `artifacts/plots/` paths, `saving(...)`, `noopen`, `bins=`,
  and `missing` options, plus interactive-only plot auto-open behavior.

---

## [0.5.0]

Phase 5 prompt-toolkit interactive shell UX (syntax highlighting, history, autocomplete).

### Added

- Added Phase 5 prompt-toolkit interactive shell UX with syntax highlighting, persistent command
  history, inline history suggestions, and context-aware autocomplete for commands, active dataset
  columns, common options, `by:` forms, and lightweight SQL helpers.

---

## [0.4.0]

Phase 4 SQL integration (`sql`, multiline queries, `into <table>`).

### Added

- Added Phase 4 SQL integration with `sql` queries over the active dataset exposed as `active`,
  multiline `sql """..."""` parsing, and `into <table>` active-dataset replacement.

---

## [0.3.0]

Phase 3 full EDA command surface (transformations, grouping, tabulate, codebook, count, head, tail).

### Added

- Completed the roadmap Phase 3 core EDA surface with executable transformations (`keep`, `drop`,
  `select`, `rename`, `generate`, `replace`), grouping (`by:` and `collapse`), and `tabulate`.
- Added session-local active DuckDB table state so transformations feed subsequent inspection and
  summary commands.
- Added the Phase 3 inspection slice with executable `codebook`, `count`, `head`, and `tail`
  commands over the active Parquet dataset.

---

## [0.2.0]

Phase 2 structured parser foundation (options, `if` clauses, expression ASTs, diagnostics).

### Added

- Added the Phase 2 parser foundation with structured command options, `if` clauses, expression
  ASTs, parsed-only future command forms, and focused diagnostics tests.

### Fixed

- Fixed Phase 2 parser regressions so `summarize` rejects assignment syntax and punctuated varlist
  names remain supported.

---

## [0.1.0]

Phase 0 project bootstrap and Phase 1 CLI skeleton (`use`, `describe`, `summarize`).

### Added

- Added Phase 1 `tabdat` CLI skeleton with `use`, `describe`, and `summarize`.
- Added DuckDB-backed local Parquet loading and numeric summary execution.
- Added focused parser, executor/backend, and CLI smoke tests.
- Added Phase 0 product guardrails for positioning, naming, MVP assumptions, non-goals, and
  contributor expectations.
- Added the v0 command glossary with the initial 12-command surface.
- Added SDD state files with feature status and planned architecture.
- Added repository guidance for 2-space tab size and proactive linting/formatting.
