# Phase 15 Slice 2-3 Delivery Summary

## Outcome

Completed two bounded Phase 15 slices in one branch:

- Slice 2: `probit` nonlinear binary-choice estimator core
- Slice 3: `estat margins` after `logit`/`probit`

## Implemented

- Added `probit <y> <xvars>[, robust cluster(<var>) noconstant]` parser and shell completion support.
- Added Python-first `statsmodels` `probit` execution with:
  - default nonrobust covariance
  - HC1 robust covariance
  - clustered covariance via `cluster(<var>)`
- Added deterministic `probit` CLI output with pseudo R-squared and coefficient rows.
- Added strict `probit` sample/outcome guards (numeric + binary outcome, complete-case sample,
  clustered-value requirements).
- Added `estat margins` after successful `logit`/`probit` with deterministic predictor-level
  metrics:
  - `dy_dx`, `std_error`, `statistic`, `p_value`, `ci_lower`, `ci_upper`.
- Added strict `estat margins` prerequisite guard when no prior binary-choice model state exists.
- Updated focused tests and SDD/handoff docs.

## Validation

- Focused tests:
  - `uv run pytest tests/test_parser.py -k "phase_15 or invalid_commands or phase_13_estat"`
  - `uv run pytest tests/test_shell.py -k "phase_13_and_phase_14_commands_and_options"`
  - `uv run pytest tests/test_executor.py -k "phase_15_logit or phase_15_probit or phase_15_estat_margins"`
  - `uv run pytest tests/test_cli.py -k "phase_15_logit or phase_15_probit or phase_15_estat_margins"`
- Full quality and integration gates:
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run pyright`
  - `uv run mypy`
  - `uv run pytest -q`
  - `uv run python integrated_testing/run_e2e.py`

All commands passed.

## Residual Risk

- Binary-choice convergence and perfect-separation warnings can still occur on tiny/pathological
  datasets; this slice keeps behavior bounded and deterministic but does not add warning-specific
  UX beyond existing command success/failure surfaces.

## Suggested Follow-up

- Continue Phase 15 with one bounded next slice from `SPEC.md` remaining list:
  nonlinear prediction routing, limited-dependent estimator entrypoint, or sample-selection surface.
