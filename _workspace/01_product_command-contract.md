# Phase 14 Slice 9 Command Contract

## Roadmap Phase

- Phase 14 endogeneity and panel foundations
  - Slice 9: expanded control-function endogenous diagnostics (`estat endogenous`)

## `estat endogenous` after `cfregress`

### Syntax

```stata
estat endogenous
```

### Rules

- Requires an active dataset.
- Requires a prior fitted model from `cfregress`.
- Runs a control-function residual-inclusion endogeneity diagnostic using the second-stage
  control-function coefficient on `cf_residual`.
- Returns a deterministic table with rows for:
  - `test`: `cf_residual`
  - `estimate`: coefficient value of `cf_residual`
  - `std_error`: standard error of `cf_residual`
  - `statistic`: t/z statistic of `cf_residual`
  - `p_value`: p-value of `cf_residual`
  - `ci_level`: confidence interval level (95)
  - `ci_lower`: lower confidence bound of `cf_residual`
  - `ci_upper`: upper confidence bound of `cf_residual`
  - `distribution`: `t` or `normal` for the statistic family
  - `df`: residual degrees of freedom for `t`; `not_available` for normal-approximation output
- No new `cfregress` or `estat` options are introduced.

### User-facing errors

- Missing prerequisite model state:
  - `estat endogenous requires a prior cfregress model`
- Missing residual-inclusion term statistics in fitted model:
  - `estat endogenous failed for current model`

## Acceptance Criteria

- `estat endogenous` succeeds after `cfregress` with deterministic expanded output shape.
- Existing `estat` behavior for `residuals`, `ovtest`, `vif`, `firststage`, `overid`, and `hausman`
  remains unchanged.
- CLI coverage demonstrates `use -> cfregress -> estat endogenous` flow with expanded diagnostics.
- Full quality checks pass (`ruff`, `pyright`, `mypy`, `pytest`).
- Integrated E2E scenarios `s1` through `s5` pass.
- SDD/docs and `_workspace` artifacts reflect delivered behavior.
