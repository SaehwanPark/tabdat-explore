# Command Reference Index

TabDat-Explore includes 69 commands and topics organized into functional categories. Click any command name to view its syntax, options, and examples.

---

## Load & Inspect
| Command | Purpose |
|---|---|
| [`use`](../commands/use.md) | Load a dataset from Parquet, Stata `.dta`, CSV, Arrow, or activate a named table. |
| [`describe`](../commands/describe.md) | Show dataset shape, variable names, and DuckDB/Arrow data types. |
| [`summarize`](../commands/summarize.md) | Descriptive statistics (count, mean, std dev, min, max) for numeric variables. |
| [`codebook`](../commands/codebook.md) | Detailed variable profiling with missingness and unique sample values. |
| [`count`](../commands/count.md) | Count rows in the active dataset. |
| [`head`](../commands/head.md) | Preview the first rows of the active dataset. |
| [`tail`](../commands/tail.md) | Preview the last rows of the active dataset. |
| [`status`](../commands/status.md) | Show execution backend state, materialization status, and active relation details. |
| [`doctor`](../commands/doctor.md) | Inspect environment, core engines, and capability health. |

---

## Transform & Subset
| Command | Purpose |
|---|---|
| [`keep`](../commands/keep.md) | Keep specific variables or rows matching a boolean condition. |
| [`drop`](../commands/drop.md) | Drop specific variables or rows matching a boolean condition. |
| [`select`](../commands/select.md) | Select a subset of columns into the active dataset. |
| [`generate`](../commands/generate.md) | Create a new variable from an arithmetic or logical expression. |
| [`replace`](../commands/replace.md) | Replace values in an existing variable conditionally or unconditionally. |
| [`rename`](../commands/rename.md) | Rename variables in the active dataset. |
| [`recode`](../commands/recode.md) | Recode values or ranges into new categories. |

---

## Combine & Reshape
| Command | Purpose |
|---|---|
| [`join`](../commands/join.md) | Join the active dataset with a named table or file on key variables. |
| [`append`](../commands/append.md) | Vertically stack rows from a named table to the active dataset. |
| [`reshape`](../commands/reshape.md) | Reshape data between wide and long layouts. |

---

## Summarize & Tabulate
| Command | Purpose |
|---|---|
| [`tabulate`](../commands/tabulate.md) | One-way and two-way frequency tables and crosstabs. |
| [`collapse`](../commands/collapse.md) | Grouped aggregations (mean, sum, min, max, count) into a new dataset. |
| [`by`](../commands/by.md) | Execute a command independently within groups of variables. |

---

## Linear & Quantile Models
| Command | Purpose |
|---|---|
| [`regress`](../commands/regress.md) | Linear regression (OLS, WLS, GLS) with robust and clustered covariance. |
| [`qreg`](../commands/qreg.md) | Quantile regression for median and conditional quantiles. |

---

## Binary & Limited Dependent Variables
| Command | Purpose |
|---|---|
| [`logit`](../commands/logit.md) | Logistic regression via maximum likelihood. |
| [`probit`](../commands/probit.md) | Probit regression via maximum likelihood. |
| [`tobit`](../commands/tobit.md) | Tobit censored regression with lower and upper bounds. |
| [`heckman`](../commands/heckman.md) | Heckman two-step sample selection estimator. |
| [`nl`](../commands/nl.md) | Nonlinear least squares regression. |

---

## Count & Survival Models
| Command | Purpose |
|---|---|
| [`poisson`](../commands/poisson.md) | Poisson log-linear count regression. |
| [`nbreg`](../commands/nbreg.md) | Negative binomial count regression. |
| [`zip`](../commands/zip.md) | Zero-inflated Poisson count regression. |
| [`zinb`](../commands/zinb.md) | Zero-inflated negative binomial regression. |
| [`streg`](../commands/streg.md) | Parametric survival regression (Weibull, Exponential, Cox). |

---

