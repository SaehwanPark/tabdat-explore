# Phase 19 Bayesian `estat bayes` Implementation Report

## Scope

Implemented `estat bayes` after `bayes:` MCMC fits on branch `temp/phase19-bayes-estat`.

## What Changed

- Parser/model: added `bayes` as a typed `EstatCommand` subcommand with existing `estat`
  validation rules preserved.
- Executor: added `estat bayes` routing over retained Bayesian MCMC state and a deterministic
  `_estat_bayes_table(...)` helper that reads ArviZ summaries plus sampler divergence counts.
- Diagnostics formatting: normalized non-finite diagnostics such as single-chain `r_hat` to
  `not_available` instead of leaking raw `nan`.
- Shell/help: added `estat bayes` completion and help documentation in `estat` and `bayes_prefix`
  topics.
- Tests: added parser, executor, CLI, shell, and help coverage for the new subcommand and guards.
- SDD: updated `SPEC.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, workspace reports, and version
  metadata.

## Validation Commands

- `uv run pytest tests/test_parser.py::test_parse_phase_13_estat_command tests/test_shell.py::test_completer_suggests_phase_13_and_phase_14_commands_and_options tests/test_help.py::test_estat_help_mentions_bayes_diagnostics tests/test_executor.py::test_phase_19_estat_bayes_after_bayes_prefix_regress tests/test_executor.py::test_phase_19_estat_bayes_after_bayes_prefix_logit tests/test_executor.py::test_phase_19_estat_bayes_requires_prior_bayes_prefix tests/test_executor.py::test_phase_19_estat_bayes_rejects_legacy_bayes_linear_state tests/test_cli.py::test_cli_runs_phase_19_bayes_prefix_estat_flow`
- `uv run pytest tests/test_parser.py tests/test_executor.py tests/test_cli.py tests/test_shell.py tests/test_help.py`
- `uv run basedpyright`
- `uv run ruff check`
- `uv run ruff format --check`

## Known Gaps

- Trace/density/autocorrelation plots remain future Phase 19 work.
- Posterior predictive intervals remain future Phase 19 work.
- Out-of-sample Bayesian prediction syntax remains future Phase 19 work.
