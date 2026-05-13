# Phase 14 Slice 6 Command Contract

## Roadmap Phase

- Phase 14 endogeneity and panel foundations
  - Slice 6: control-function prediction routing (`predict` after `cfregress`)

## `predict` after `cfregress`

### Syntax

```stata
predict <newvar>
predict <newvar>, residuals
```

### Rules

- Requires an active dataset.
- Requires a prior fitted model from either:
  - `regress` (existing behavior), or
  - `cfregress` (new in this slice).
- `predict <newvar>` returns fitted values (`xb`).
- `predict <newvar>, residuals` returns outcome minus fitted values.
- Prediction target variable must not already exist.
- No new `predict` options are introduced.

### User-facing errors

- Missing prerequisite model state:
  - `predict requires a prior regress or cfregress model`
- Existing output-column and unknown-variable errors remain under `predict` scope.

## Acceptance Criteria

- `predict` succeeds after `cfregress` for both `xb` and `residuals`.
- Existing `predict` behavior after `regress` remains unchanged.
- CLI coverage demonstrates `use -> cfregress -> predict -> predict, residuals` flow.
- Full quality checks pass (`ruff`, `pyright`, `mypy`, `pytest`).
- SDD/docs and `_workspace` artifacts reflect delivered behavior.
