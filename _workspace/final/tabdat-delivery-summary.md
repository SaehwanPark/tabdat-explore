# Phase 14 Slices 10-11 Delivery Summary

## Outcome

Completed two bounded Phase 14 slices in one branch:

- Slice 10: `ivregress gmm` plus estimator-compatible `estat overid`
- Slice 11: `estat endogenous` after `ivregress 2sls`

## Implemented

- Expanded `ivregress` command surface to `2sls|gmm` while preserving existing IV options.
- Added Python-first `IVGMM` execution path via `linearmodels`.
- Preserved deterministic covariance output across IV estimator modes.
- Extended `estat overid` output routing:
  - `2sls`: `sargan` and `wooldridge_overid`
  - `gmm`: `gmm_j`
- Extended `estat endogenous` routing:
  - existing `cfregress` residual-inclusion diagnostics unchanged
  - new IV path after `ivregress 2sls` with Durbin/Wu-Hausman diagnostics
  - explicit non-2SLS IV guard message
- Updated focused parser/executor/CLI/shell coverage and SDD/docs.

## Validation

- Focused parser/executor/CLI/shell tests for IV Phase 14 flows passed.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pyright`
- `uv run mypy`
- `uv run pytest -q`
- `uv run python integrated_testing/run_e2e.py`

All commands passed.

## Residual Risk

- `estat endogenous` IV path is intentionally scoped to prior `ivregress 2sls` state; GMM-specific
  endogenous diagnostics remain out of scope for this slice.

## Suggested Follow-up

- Continue Phase 14 with remaining panel/control-function semantic extensions under dedicated
  contracts.
