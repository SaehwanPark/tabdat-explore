# Command Reference

This is the living command index for TabDat-Explore. For authoritative syntax and options, run
`help <command>` in the interactive shell or batch mode.

The historical Phase 0 glossary lives in [command_glossary_v0.md](command_glossary_v0.md). That
document records early scope decisions; this reference reflects the current CLI.

## Load and inspect

| Command | Purpose | Minimal invocation |
|---------|---------|-------------------|
| `use` | Load a dataset or activate a named table | `use data.parquet` |
| `describe` | Show dataset structure, types, and shape | `describe` |
| `summarize` | Compute descriptive statistics | `summarize age bmi` |
| `codebook` | Profile columns with missingness and sample values | `codebook age sex` |
| `count` | Count rows in the active dataset | `count` |
| `head` | Preview the first rows | `head` |
| `tail` | Preview the last rows | `tail` |

Run `help use`, `help describe`, and so on for format options (lazy loading, CSV delimiters, remote
paths, and more).

## Transform and subset

| Command | Purpose | Minimal invocation |
|---------|---------|-------------------|
| `keep` | Keep variables or rows matching a condition | `keep age bmi` |
| `drop` | Drop variables or rows matching a condition | `drop cost` |
| `select` | Select a subset of columns | `select age sex` |
| `generate` | Create a new variable from an expression | `generate bmi_sq = bmi^2` |
| `replace` | Replace values in an existing variable | `replace age = . if age < 0` |
| `rename` | Rename a variable | `rename cost charges` |
| `recode` | Recode values or ranges into new categories | `recode age (18/64=1) (65/max=2), generate(age_grp)` |

## Combine and reshape

| Command | Purpose | Minimal invocation |
|---------|---------|-------------------|
| `join` | Join the active dataset with another table | `join lookup on id` |
| `append` | Append rows from a named table | `append followup` |
| `reshape` | Reshape data between wide and long layouts | `reshape long value, i(id) j(year)` |

## Summarize and tabulate

| Command | Purpose | Minimal invocation |
|---------|---------|-------------------|
| `tabulate` | Frequency tables and crosstabs | `tabulate sex` |
| `collapse` | Grouped aggregation into a new dataset | `collapse (mean) bmi, by(sex)` |
| `by` | Run a command within groups | `by sex: summarize bmi` |

## Linear and quantile models

| Command | Purpose | Minimal invocation |
|---------|---------|-------------------|
| `regress` | Linear regression (OLS, WLS, GLS) | `regress cost age bmi` |
| `qreg` | Quantile regression | `qreg cost age bmi, quantile(0.5)` |

## Binary and limited-dependent models

| Command | Purpose | Minimal invocation |
|---------|---------|-------------------|
| `logit` | Logistic regression | `logit admit gpa` |
| `probit` | Probit regression | `probit admit gpa` |
| `tobit` | Tobit regression with censoring bounds | `tobit hours wage, ll(0)` |
| `heckman` | Sample-selection model | `heckman wage educ, selectdep(inwork) select(educ age)` |
| `nl` | Nonlinear least squares | `nl y = b0 + b1*exp(-b2*x), params(b0 b1 b2) start(0 1 1)` |

## Count and survival models

| Command | Purpose | Minimal invocation |
|---------|---------|-------------------|
| `poisson` | Poisson count regression | `poisson visits age` |
| `nbreg` | Negative-binomial count regression | `nbreg visits age` |
| `zip` | Zero-inflated Poisson | `zip visits age, inflate(age)` |
| `zinb` | Zero-inflated negative binomial | `zinb visits age, inflate(age)` |
| `streg` | Parametric survival regression | `streg time age, failure(died) dist(weibull)` |

## IV, panel, and causal inference

