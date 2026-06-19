# QA Report: Phase 19 — Richer Bayesian Prediction Workflows

## Status

pass

## Boundaries Checked

- **Contract to Parser**: Verified that syntax options (`std` and `saving(<path>)`) for `predict` are correctly parsed and validated. Mutual exclusivity constraints between saving and active dataset options (`std`, `interval`, `level`) are verified to raise `ParseError` on syntax load.
- **Parser to Executor**: Verified mapping of PredictCommand properties (`std` and `saving`) to the execution engine. Proactive collision checks for `<newvar>_std`, `<newvar>_lower`, and `<newvar>_upper` columns occur *before* MCMC sampling begins, raising early `ExecutionError` in case of collision.
- **Executor to Backend**: Verified DuckDB active table operations. Predictions are added as double precision floats. When `saving` is requested, the active dataset is not mutated, and the backend exports raw draws directly to the destination Parquet file.
- **Out-of-Sample Predictions**: Verified that predictions and draws saving function correctly on datasets where the outcome variable is missing (only predictors are present).
- **Empty Datasets / Missing Predictors**: Verified that empty dataset prediction writes an empty Parquet file with explicit schema column types (`observation_index`, `chain`, `draw`, `value`) to avoid PyArrow serialization issues. Partially missing predictors correctly propagate `None` predictions to the dataset and skip MCMC draws inside the saved file.
- **Type Safety**: Passed `basedpyright` with 0 errors, warnings, or notes.
- **Code Style**: Checked and formatted via `ruff check` and `ruff format`. All checks passed.

## Blocking Issues

- None.

## PR Review Loop

- Branch: `feat/bayes-oos-predict`
- Pass 1 verified the code correctness and identified a redundant pandas import in the backend/executor module. The redundant import was removed.
- Pass 2 verified type safety and suggested early checks to make sure the target columns are checked before launching time-consuming sampling. Early collision checking was successfully added.
- Pass 3 verified memory consumption and recommended replacing the heavy `to_dataframe().reset_index()` multi-index call with a high-performance vectorized NumPy construction. Tiling and repeating arrays via NumPy was implemented and fully verified.

## Validation Evidence

- **Type safety check**: `uv run basedpyright` (passed, 0 errors)
- **Formatting and Lint**: `uv run ruff format --check && uv run ruff check` (passed, all checks passed)
- **Target unit tests**: `uv run pytest tests/test_parser.py -k "predict" && uv run pytest tests/test_executor.py -k "bayes"` (passed)
- **Full test suite**: `uv run pytest` (940 passed, 311 warnings)
