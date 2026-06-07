# Phase 19 Slice 6 Command Contract: `predict ..., spatial_lag` after `spregress`

## Roadmap Phase

- Phase 19 modern extensions
- Spatial predictive workflow, split into a thinner first slice over the existing `spregress`
  foundation

## Syntax

```stata
predict <newvar>[, xb residuals pr spatial_lag]
```

This slice adds one new `predict` mode:

```stata
predict <newvar>, spatial_lag
```

## Behavior

- `predict <newvar>, spatial_lag` is supported only after a successful
  `spregress <y> <xvars>, coord(...) model(lag) ...` fit.
- The new column contains the fitted spatial-lag full prediction for the same active dataset sample
  used by the current `spregress` state.
- Existing `predict <newvar>` / `predict <newvar>, xb` behavior after `spregress` remains
  supported and unchanged.
- Existing `predict` behavior for all non-spatial model families remains unchanged.

## Option Rules

- `xb`, `residuals`, `pr`, and `spatial_lag` are mutually exclusive flags.
- Unsupported predict options still fail with deterministic parser errors.
- `predict ..., spatial_lag` after `spregress ... model(error)` fails deterministically at
  execution time with a user-facing error explaining that the mode is only available after
  `model(lag)`.

## Data/State Rules

- This slice is same-sample only.
- It relies on the currently stored spatial regression state and does not attempt out-of-sample or
  cross-dataset spatial prediction.
- If the active dataset has changed such that the needed spatial columns are unavailable, prediction
  must fail deterministically rather than silently recomputing with partial state.

## Output Contract

- Successful execution follows the existing transform transcript:
  - `Predicted <newvar>: <rows> rows, <cols> columns`
- No new result formatter output is introduced beyond the added active-dataset column.

## Help Contract

- Update `help predict` to include `spatial_lag`.
- Update `help spregress` to show the new prediction workflow.
- `tests/test_help.py` command coverage gate must still pass.

## Acceptance Criteria

- Parser, shell, executor, CLI, and help tests cover the new behavior.
- `predict yhat, spatial_lag` parses successfully.
- `predict ..., spatial_lag` cannot be combined with `xb`, `residuals`, or `pr`.
- `spregress ... model(lag)` then `predict ..., spatial_lag` succeeds.
- `spregress ... model(error)` then `predict ..., spatial_lag` fails deterministically.
- Full suite and static checks pass.
- `SPEC.md` and SDD docs reflect that this sub-slice is complete while broader spatial follow-on
  work remains.
