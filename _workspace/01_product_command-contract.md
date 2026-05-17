# Phase 17 Slice 2 Command Contract

## Roadmap Phase

- Phase 17 advanced empirical methods
  - Slice 2: bounded DID causal starter with deterministic prediction support

## `did`

### Syntax

```stata
did <y> [controls], treat(<var>) post(<var>) [robust]
```

### Rules

- Requires one active dataset.
- Requires prior panel metadata via `panel <id_var> <time_var>`.
- Requires one outcome variable.
- Optional controls are numeric and may be empty.
- `treat(...)` and `post(...)` each require exactly one variable.
- Treatment and post variables must be numeric binary values (`0`/`1`).
- Supports covariance modes:
  - nonrobust (default)
  - robust

## Post-estimation behavior

- `predict <newvar>[, xb]` is supported after successful `did`.
- `predict ..., residuals` and `predict ..., pr` are not supported after `did`.

## Error/guard behavior

- Missing panel metadata:
  - `did requires panel metadata; run panel <id_var> <time_var> first`
- Non-binary treatment/post inputs:
  - `did treatment and post variables must be binary with values 0 and 1`
- Missing variables/non-numeric variables:
  - existing unknown-variable and numeric-type errors
- Empty complete-observation sample:
  - `did requires at least one complete observation`
- Fit failures:
  - `did failed`

## State behavior

- Running `did` clears incompatible prior estimation-family state.
- Existing `predict` and `estat` boundaries for other families remain unchanged.

## Acceptance Criteria

- `did` parses and executes with required `treat(...)` and `post(...)` plus optional `robust`.
- deterministic typed and formatted output includes DID interaction coefficient rows.
- `predict` supports `xb` after `did`.
- focused parser/executor/CLI/shell/help coverage passes.
