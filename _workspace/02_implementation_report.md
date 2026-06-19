# Implementation Report: Phase 19 — Richer Bayesian Prediction Workflows

## Contract Consumed

- `_workspace/01_product_command-contract.md` (Design for Phase 19: Richer Bayesian Prediction Workflows).

## Files Changed

- [src/tabdat/models.py](file:///Users/saehwan/gitrepos/tabdat-explore-dev/src/tabdat/models.py):
  - Updated `PredictCommand` to support fields `std: bool` and `saving: Path | None`.
- [src/tabdat/parser.py](file:///Users/saehwan/gitrepos/tabdat-explore-dev/src/tabdat/parser.py):
  - Updated `_parse_predict` syntax parser to parse `std` and `saving(<path>)` options for the `predict` command.
  - Enforced mutual exclusivity: raising `ParseError` if `saving()` is combined with active dataset options (`std`, `interval`, `level`), or if `std` and `saving()` are used without `posterior_predictive`.
- [src/tabdat/executor.py](file:///Users/saehwan/gitrepos/tabdat-explore-dev/src/tabdat/executor.py):
  - Updated `_execute_predict` to preemptively check for target/appended column name collisions (including `<newvar>_std` and `<newvar>_lower`/`<newvar>_upper` if applicable) before running Bayesian sampling.
  - Updated `_bayes_mcmc_posterior_predictive_summary` to compute standard deviations (`predictive_samples.std(dim="__sample").values`) and append the `<newvar>_std` column when `std` is specified.
  - Implemented high-performance, vectorized draws export to Parquet when `saving(...)` is specified using memory-efficient tiling/repeating via NumPy (`np.tile` and `np.repeat`) instead of expensive xarray MultiIndex `to_dataframe()` calls.
  - Ensured correct out-of-sample predictions when outcome variables are missing from the test dataset (DuckDB active table) by selecting only predictor variables for the design matrix inputs.
  - Removed redundant local `import pandas as pd` inside `_bayes_mcmc_posterior_predictive_summary`.
- [src/tabdat/shell.py](file:///Users/saehwan/gitrepos/tabdat-explore-dev/src/tabdat/shell.py):
  - Registered `std` and `saving(` completion options for the `predict` command.
- [tests/test_parser.py](file:///Users/saehwan/gitrepos/tabdat-explore-dev/tests/test_parser.py):
  - Added parser unit tests covering successful syntax parsing and mutual exclusivity errors.
- [tests/test_executor.py](file:///Users/saehwan/gitrepos/tabdat-explore-dev/tests/test_executor.py):
  - Added integration tests verifying standard deviation generation (`y_pp_std`), draws saving functionality, and out-of-sample predictions with missing outcomes.
- [tests/test_cli.py](file:///Users/saehwan/gitrepos/tabdat-explore-dev/tests/test_cli.py):
  - Added CLI integration flows for the new options.
- [tests/test_shell.py](file:///Users/saehwan/gitrepos/tabdat-explore-dev/tests/test_shell.py):
  - Updated autocomplete checks to match the new command signatures.

## Validation Commands and Outcomes

1. **Basedpyright Type Safety**:
   - Command: `uv run basedpyright`
   - Outcome: `0 errors, 0 warnings, 0 notes`
2. **Pytest Target Integration Tests**:
   - Command: `uv run pytest tests/test_parser.py -k "predict" && uv run pytest tests/test_executor.py -k "bayes"`
   - Outcome: All target tests passed.
3. **Full Test Suite Validation**:
   - Command: `uv run pytest`
   - Outcome: `940 passed, 311 warnings in 20.04s`
