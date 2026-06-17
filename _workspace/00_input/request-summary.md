# Request Summary: Classical Hypothesis Testing (`test`, `lincom`, `ttest`)

## Goal

Add post-estimation hypothesis testing and classical sample t-tests to TabDat-Explore:
- `test` for Wald and F constraint testing over regression coefficients.
- `lincom` for estimating and computing inference properties on linear combinations of coefficients.
- `ttest` for standard one-sample, paired-sample, and two-sample (Welch/equal variance) t-tests.

## Phase Fit

- Phase 21: Classical Statistical & Hypothesis Testing.
- Interacts with active estimation results (`regress`, `ivregress`).

## Touched Surfaces

- `src/tabdat/models.py`: Register commands and their respective results.
- `src/tabdat/parser.py`: Parse constraint syntax, linear combination expressions, and t-test group/variance options.
- `src/tabdat/executor.py`: Compute Wald/F test statistics, calculate linear combination properties (std err, confidence intervals), and run t-tests using SciPy.
- `src/tabdat/formatter.py`: Create Stata-style text tables for results.
- `tests/test_statistical_testing.py` and `tests/test_parser.py`: Verify parsing correctness and execution accuracy.

## Assumptions

- Multiple constraints are grouped in parentheses: `test (x1 = x2) (x3 = 0)`.
- `lincom` expressions are linear combinations of predictors.
- `ttest` options include `by(group_var)` and `welch`/`unequal`.

## Non-Goals

- Non-linear constraint post-estimation testing (`testnl`, `nlcom`) is out of scope.
- ANOVA and non-parametric tests are out of scope.
