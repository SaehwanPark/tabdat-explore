# Phase 14 Slice 7 Delivery Summary

## Outcome

Completed Phase 14 Slice 7 in one bounded delivery branch:

- Slice 7: control-function endogenous diagnostics via existing command surface:
  - `estat endogenous`
  - after successful `cfregress`

## Implemented

- Added executor-held control-function endogenous diagnostic state from `cfregress` fits.
- Added deterministic `estat endogenous` table output for residual-inclusion test rows:
  - `test=cf_residual`
  - `statistic=<t>`
  - `p_value=<p>`
- Extended parser/shell `estat` surface to include `endogenous` without new options.
- Added focused parser, shell, executor, and CLI coverage for `cfregress -> estat endogenous`.
- Updated SDD/docs and `_workspace` artifacts.

## Validation

- `uv run pytest -q tests/test_parser.py -k "estat"`
- `uv run pytest -q tests/test_shell.py::test_completer_suggests_phase_13_and_phase_14_commands_and_options`
- `uv run pytest -q tests/test_executor.py -k "cfregress or estat"`
- `uv run pytest -q tests/test_cli.py -k "cfregress_flow or estat"`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pyright`
- `uv run mypy`
- `uv run pytest -q`
- `uv run python integrated_testing/run_e2e.py`

All commands passed.

## Residual Risk

- `estat endogenous` is intentionally scoped to residual-inclusion t/p-value diagnostics only.

## Suggested Follow-up

- Continue Phase 14 with any remaining control-function or panel-semantic extensions under
  dedicated contracts.
