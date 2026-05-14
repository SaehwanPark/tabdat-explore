# Phase 14 Slices 10-11 Command Contract

## Roadmap Phase

- Phase 14 endogeneity and panel foundations
  - Slice 10: IV estimator expansion (`ivregress gmm`)
  - Slice 11: IV endogenous diagnostics (`estat endogenous` after `ivregress 2sls`)

## `ivregress` estimator expansion

### Syntax

```stata
ivregress 2sls|gmm <y> [exog_vars], endog(<var>) iv(<vars>)[, robust cluster(<var>) noconstant]
```

### Rules

- Keeps one endogenous variable and one-or-more instruments.
- Supports `2sls` and `gmm` estimators through Python-first `linearmodels`.
- Preserves covariance modes:
  - nonrobust (default)
  - robust
  - cluster(`<var>`)

## `estat overid` after `ivregress`

### Syntax

```stata
estat overid
```

### Rules

- Requires prior `ivregress` model state.
- After `ivregress 2sls`: returns deterministic `sargan` and `wooldridge_overid` rows.
- After `ivregress gmm`: returns deterministic `gmm_j` rows.

## `estat endogenous`

### Syntax

```stata
estat endogenous
```

### Rules

- Existing behavior remains unchanged after prior `cfregress`.
- New behavior: after prior `ivregress 2sls`, returns deterministic rows for:
  - `durbin`
  - `wu_hausman`
  with metrics `statistic`, `p_value`, `df`, and `distribution`.
- Guard: after prior `ivregress gmm`, returns
  - `estat endogenous requires a prior ivregress 2sls model`

## Acceptance Criteria

- `ivregress gmm` parses and executes with existing IV option/covariance surface.
- `estat overid` works deterministically after both `ivregress 2sls` and `ivregress gmm`.
- `estat endogenous` works after `ivregress 2sls` and preserves current `cfregress` path.
- Existing `regress`/`cfregress`/`xtreg`/`xtdata` behavior remains stable.
- Focused parser/executor/CLI/shell tests pass.
