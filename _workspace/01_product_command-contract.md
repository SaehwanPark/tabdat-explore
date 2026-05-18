# Phase 17 Slice 4 Command Contract

## Roadmap Phase

- Phase 17 advanced empirical methods
  - Slice 4: bounded dynamic-panel option expansion (`xtabond`) plus richer DID diagnostics

## `xtabond`

### Syntax

```stata
xtabond <y> [xvars] [, robust lags(#) instlag(#)]
```

### Rules

- Requires one active dataset.
- Requires prior panel metadata via `panel <id_var> <time_var>`.
- Requires one outcome variable.
- Optional predictors are numeric and may be empty.
- Supports covariance modes:
  - nonrobust (default)
  - robust
- Supports lag options:
  - `lags(#)` where `# >= 1`
  - `instlag(#)` where `# >= 2`
  - `instlag(#)` must be strictly greater than `lags(#)`.

## `estat did`

### Syntax

```stata
estat did
```

### Rules

- Requires one active dataset.
- Requires prior successful `did` model state.
- Returns deterministic interaction diagnostics plus deterministic DID cell counts/means and raw
  diff-in-diff contrasts.

## Error/guard behavior

- Missing panel metadata for `xtabond`:
  - `xtabond requires panel metadata; run panel <id_var> <time_var> first`
- Empty complete-observation dynamic sample:
  - `xtabond requires at least one complete observation`
- Invalid lag options:
  - `xtabond option lags must be at least 1`
  - `xtabond option instlag must be at least 2`
  - `xtabond option instlag must be greater than option lags`
- Missing variables/non-numeric variables:
  - existing unknown-variable and numeric-type errors
- Fit failures:
  - `xtabond failed`
- Missing DID state for `estat did`:
  - `estat did requires a prior did model`

## State behavior

- Running `xtabond` clears incompatible prior estimation-family state.
- Existing `predict` and `estat` boundaries for other families remain unchanged.

## Acceptance Criteria

- `xtabond` parses and executes with optional predictors plus `robust`, `lags(#)`, and `instlag(#)`.
- Deterministic typed/formatted output includes dynamic-panel coefficient rows with lag-aware naming.
- `estat did` parses and executes after `did` with deterministic expanded table output.
- Focused parser/executor/CLI/shell/help coverage passes.
