# Phase 14 Slice 9 Delivery Summary

## Outcome

Completed Phase 14 Slice 9 in one bounded delivery branch:

- Slice 9: expanded control-function endogenous diagnostics via existing command surface:
  - `estat endogenous`
  - after successful `cfregress`

## Implemented

- Extended executor-held control-function endogenous diagnostic state from `cfregress` fits with
  residual-inclusion confidence-interval and distribution metadata.
- Expanded deterministic `estat endogenous` table output for residual-inclusion test rows:
  - `test=cf_residual`
  - `estimate=<coef>`
  - `std_error=<se>`
  - `statistic=<t/z>`
  - `p_value=<p>`
  - `ci_level=95`
  - `ci_lower=<lower>`
  - `ci_upper=<upper>`
  - `distribution=t|normal`
  - `df=<df>|not_available`
- Preserved `estat endogenous` parser/shell command surface with no new options.
- Added focused executor and CLI coverage for expanded `cfregress -> estat endogenous` diagnostics.
- Updated SDD/docs and `_workspace` artifacts.

## Validation

- `uv run pytest -q tests/test_executor.py -k "estat_endogenous"`
- `uv run pytest -q tests/test_cli.py -k "phase_14_cfregress_flow"`
- `uv run pytest -q tests/test_executor.py -k "cfregress or estat"`
- `uv run pytest -q tests/test_cli.py -k "cfregress_flow or estat"`
- `uv run pytest -q tests/test_parser.py -k "estat"`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pyright`
- `uv run mypy`
- `uv run pytest -q`
- `uv run python integrated_testing/run_e2e.py`

All commands passed.

## Residual Risk

- `estat endogenous` remains intentionally scoped to residual-inclusion coefficient diagnostics and
  fixed 95% confidence-interval metadata.

## Suggested Follow-up

- Continue Phase 14 with any remaining control-function or panel-semantic extensions under
  dedicated contracts.
