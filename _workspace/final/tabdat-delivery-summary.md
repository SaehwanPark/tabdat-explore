# Phase 19 Bayesian Posterior Predictive Delivery Summary

## Outcome

Completed posterior predictive `predict` support after `bayes:` MCMC fits.

## Implemented

- Added `predict <newvar>, posterior_predictive`.
- Supported posterior predictive mean columns after both `bayes: regress` and `bayes: logit`.
- Preserved active row order and active rows with missing predictors.
- Added deterministic parser and executor guards for invalid mode combinations and missing
  Bayesian MCMC state.
- Updated shell completions, help topics, SPEC, architecture notes, changelog, and package version.

## Validation

- `uv run pytest tests/test_parser.py -k "predict or bayes"`
- `uv run pytest tests/test_executor.py -k "bayes_prefix or posterior_predictive"`
- `uv run pytest tests/test_cli.py -k "bayes_prefix"`
- `uv run pytest tests/test_shell.py::test_completer_suggests_phase_13_and_phase_14_commands_and_options`
- `uv run basedpyright`
- `uv run ruff check`
- `uv run ruff format --check`

## Remaining Phase 19 Slices

- Bayesian diagnostic plots/tables and posterior predictive intervals.
- Out-of-sample Bayesian prediction syntax.
- Advanced spatial autoregressive models and diagnostics.
- Broader spatial prediction workflows.
