# Estimation Workflows

TabDat provides a comprehensive suite of econometric, statistical, machine learning, and Bayesian estimation commands.

---

## 1. Linear & Quantile Regression

### Classical, Robust & Clustered OLS
```text
tabdat> regress wage educ exper
tabdat> regress wage educ exper, robust
tabdat> regress wage educ exper, cluster(industry)
```

### Quantile Regression
Estimate median or arbitrary conditional quantiles:
```text
tabdat> qreg wage educ exper, quantile(0.5)
tabdat> qreg wage educ exper, quantile(0.9)
```

---

## 2. Binary & Limited Dependent Variables

### Logit & Probit MLE
```text
tabdat> logit employed educ age married, robust
tabdat> probit employed educ age married
```

### Censored Regression (Tobit)
```text
tabdat> tobit hours_worked wage educ, ll(0)
```

### Sample Selection (Heckman)
Two-step Heckman selection estimator:
```text
tabdat> heckman wage educ, selectdep(inwork) select(educ age kids)
```

---

## 3. Count & Survival Data

- **Poisson MLE**: `poisson visits age insurance`
- **Negative Binomial**: `nbreg visits age insurance`
- **Zero-Inflated Poisson**: `zip visits age insurance, inflate(age)`
- **Zero-Inflated Negative Binomial**: `zinb visits age insurance, inflate(age)`
- **Parametric Survival**: `streg duration age, failure(event) dist(weibull)`

---

## 4. Panel Data & Instrumental Variables

### Panel Regression (`xtreg`)
Requires `panel id_var time_var` first:
```text
tabdat> panel firm year
tabdat> xtreg investment capital profit, fe
tabdat> xtreg investment capital profit, re
```

### Dynamic Panel GMM (`xtabond`)
Arellano-Bond linear dynamic panel estimator:
```text
tabdat> xtabond investment capital profit, lags(1)
```

### Instrumental Variables (`ivregress`)
Two-stage least squares (2SLS) and GMM:
```text
tabdat> ivregress 2sls wage exper, endog(educ) iv(near_college parents_educ)
```

---

## 5. Causal Inference

### Difference-in-Differences (`did`)
```text
tabdat> did outcome, treat(treated) post(post_period)
```

### Doubly Robust Difference-in-Differences (`drdid`)
```text
tabdat> drdid outcome covariates, treat(treated) post(post_period)
```

---

## 6. Regularization & Machine Learning

- **Lasso**: `lasso linear y x1 x2 x3`
- **Post-Lasso OLS**: `postlasso linear y x1 x2 x3`
- **Ridge Regression**: `ridge linear y x1 x2 x3`
- **Elastic Net**: `elasticnet linear y x1 x2 x3, l1_ratio(0.5)`
- **Cross-Validated Models**: `cvlasso linear y x1 x2 x3`, `cvridge ...`, `cvelasticnet ...`
- **Double/Debiased Machine Learning (DML)**: `dml linear y controls, treat(t)`

---

## 7. Bayesian Estimation

### Bayesian Ridge Linear Regression
```text
tabdat> bayes linear wage educ exper
```

### Full MCMC Sampling (`bayes:` Prefix)
MCMC estimation via Bambi/PyMC backends with custom priors:
```text
tabdat> bayes, draws(2000) burnin(1000) chains(4): regress wage educ exper
```

- **MCMC Diagnostics**: `estat bayes`
- **MCMC Trace Plots**: `bayesplot trace`, `bayesplot density`, `bayesplot autocorrelation`
- **Posterior Predictive Predictions**: `predict wage_pp, posterior_predictive std interval`

---

## 8. Spatial Econometrics (`spregress`)

Fit spatial lag (SAR) and spatial error (SEM) models:
```text
tabdat> spregress crime income, coord(lat lon) model(lag)
```

---

## 9. Post-Estimation Diagnostics

- `predict <varname>, xb`: Compute linear predictions.
- `predict <varname>, residuals`: Compute residuals.
- `predict <varname>, pr`: Predicted probabilities (after Logit/Probit).
- `estat vif`: Multicollinearity variance inflation factors.
- `estat report`: Generate self-contained HTML regression summary report.
- `test x1 = x2`: Linear hypothesis Wald tests.
- `lincom x1 + 2*x2`: Estimate linear combinations of parameters.
