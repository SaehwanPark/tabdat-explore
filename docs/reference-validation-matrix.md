# Statistical Reference Validation Matrix

This document tracks the validation status of TabDat's statistical and econometric commands against authoritative reference implementations (such as `statsmodels`, `scipy`, `linearmodels`, `rpy2`, and published benchmark packages).

Machine-readable specification: [`docs/reference_validation_matrix.json`](reference_validation_matrix.json).

---

## Validation Status Taxonomy

- **Reference Validated (✓)**: Systematically verified against independent reference implementations across coefficients, standard errors, test statistics, degrees of freedom, and log-likelihood with explicit numerical tolerances ($10^{-5}$ to $10^{-6}$).
- **Implemented (○)**: Feature complete with end-to-end integration and unit test coverage, queued for reference benchmark differential suites.

---

## Tier 1 — Foundational Linear & Discrete Models

| Command | Mode / Target | Reference Implementation | Coef Tol (`rtol`) | SE Tol (`rtol`) | Status | Notes |
|---------|---------------|--------------------------|-------------------|-----------------|--------|-------|
| `regress` | Classical OLS | `statsmodels.OLS` (standard) | $10^{-6}$ | $10^{-5}$ | **Reference Validated** | Point estimates, SEs, t-stats, p-values, $R^2$, F-stat |
| `regress` | Robust HC1 | `statsmodels.OLS` (`cov_type='HC1'`) | $10^{-6}$ | $10^{-5}$ | **Reference Validated** | Heteroskedasticity-consistent robust covariance |
| `regress` | Cluster Robust | `statsmodels.OLS` (`cov_type='cluster'`) | $10^{-6}$ | $10^{-5}$ | **Reference Validated** | Clustered standard errors with group adjustment |
| `predict` | Fitted values & residuals | `RegressionResults.predict/resid` | $10^{-6}$ | $10^{-5}$ | **Reference Validated** | Linear indices and residual derivations |
| `estat` | VIF & Model IC | `statsmodels.stats.outliers_influence` | $10^{-5}$ | $10^{-5}$ | **Reference Validated** | Multicollinearity diagnostics & AIC/BIC |
| `logit` | Binary Logit MLE | `statsmodels.Logit` | $10^{-5}$ | $10^{-4}$ | **Reference Validated** | Maximum likelihood coefficients, SEs, pseudo-$R^2$ |
| `probit` | Binary Probit MLE | `statsmodels.Probit` | $10^{-5}$ | $10^{-4}$ | **Reference Validated** | Maximum likelihood coefficients, SEs, pseudo-$R^2$ |
| `poisson` | Poisson Log-Linear MLE | `statsmodels.Poisson` | $10^{-5}$ | $10^{-4}$ | **Reference Validated** | Log-linear count regression MLE parameters & deviance |
| `qreg` | Quantile Regression | `statsmodels.QuantReg` | $10^{-5}$ | $10^{-4}$ | **Reference Validated** | Median and arbitrary quantile ($q \in (0,1)$) regression |

---

## Tier 2 — Panel, Instrumental Variables & Causal

| Command | Mode / Target | Reference Implementation | Status |
|---------|---------------|--------------------------|--------|
| `ivregress` | 2SLS & GMM | `linearmodels.iv.IV2SLS / IVGMM` | Implemented |
| `xtreg` | Panel Fixed & Random Effects | `linearmodels.panel.PanelOLS / RandomEffects` | Implemented |
| `cfregress` | Control Function IV | 2-step residual projection OLS | Implemented |
| `did` | Difference-in-Differences | Two-way fixed effects DID | Implemented |
| `xtabond` | Dynamic Panel GMM | Arellano-Bond instrument moment conditions | Implemented |
| `xtlogit` | Panel Binary Logit | Conditional / random-effects logit | Implemented |

---

## Tier 3 — Advanced & Specialized Capabilities

| Command | Mode / Target | Reference Implementation | Status |
|---------|---------------|--------------------------|--------|
| `tobit` | Censored Regression | MLE with normal error log-likelihood | Implemented |
| `heckman` | Sample Selection | 2-step inverse Mills ratio estimator | Implemented |
| `zip` / `zinb` | Zero-Inflated Counts | `statsmodels.ZeroInflatedPoisson / ZeroInflatedNegativeBinomialP` | Implemented |
| `streg` | Parametric Survival | `statsmodels.PHReg` / Exponential / Weibull / Cox | Implemented |
| `dml` / `drdid` | Double Machine Learning & DR-DID | Cross-fitting orthogonalized AIPW score estimators | Implemented |
| `lasso` / `ridge` / `elasticnet` | Regularized Linear Models | `scikit-learn.linear_model` / `cvlasso`, `cvridge`, `cvelasticnet` | Implemented |
| `bayes` | MCMC Bayesian Estimation | `bambi` / `pymc` NUTS sampler & ArviZ posterior diagnostics | Implemented |
| `spregress` | Spatial Econometrics | `spreg` / `libpysal` Spatial Lag (SAR) & Spatial Error (SEM) | Implemented |

---

## Differential Test Suite

Differential testing is automated via `pytest tests/test_reference_validation.py`. The suite builds deterministic synthetic datasets with known DGP (data generating process), runs TabDat commands, and verifies point estimates, standard errors, log-likelihood, and predictions directly against `statsmodels` models.
