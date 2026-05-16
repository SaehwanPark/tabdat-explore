# Phase 16 Slice 2 Implementation Report

## Scope

Implemented one bounded Phase 16 slice on branch
`codex/tmp-phase16-slice2-nbreg-gof`:

- Slice 2: bounded negative-binomial count-model semantics (`nbreg`) with deterministic
  post-estimation support

## What Changed

### Parser and shell command surface

- Added `nbreg <y> <xvars>[, robust cluster(<var>) noconstant]`.
- Reused existing `estat gof` parser surface with `nbreg` executor routing.
- Added shell completion support for `nbreg` options and column suggestions.

### Executor and formatter behavior

- Added bounded `nbreg` execution with deterministic covariance labels:
  - `nonrobust` (default)
  - `robust`
  - `cluster(<var>)`
- Added deterministic non-negative outcome guard and complete-case sampling.
- Added deterministic `nbreg` output formatting with coefficient table and log-likelihood.
- Added `predict <newvar>[, xb residuals]` routing after successful `nbreg`.
- Added `estat gof` diagnostics after successful `nbreg`.

### State behavior

- `nbreg` clears incompatible prior estimation-family state.
- Existing model-family routing behavior remains intact.

### Help and docs

- Added in-app `nbreg` help topic.
- Updated `predict` and `estat` in-app help topics.
- Updated SDD/docs (`SPEC.md`, `ARCHITECTURE.md`, `README.md`, `CHANGELOG.md`).

## Validation

- `uv run pytest tests/test_parser.py tests/test_shell.py tests/test_help.py tests/test_executor.py tests/test_cli.py -k "nbreg or gof or predict"`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pyright`
- `uv run mypy`
- `uv run pytest -q`
- `uv run python integrated_testing/run_e2e.py`
