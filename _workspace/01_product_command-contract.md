# Phase 17 Slice 3 Command Contract

## Roadmap Phase

- Phase 17 advanced empirical methods
  - Slice 3: bounded dynamic-panel starter (`xtabond`) plus DID post-estimation diagnostics

## `xtabond`

### Syntax

```stata
xtabond <y> [xvars] [, robust]
```

### Rules

- Requires one active dataset.
- Requires prior panel metadata via `panel <id_var> <time_var>`.
- Requires one outcome variable.
- Optional predictors are numeric and may be empty.
- Supports covariance modes:
  - nonrobust (default)
  - robust

## `estat did`

### Syntax

```stata
estat did
```

### Rules

- Requires one active dataset.
- Requires prior successful `did` model state.
- Returns deterministic interaction-diagnostic rows for the DID interaction term.

## Error/guard behavior

- Missing panel metadata for `xtabond`:
  - `xtabond requires panel metadata; run panel <id_var> <time_var> first`
- Empty complete-observation dynamic sample:
  - `xtabond requires at least one complete observation`
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

- `xtabond` parses and executes with optional predictors and optional `robust`.
- deterministic typed/formatted output includes dynamic-panel coefficient rows.
- `estat did` parses and executes after `did` with deterministic table output.
- focused parser/executor/CLI/shell/help coverage passes.
