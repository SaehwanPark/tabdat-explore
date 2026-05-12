# Phase 14 Slice 2+3 Command Contract

## Roadmap Phase

- Phase 14 endogeneity and panel foundations
  - Slice 2: IV diagnostics
  - Slice 3: panel FE/RE starter + Hausman comparison

## Slice 2 Contract

### `estat firststage`

#### Syntax

```stata
estat firststage
```

#### Rules

- Requires an active dataset.
- Requires a prior successful `ivregress` model state.
- Reports first-stage diagnostics for endogenous regressors.

#### User-facing errors

- Missing prior IV state:
  - `estat firststage requires a prior ivregress model`
- Execution failure:
  - `estat firststage failed for current model`

### `estat overid`

#### Syntax

```stata
estat overid
```

#### Rules

- Requires an active dataset.
- Requires a prior successful `ivregress` model state.
- Reports deterministic overidentification diagnostics using:
  - `sargan`
  - `wooldridge_overid`
- Exactly identified models must report deterministic not-available output, not crash.

#### User-facing errors

- Missing prior IV state:
  - `estat overid requires a prior ivregress model`
- Execution failure:
  - `estat overid failed for current model`

## Slice 3 Contract

### `xtreg`

#### Syntax

```stata
xtreg <y> <xvars>, fe
xtreg <y> <xvars>, re
xtreg <y> <xvars>, fe robust
xtreg <y> <xvars>, re robust
xtreg <y> <xvars>, fe cluster(<var>)
xtreg <y> <xvars>, re cluster(<var>)
```

#### Rules

- Requires an active dataset.
- Requires prior panel metadata from `panel <id_var> <time_var>`.
- Requires exactly one estimator flag: `fe` or `re`.
- `robust` and `cluster(<var>)` are mutually exclusive.
- `cluster(<var>)` requires exactly one variable.
- Execution uses Python-first `linearmodels` panel estimators.

#### User-facing errors

- Missing panel metadata:
  - `xtreg requires panel metadata; run panel <id_var> <time_var> first`
- Invalid command shape:
  - `xtreg expects syntax: xtreg <y> <xvars>, fe|re`
- Invalid estimator selection:
  - `xtreg requires exactly one of fe or re`
- Invalid cluster option arity:
  - `xtreg option cluster expects one variable`
- Conflicting covariance options:
  - `xtreg cannot combine robust and cluster`
- Execution failure:
  - `xtreg failed`

### `estat hausman`

#### Syntax

```stata
estat hausman
```

#### Rules

- Requires an active dataset.
- Requires prior `xtreg ..., fe` and `xtreg ..., re` model states.
- Requires matching FE/RE model specs (outcome, predictors, panel metadata, covariance mode).
- Supports non-cluster and robust model pairs in this slice.
- Clustered FE/RE fits are rejected for Hausman in this slice.

#### User-facing errors

- Missing prior panel-model states:
  - `estat hausman requires prior xtreg fe and xtreg re models`
- Non-matching FE/RE specs:
  - `estat hausman requires matching xtreg specifications`
- Non-matching covariance mode:
  - `estat hausman requires matching xtreg covariance modes`
- Clustered Hausman unsupported:
  - `estat hausman does not support clustered covariance`
- Execution failure:
  - `estat hausman failed for current models`

## Cross-family State Rules

- Running `regress` invalidates stored IV and panel-model states.
- Running `ivregress` invalidates stored linear-regression and panel-model states.
- Running `xtreg` invalidates stored linear-regression and IV states.

## Acceptance Criteria

- Parser accepts valid forms and rejects malformed forms deterministically.
- Executor returns deterministic result shapes for all added commands.
- CLI/shell tests cover command success and completion paths.
- Full quality checks pass (`ruff`, `pyright`, `mypy`, `pytest`).
- SDD/docs and `_workspace` artifacts reflect delivered behavior.
