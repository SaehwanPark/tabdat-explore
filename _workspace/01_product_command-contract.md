# Command Contract: Classical Hypothesis Testing (`test`, `lincom`, `ttest`)

## Request Summary

Add hypothesis testing and statistical t-tests over active datasets and regression states.

## Command Syntax

```text
test (constraint1) [(constraint2) ...]
lincom expression [, level(num)]
ttest varname == exp [if exp]
ttest var1 == var2 [if exp]
ttest varname [if exp], by(groupvar) [welch|unequal]
```

## Examples

- `test (educ = 0) (exper = 0)`
- `lincom educ + 2*exper`
- `ttest wage == 15`
- `ttest wage, by(sex) unequal`

## Data Assumptions

- `test` and `lincom` require an active regression state (`self.state.regression` is not None).
- `ttest` operates on the active dataset variables.
- Excludes observations with missing values during estimation/testing.

## Execution Semantics

- `test` computes F-statistics (or Wald chi-squared if robust/clustered is used) under restriction $R \beta = r$.
- `lincom` estimates linear combinations using delta method/covariance propagation.
- `ttest` uses SciPy's standard distributions (`scipy.stats.t` / `scipy.stats.ttest_ind` / `scipy.stats.ttest_rel`).

## Acceptance Criteria

- `test` outputs restriction constraints, F-statistic, degrees of freedom, and p-value.
- `lincom` displays coefficient estimate, standard error, t-statistic, p-value, and confidence interval.
- `ttest` displays summary statistics per group/variable, mean difference, standard error of difference, and p-values for left-tailed, two-sided, and right-tailed hypotheses.
