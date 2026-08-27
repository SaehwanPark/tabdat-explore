# Product Contract: Statistical Reference Validation Matrix & Tier 1 Assurance

## Request Summary
Track, publish, and differentially verify statistical estimator accuracy against trusted numerical reference implementations with explicit tolerances.

## Roadmap Phase
Phase 24C (Statistical Trust and Reference Validation).

## Specification & Validation Rules

### 1. Tracked Reference Validation Matrix Schema
Each estimator entry in `docs/reference_validation_matrix.json` records:
- `command`: Command name (e.g. `regress`, `logit`, `probit`, `poisson`, `qreg`).
- `estimator_mode`: Specific inference/estimation mode (e.g., `ols_classical`, `ols_hc1_robust`, `ols_cluster`, `logit_mle`, `probit_mle`, `poisson_mle`, `quantile_median`).
- `backend`: Execution backend (`duckdb` data relation + stats engine).
- `reference_implementation`: External reference package (e.g. `statsmodels.regression.linear_model.OLS`, `statsmodels.discrete.discrete_model.Logit`).
- `tolerances`:
  - `coef_rtol`: Maximum relative tolerance on point estimates ($10^{-5}$).
  - `se_rtol`: Maximum relative tolerance on standard errors ($10^{-4}$).
  - `pvalue_rtol`: Maximum relative tolerance on p-values ($10^{-4}$).
  - `log_likelihood_rtol`: Maximum relative tolerance on log-likelihood ($10^{-5}$).
- `validation_status`: `"reference_validated"` for fully verified Tier 1 estimators; `"implemented"` for remaining estimators.

### 2. Tier 1 Differential Testing
- `tests/test_reference_validation.py` synthesizes deterministic fixtures with noise, controls, and cluster groups.
- Directly invokes TabDat commands (`regress`, `logit`, `probit`, `poisson`, `qreg`) through the Executor pipeline and compares structured Result coefficients, standard errors, test statistics, and predictions against direct `statsmodels` fits over identical data.
- Asserts deterministic numerical convergence within the specified tolerances.

## Acceptance Criteria
- [ ] `docs/reference_validation_matrix.json` exists, is valid JSON, and catalogs all TabDat estimators.
- [ ] `docs/reference-validation-matrix.md` is rendered, linked, and documented in the doc tree.
- [ ] `tests/test_reference_validation.py` contains thorough differential tests for Tier 1 estimators (`regress` standard/robust/cluster, `logit`, `probit`, `poisson`, `qreg`).
- [ ] All tests pass without flakiness.
- [ ] `scripts/check_docs_alignment.py` and `pytest` pass.
