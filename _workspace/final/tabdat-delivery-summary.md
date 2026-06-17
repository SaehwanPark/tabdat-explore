# Delivery Summary: Classical Hypothesis Testing (`test`, `lincom`, `ttest`)

## Result

Implemented on `main` (branch `feat/hypothesis-testing-alignment` created for workspace synchronization).

## Delivered

- Added `test` command for Wald/F post-estimation joint restrictions testing.
- Added `lincom` command for linear combinations of coefficients and confidence intervals.
- Added `ttest` command for one-sample, paired-sample, and group-grouped (Welch/equal variance) t-tests.
- Added tokenizer and constraint equation parser supporting parenthesis constraints: `test (x1 = x2) (x3 = 0)`.
- Integrated SciPy distributions for robust hypothesis testing (degrees of freedom, stats, and p-values).
- Formatted tables to Stata style and checked them against 100-character line-length restrictions.
- Added unit tests in `tests/test_parser.py` and integration tests in `tests/test_statistical_testing.py`.

## Validation

- `uv run pytest tests/test_statistical_testing.py` (8 passed)
- `uv run basedpyright` (0 errors)
- `uv run ruff check` (passed)
- `uv run pytest` (922 passed)

## Review

- QA status: `pass` (recorded in `_workspace/03_qa_report.md`).
- Verified parser-to-executor and executor-to-backend boundaries.

## Deferred

- Non-linear constraint post-estimation testing (`testnl`, `nlcom`).
