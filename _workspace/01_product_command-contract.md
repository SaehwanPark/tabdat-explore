# Phase 14 Slice 1 Command Contract

## Request Summary

Close prerequisite Phase 13 hardening gaps first, then implement the first executable Phase 14
endogeneity slice with a Python-first IV command.

## Roadmap Phase

- Phase 13 hardening closeout (prerequisite)
- Phase 14 endogeneity and panel foundations (slice 1)

## Prerequisite Gate Contract

### Integrated E2E hardening

- Integrated harness must pass all scenarios.
- Existing `s4_penguins_script_repro` expectations must match current `export` wording
  (`Exported:`).
- Integrated harness must include one real-dataset Phase 13 dogfood flow that exercises
  `regress`, `predict`, and `estat` together.

## Command Contract

### `ivregress`

#### Syntax

```stata
ivregress 2sls <y> [exog_vars], endog(<var>) iv(<vars>)
ivregress 2sls <y> [exog_vars], endog(<var>) iv(<vars>) robust
ivregress 2sls <y> [exog_vars], endog(<var>) iv(<vars>) cluster(<var>)
ivregress 2sls <y> [exog_vars], endog(<var>) iv(<vars>) noconstant
```

#### Rules

- Requires an active dataset.
- Requires estimator token `2sls`.
- Requires one endogenous variable via `endog(...)`.
- Requires one-or-more instruments via `iv(...)`.
- `robust` and `cluster(...)` are mutually exclusive.
- `cluster(...)` requires one clustering variable.
- Endogenous variable cannot also appear in exogenous variables.
- Execution uses Python-first `linearmodels` IV2SLS.
- Covariance labels in output:
  - default: `nonrobust`
  - robust: `robust`
  - clustered: `cluster(<var>)`

#### User-facing errors

- Invalid command shape:
  - `ivregress expects syntax: ivregress 2sls <y> [exog_vars], endog(<var>) iv(<vars>)`
- Invalid estimator token:
  - `ivregress estimator must be 2sls`
- Invalid `endog`/`iv`/`cluster` option arity:
  - `ivregress option endog expects one variable`
  - `ivregress option iv expects at least one variable`
  - `ivregress option cluster expects one variable`
- Conflicting covariance options:
  - `ivregress cannot combine robust and cluster`
- Exogenous/endogenous overlap:
  - `ivregress endog variable must not appear in exogenous variables`
- Execution failure:
  - `ivregress failed`

## Acceptance Criteria

- Prerequisite integrated-harness gate passes (`s1`..`s5`).
- Parser accepts valid `ivregress 2sls` forms and rejects malformed forms deterministically.
- Executor returns deterministic IV results for default, robust, and clustered covariance modes.
- CLI/shell tests cover `ivregress` command success and completion flows.
- SDD docs and changelog reflect:
  - completed Phase 13 hardening
  - started Phase 14 with `ivregress 2sls` slice
