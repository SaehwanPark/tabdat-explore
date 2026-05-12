# Phase 13 Slice 3 Command Contract

## Request Summary

Implement the next executable Phase 13 linear-econometrics slice by adding post-estimation
linear diagnostics while preserving existing `regress` and `predict` behavior.

## Roadmap Phase

- Phase 13 core linear econometrics (slice 3)

## Command Contracts

### `estat`

#### Syntax

```stata
estat residuals
estat ovtest
estat vif
```

#### Rules

- Requires an active dataset.
- Requires a prior successful `regress` model in session state.
- Subcommands:
  - `residuals`: display residual-analysis summary metrics.
  - `ovtest`: run Ramsey RESET-style specification test and report statistic/p-value metadata.
  - `vif`: report predictor-level variance inflation factors.
- Diagnostics should use Python-first `statsmodels` APIs.
- Diagnostics should run with best-effort compatibility for OLS, WLS, and GLS fitted models.
- If a diagnostic cannot be produced for the current model shape, fail with a deterministic error.

#### User-Facing Errors

- Missing active dataset: existing `NoActiveDatasetError` shape.
- Missing prior model: `estat requires a prior regress model`.
- Invalid syntax: `estat expects syntax: estat <residuals|ovtest|vif>`.
- Invalid subcommand: `estat subcommand must be residuals, ovtest, or vif`.
- Unsupported diagnostic execution for current model:
  - `estat residuals failed for current model`
  - `estat ovtest failed for current model`
  - `estat vif failed for current model`

## Acceptance Criteria

- Parser accepts supported `estat` subcommands and rejects malformed/unsupported forms.
- Executor returns deterministic tabular outputs for `estat residuals`, `estat ovtest`, and `estat vif`.
- `estat` fails without prior `regress` state.
- `estat` works after OLS and best-effort weighted (`wls`/`gls`) regressions.
- CLI/shell tests cover successful and failure flows.
- SDD docs and changelog align with implemented Phase 13 slice scope.