| Command | Purpose | Minimal invocation |
|---------|---------|-------------------|
| `panel` | Set or clear panel id/time metadata | `panel id year` |
| `ivregress` | Instrumental-variables regression | `ivregress 2sls y x, endog(x) iv(z)` |
| `cfregress` | Control-function regression | `cfregress y x, endog(x) iv(z)` |
| `xtreg` | Panel fixed- or random-effects regression | `xtreg y x, fe` |
| `xtdata` | Within/between panel transforms | `xtdata wage, within` |
| `xtlogit` | Panel fixed-effects logit | `xtlogit y x, fe` |
| `xtabond` | Dynamic panel GMM | `xtabond y x, lags(1)` |
| `did` | Difference-in-differences (panel metadata) | `did y, treat(treated) post(post)` |
| `drdid` | Doubly robust difference-in-differences | `drdid y, treat(treated) post(post)` |

## Machine learning and regularization

| Command | Purpose | Minimal invocation |
|---------|---------|-------------------|
| `lasso` | Lasso linear regression | `lasso linear y x1 x2 x3` |
| `postlasso` | Post-selection OLS inference after Lasso | `postlasso linear y x1 x2 x3` |
| `ridge` | Ridge linear regression | `ridge linear y x1 x2 x3` |
| `elasticnet` | Elastic-net linear regression | `elasticnet linear y x1 x2 x3` |
| `cvlasso` | Cross-validated Lasso | `cvlasso linear y x1 x2 x3` |
| `cvridge` | Cross-validated ridge | `cvridge linear y x1 x2 x3` |
| `cvelasticnet` | Cross-validated elastic net | `cvelasticnet linear y x1 x2 x3` |
| `dml` | Double/debiased machine learning ATE | `dml linear y controls, treat(t)` |

## Bayesian and spatial

| Command | Purpose | Minimal invocation |
|---------|---------|-------------------|
| `bayes` | Bayesian linear regression | `bayes linear y x1 x2` |
| `bayes:` | Bayesian prefix for MCMC estimation | `bayes: regress y x1 x2` |
| `bayesplot` | MCMC diagnostic plots | `bayesplot trace` |
| `spregress` | Spatial regression | `spregress y x, coord(lat lon)` |

## Post-estimation and hypothesis testing

| Command | Purpose | Minimal invocation |
|---------|---------|-------------------|
| `predict` | Generate fitted values, residuals, or probabilities | `predict yhat, xb` |
| `estat` | Post-estimation diagnostics | `estat vif` |
| `estat report` | HTML regression report with diagnostic plots | `estat report` |
| `test` | Linear hypothesis tests after regression | `test x1 = 0` |
| `lincom` | Linear combinations of coefficients | `lincom x1 + x2` |
| `ttest` | One-, two-, or paired-sample t-tests | `ttest age, by(sex)` |

## Visualization

| Command | Purpose | Minimal invocation |
|---------|---------|-------------------|
| `histogram` | Histogram plot artifact | `histogram age` |
| `scatter` | Scatter plot artifact | `scatter bmi age` |
| `bar` | Bar chart artifact | `bar sex` |

## Scripts, SQL, and persistence

| Command | Purpose | Minimal invocation |
|---------|---------|-------------------|
| `sql` | Run SQL against the active dataset (`active`) | `sql select * from active limit 5` |
| `run` | Execute a TabDat script file | `run analysis.td` |
| `save` | Save the active dataset to Parquet | `save output.parquet` |
| `export` | Export the active dataset to Parquet | `export output.parquet` |

Script-only directives (not interactive commands): `seed <integer>` and `let <name> = <value>` for
reproducible `.td` scripts. See the [user guide](user-guide.md).

## Session and utilities

| Command | Purpose | Minimal invocation |
|---------|---------|-------------------|
| `set` | Change runtime settings for the session | `set graph_format png` |
| `status` | Show read-only execution state, last operation, and materialization taxonomy | `status` |
| `lowess` | Nonparametric smoothing into a new variable | `lowess y x, gen(y_smooth)` |
| `help` | Show in-app help for a command | `help regress` |
| `exit` / `quit` | Leave the interactive shell | `exit` |

## Getting help

In the interactive shell or with batch `-c`:

```bash
uv run tabdat -c "help use"
uv run tabdat -c "help regress"
```

Run `help` with no arguments in the interactive shell to browse available topics.

For workflows, configuration, and behavioral notes, see the [user guide](user-guide.md).
