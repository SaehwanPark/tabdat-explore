# Quickstart Tutorial

This hands-on tutorial walks through loading a dataset, inspecting variables, cleaning data, fitting models, and generating plots.

---

## 1. Load Data

Open a Parquet dataset eagerly:

```text
tabdat> use https://github.com/SaehwanPark/tabdat-explore/raw/main/demos/data/sample.parquet
Loaded: sample.parquet (1000 rows, 6 columns)
```

Or load a local file lazily (deferred scan):

```text
tabdat> use data.parquet, lazy
Active dataset: data.parquet (lazy scan)
```

---

## 2. Inspect Structure and Summary Statistics

Check dataset metadata and schema:

```text
tabdat> describe
Dataset: sample.parquet
Rows: 1000
Columns: 6

Variable  Type     Nulls
id        INTEGER  0
age       INTEGER  12
income    DOUBLE   5
educ      INTEGER  0
married   BOOLEAN  0
score     DOUBLE   18
```

Inspect summary statistics for specific columns:

```text
tabdat> summarize age income score
Variable  Count  Mean     Std Dev  Min   Max
age       988    42.1     11.8     18    79
income    995    58420.0  15400.0  8500  182000
score     982    74.3     14.2     32.0  99.5
```

Profile missingness and sample values with `codebook`:

```text
tabdat> codebook age married
```

---

## 3. Transform and Subset Data

Filter rows:

```text
tabdat> keep if age >= 21
Kept 970 rows (dropped 30)
```

Create derived variables:

```text
tabdat> generate log_income = log(income)
Generated: log_income (DOUBLE)
```

Recode values into categorical groups:

```text
tabdat> recode age (18/35=1) (36/55=2) (56/max=3), generate(age_group)
Generated: age_group (INTEGER)
```

---

## 4. Grouped Summaries and Aggregations

Tabulate frequency distributions:

```text
tabdat> tabulate age_group
age_group  Freq.  Percent  Cum.
1          320    32.99%   32.99%
2          480    49.48%   82.47%
3          170    17.53%   100.00%
Total      970    100.00%
```

Run summaries within groups with `by`:

```text
tabdat> by age_group: summarize income
```

Collapse data into a summary table:

```text
tabdat> collapse (mean) income score (count) n=id, by(age_group)
Collapsed to 3 rows, 4 columns
```

---

## 5. Statistical Estimation

Fit an OLS regression with robust standard errors:

```text
tabdat> regress income age educ, robust
```

Run post-estimation variance inflation factor (VIF) diagnostics:

```text
tabdat> estat vif
Variable  VIF
age       1.12
educ      1.12
Mean VIF  1.12
```

Generate fitted predictions into the active dataset:

```text
tabdat> predict income_hat, xb
Generated: income_hat
```

Generate an interactive HTML diagnostic report:

```text
tabdat> estat report
Report saved: artifacts/reports/regression_report.html
```

---

## 6. Visualization

Plot a histogram of `income`:

```text
tabdat> histogram income
Plot saved: artifacts/plots/histogram-income.png
file:///Users/username/project/artifacts/plots/histogram-income.png
```

Plot a scatter plot with regression line:

```text
tabdat> scatter income age
Plot saved: artifacts/plots/scatter-income-age.png
```

---

## 7. Exporting Results

Save the transformed dataset:

```text
tabdat> save cleaned_data.parquet
Saved: cleaned_data.parquet (970 rows, 8 columns)
```
