# Phase 14 Slice 5 Command Contract

## Roadmap Phase

- Phase 14 endogeneity and panel foundations
  - Slice 5: control-function core (`cfregress`)

## `cfregress`

### Syntax

```stata
cfregress <y> [exog_vars], endog(<var>) iv(<vars>)
cfregress <y> [exog_vars], endog(<var>) iv(<vars>) robust
cfregress <y> [exog_vars], endog(<var>) iv(<vars>) cluster(<var>)
cfregress <y> [exog_vars], endog(<var>) iv(<vars>) noconstant
```

### Rules

- Requires an active dataset.
- Requires one outcome variable.
- Requires exactly one endogenous variable via `endog(<var>)`.
- Requires one or more instruments via `iv(<vars>)`.
- `robust` and `cluster(<var>)` are mutually exclusive.
- `cluster(<var>)` requires exactly one variable.
- Endogenous variable cannot appear in exogenous varlist.
- Variables in outcome/exogenous/endogenous/instruments must be numeric.
- Execution performs bounded two-step control-function estimation:
  - first stage: endogenous on exogenous + instruments
  - second stage: outcome on exogenous + endogenous + first-stage residual

### User-facing errors

- Invalid command shape:
  - `cfregress expects syntax: cfregress <y> [exog_vars], endog(<var>) iv(<vars>)`
- Unsupported options:
  - `cfregress unsupported option: <options>`
- Invalid option arity:
  - `cfregress option endog expects one variable`
  - `cfregress option iv expects at least one variable`
  - `cfregress option cluster expects one variable`
- Conflicting covariance options:
  - `cfregress cannot combine robust and cluster`
- Endogenous duplicated in exogenous:
  - `cfregress endog variable must not appear in exogenous variables`
- Missing/unknown/nonnumeric prerequisites:
  - standard active-dataset and unknown/numeric errors scoped to `cfregress`
- No usable sample rows:
  - `cfregress requires at least one complete observation`

## Acceptance Criteria

- Parser accepts valid forms and rejects malformed forms deterministically.
- Executor returns deterministic control-function result shape for nonrobust/robust/clustered modes.
- CLI/shell tests cover command success and completion paths.
- Full quality checks pass (`ruff`, `pyright`, `mypy`, `pytest`).
- SDD/docs and `_workspace` artifacts reflect delivered behavior.