## Panel, IV & Causal Inference
| Command | Purpose |
|---|---|
| [`panel`](../commands/panel.md) | Set, display, or clear panel identifier and time metadata. |
| [`ivregress`](../commands/ivregress.md) | Instrumental variables regression (2SLS and GMM). |
| [`cfregress`](../commands/cfregress.md) | Control function regression for endogeneity. |
| [`xtreg`](../commands/xtreg.md) | Panel data fixed-effects (FE) and random-effects (RE) models. |
| [`xtdata`](../commands/xtdata.md) | Panel within and between transformations. |
| [`xtlogit`](../commands/xtlogit.md) | Fixed-effects conditional logit regression. |
| [`xtabond`](../commands/xtabond.md) | Arellano-Bond dynamic panel GMM estimator. |
| [`did`](../commands/did.md) | Difference-in-differences estimator with panel metadata. |
| [`drdid`](../commands/drdid.md) | Doubly robust difference-in-differences estimator. |

---

## Machine Learning & Regularization
| Command | Purpose |
|---|---|
| [`lasso`](../commands/lasso.md) | L1-regularized Lasso linear regression. |
| [`postlasso`](../commands/postlasso.md) | Post-selection OLS estimation after Lasso. |
| [`ridge`](../commands/ridge.md) | L2-regularized Ridge linear regression. |
| [`elasticnet`](../commands/elasticnet.md) | Elastic net regression with combined L1/L2 penalties. |
| [`cvlasso`](../commands/cvlasso.md) | Cross-validated Lasso with optimal penalty selection. |
| [`cvridge`](../commands/cvridge.md) | Cross-validated Ridge regression. |
| [`cvelasticnet`](../commands/cvelasticnet.md) | Cross-validated Elastic net regression. |
| [`dml`](../commands/dml.md) | Double / debiased machine learning average treatment effect (ATE). |

---

## Bayesian & Spatial
| Command | Purpose |
|---|---|
| [`bayes`](../commands/bayes.md) | Bayesian linear regression via Ridge estimation. |
| [`bayes_prefix`](../commands/bayes_prefix.md) | MCMC sampling prefix for linear and logistic regression models. |
| [`bayesplot`](../commands/bayesplot.md) | MCMC chain diagnostic plots (trace, density, autocorrelation). |
| [`spregress`](../commands/spregress.md) | Spatial lag (SAR) and spatial error (SEM) regression models. |

---

## Post-Estimation & Hypothesis Tests
| Command | Purpose |
|---|---|
| [`predict`](../commands/predict.md) | Compute fitted values (`xb`), residuals, probabilities (`pr`), or draws. |
| [`estat`](../commands/estat.md) | Post-estimation diagnostics (VIF, AIC/BIC, Hausman test, etc.). |
| [`estat_report`](../commands/estat_report.md) | Generate self-contained HTML regression diagnostic report. |
| [`test`](../commands/regress.md) | Linear hypothesis Wald test after regression. |
| [`lincom`](../commands/regress.md) | Estimate linear combinations of model parameters. |
| [`ttest`](../commands/summarize.md) | Student t-tests for one sample, two samples, or paired observations. |

---

## Visualization
| Command | Purpose |
|---|---|
| [`histogram`](../commands/histogram.md) | Save frequency or density histogram plots. |
| [`scatter`](../commands/scatter.md) | Save bivariate scatter plots with optional fit lines. |
| [`bar`](../commands/bar.md) | Save categorical bar charts. |

---

## Scripts, SQL & System
| Command | Purpose |
|---|---|
| [`sql`](../commands/sql.md) | Run DuckDB SQL queries against the active dataset. |
| [`run`](../commands/run.md) | Execute a `.td` script file. |
| [`save`](../commands/save.md) | Save the active dataset to Parquet. |
| [`export`](../commands/export.md) | Export the active dataset to Parquet. |
| [`set`](../commands/set.md) | Configure session runtime settings (`graph_format`, `artifact_dir`, `graph_open`). |
| [`lowess`](../commands/lowess.md) | Locally weighted scatterplot smoothing (LOWESS). |
| [`help`](../commands/describe.md) | Display in-app help for commands and topics. |
| [`exit`](../commands/exit.md) / [`quit`](../commands/quit.md) | Exit the interactive shell. |
