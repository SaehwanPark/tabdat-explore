# Phase 19 Bayesian `bayesplot` Implementation Report

## Scope

Implemented `bayesplot <trace|density|autocorrelation>` after `bayes:` MCMC fits on branch
`temp/phase19-bayesplot-diagnostics`.

## What Changed

- Parser/model: added a typed `BayesPlotCommand` with `saving(<path>)` and `noopen` support.
- Executor: added `bayesplot` routing over retained Bayesian MCMC state with deterministic guards
  for missing `bayes:` state and legacy `bayes linear` state.
- Visualization: added artifact rendering for trace, density, and autocorrelation diagnostics
  from retained posterior draws, reusing existing `.svg`/`.png` path validation.
- CLI/shell/help: added interactive default-path collision avoidance, autocomplete, and a help
  topic for `bayesplot`.
- SDD: updated `SPEC.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, `README.md`, workspace reports, and
  version metadata.

## Validation Commands

- `uv run pytest tests/test_parser.py::test_parse_phase_19_bayesplot_command tests/test_parser.py::test_parse_phase_19_bayesplot_errors tests/test_executor.py::test_phase_19_bayesplot_writes_diagnostic_artifact tests/test_executor.py::test_phase_19_bayesplot_default_path_uses_graph_config tests/test_executor.py::test_phase_19_bayesplot_requires_bayes_prefix_state tests/test_cli.py::test_cli_runs_phase_19_bayesplot_flow tests/test_shell.py::test_completer_suggests_command_names tests/test_shell.py::test_completer_suggests_bayesplot_kinds_and_options tests/test_help.py::test_bayesplot_help_mentions_diagnostic_artifacts`

## Known Gaps

- Posterior predictive interval columns remain future Phase 19 work.
- Explicit out-of-sample Bayesian prediction syntax remains future Phase 19 work.
- Spatial diagnostics and expanded spatial prediction remain future Phase 19 work.
