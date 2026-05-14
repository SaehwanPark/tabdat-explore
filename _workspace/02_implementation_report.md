# Phase 14 Slices 10-11 Implementation Report

## Scope

Implemented two bounded Phase 14 slices on one branch:

- Slice 10: `ivregress gmm` and IV overidentification output compatibility
- Slice 11: `estat endogenous` after `ivregress 2sls`

## What Changed

### Parser/model behavior

- Expanded `ivregress` estimator contract from `2sls` to `2sls|gmm`.
- Updated parser syntax/errors for `ivregress 2sls|gmm ...` while preserving existing IV option
  handling (`endog`, `iv`, `robust`, `cluster`, `noconstant`).

### Executor/model-state behavior

- Added `linearmodels.IVGMM` execution path to `ivregress`.
- Preserved covariance routing across nonrobust, robust, and clustered IV modes.
- Extended IV state to record estimator family (`2sls` or `gmm`) for post-estimation routing.
- Expanded `estat overid` behavior:
  - `2sls`: deterministic `sargan` and `wooldridge_overid` rows
  - `gmm`: deterministic `gmm_j` rows
- Extended `estat endogenous` routing:
  - preserved existing `cfregress` residual-inclusion diagnostics path
  - added IV path after `ivregress 2sls` with deterministic Durbin/Wu-Hausman rows
  - added explicit guard for non-2SLS IV state (`ivregress gmm`)

### CLI/shell behavior

- CLI Phase 14 IV flow coverage now includes `ivregress gmm`.
- Shell completion coverage confirms column completions work for `ivregress gmm ...`.

### Documentation and SDD state

- Updated `SPEC.md`, `ARCHITECTURE.md`, `README.md`, and `CHANGELOG.md`.
- Updated `_workspace` handoff artifacts for slices 10-11 delivery.

## Checkpoint Commits

- `feat(iv): add ivregress gmm and gmm overid diagnostics`
- `feat(estat): support iv 2sls endogenous diagnostics`

## Files Changed

- `src/tabdat/models.py`
- `src/tabdat/parser.py`
- `src/tabdat/executor.py`
- `tests/test_parser.py`
- `tests/test_executor.py`
- `tests/test_cli.py`
- `tests/test_shell.py`
- `SPEC.md`
- `ARCHITECTURE.md`
- `README.md`
- `CHANGELOG.md`
- `_workspace/00_input/request-summary.md`
- `_workspace/01_product_command-contract.md`
- `_workspace/02_implementation_report.md`
- `_workspace/03_qa_report.md`
- `_workspace/final/tabdat-delivery-summary.md`
