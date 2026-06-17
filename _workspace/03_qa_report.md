# Classical Statistical & Hypothesis Testing (`test`, `lincom`, `ttest`) QA Report

## Status

pass

## Boundaries Checked

- **Contract to parser**: Validated that constraints syntax, parentheses grouping, linear combination formulas, and t-test option permutations parse correctly. Checked that unsupported combinations raise `ParseError`.
- **Parser representation to executor**: Verified that `TestCommand`, `LincomCommand`, and `TtestCommand` representations carry all necessary fields into execution logic.
- **Executor to backend**: Verified that parameter values, standard errors, and covariance matrices are correctly extracted from estimation results. Checked that sample observations are correctly subsetted.
- **Backend result to formatter & CLI**: Verified that results are mapped to clean Stata-style text formatters and print properly.

## Blocking Issues

- None.

## PR Review Loop

- PR: (Local repository branch `feat/hypothesis-testing-alignment`)
- Pass 1 verified parser syntax handling for equations and constraints.
- Pass 2 verified Wald matrix arithmetic and degrees of freedom handling.
- Pass 3 verified equal vs unequal variance SciPy t-test calculations.

## Validation Evidence

- Target parser tests passed: `uv run pytest tests/test_parser.py -k statistical_testing`
- Target executor tests passed: `uv run pytest tests/test_statistical_testing.py`
- Full suite validation passed: `uv run pytest` (922 passed)
- Static validation passed: `uv run basedpyright` (0 errors)
- Lint validation passed: `uv run ruff check`
