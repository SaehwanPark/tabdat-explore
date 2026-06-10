# Phase 19 Bayesian `estat bayes` Delivery Summary

## Outcome

Completed `estat bayes` diagnostics after `bayes:` MCMC fits.

## Implemented

- Added `estat bayes`.
- Supported deterministic diagnostics after both `bayes: regress` and `bayes: logit`.
- Reported `ess_bulk`, `ess_tail`, `r_hat`, `mcse_mean`, `mcse_sd`, and sampler
  `divergence_count`.
- Normalized unavailable diagnostics from short-chain runs to `not_available`.
- Added strict guards for missing prerequisite `bayes:` state and legacy `bayes linear` state.
- Updated shell completions, help topics, spec, architecture notes, changelog, and version
  metadata.

## Validation

- `uv run pytest tests/test_parser.py tests/test_executor.py tests/test_cli.py tests/test_shell.py tests/test_help.py`
- `uv run basedpyright`
- `uv run ruff check`
- `uv run ruff format --check`

## Remaining Phase 19 Slices

- Bayesian diagnostic plots and posterior predictive intervals.
- Out-of-sample Bayesian prediction syntax.
- Advanced spatial autoregressive models and diagnostics.
- Broader spatial prediction workflows.
