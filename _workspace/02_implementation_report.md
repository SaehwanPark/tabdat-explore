# Bayesian Posterior Predictive Intervals Implementation Report

## Contract Consumed

`_workspace/01_product_command-contract.md`

## What Changed

- Parser/model: extended `PredictCommand` with `interval` and `level`, and parsed
  `posterior_predictive interval [level(<num>)]` with command-level validation.
- Executor/backend: summarized posterior predictive draws into means and central quantile
  intervals, and added atomic multi-column numeric prediction insertion.
- CLI/shell/help: updated smoke coverage, completions, and help text for interval prediction.
- SDD: updated README, SPEC, architecture notes, changelog, and workspace handoffs.

## Validation Commands

- `uv run pytest tests/test_parser.py tests/test_executor.py::test_phase_19_bayes_prefix_predict_supports_posterior_predictive tests/test_executor.py::test_phase_19_bayes_prefix_predict_supports_posterior_predictive_intervals tests/test_executor.py::test_phase_19_bayes_prefix_logit_predict_supports_posterior_predictive tests/test_executor.py::test_phase_19_bayes_prefix_logit_predict_intervals_are_probabilities tests/test_executor.py::test_phase_19_bayes_prefix_posterior_predictive_preserves_missing_rows tests/test_executor.py::test_phase_19_bayes_prefix_posterior_predictive_all_missing_rows tests/test_executor.py::test_phase_19_bayes_prefix_posterior_predictive_interval_collision_is_atomic tests/test_executor.py::test_phase_19_bayes_prefix_posterior_predictive_requires_bayes_prefix tests/test_cli.py::test_cli_runs_phase_19_bayes_prefix_posterior_predictive_flow tests/test_shell.py::test_completer_suggests_phase_13_and_phase_14_commands_and_options tests/test_help.py`
- `uv run ruff check`
- `uv run ruff format --check`
- `uv run basedpyright`
- `uv run pytest`

## Known Gaps

- Out-of-sample Bayesian prediction workflows remain future work.
- Interval type is fixed to central quantile intervals.
- Custom interval output names are out of scope.
