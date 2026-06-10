# Phase 19 Bayesian Posterior Predictive Implementation Report

## Scope

Implemented `predict <newvar>, posterior_predictive` after `bayes:` MCMC fits on branch
`codex/phase19-bayes-posterior-predict`.

## What Changed

- Parser/model: added `posterior_predictive` as a typed, mutually exclusive `PredictCommand`
  mode.
- Executor: retained the fitted Bambi model in Bayesian MCMC state and added row-preserving
  posterior predictive mean extraction from ArViZ posterior predictive draws.
- Backend boundary: reused `add_numeric_column_from_values` so the output column follows existing
  active-dataset transform behavior.
- Shell/help: added completion and help documentation for the new predict option.
- Tests: added parser, executor, CLI, and shell coverage for the new mode and guards.
- SDD: updated `SPEC.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, workspace reports, and package
  version metadata.

## Validation Commands

- `uv run pytest tests/test_parser.py -k "predict or bayes"` passed.
- `uv run pytest tests/test_executor.py -k "bayes_prefix or posterior_predictive"` passed.
- `uv run pytest tests/test_cli.py -k "bayes_prefix"` passed.
- `uv run pytest tests/test_shell.py::test_completer_suggests_phase_13_and_phase_14_commands_and_options` passed.
- `uv run basedpyright` passed with 0 errors.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed.

## Known Gaps

- Posterior intervals, posterior diagnostic plots, and out-of-sample prediction syntax remain
  future Phase 19 work.
