# Phase 14 Slices 12-13 Command Contract

## Roadmap Phase

- Phase 14 endogeneity and panel foundations
  - Slice 12: control-function first-stage diagnostics (`estat firststage` after `cfregress`)
  - Slice 13: panel report semantic expansion

## `estat firststage` after `cfregress`

### Syntax

```stata
estat firststage
```

### Rules

- Existing behavior remains unchanged after prior `ivregress`.
- New behavior: after prior `cfregress`, return deterministic first-stage diagnostic rows with
  headers `Variable`, `Metric`, and `Value`.
- Include coefficient-level metrics for first-stage terms:
  - `coefficient`
  - `std_error`
  - `statistic`
  - `p_value`
- Include first-stage fit summary rows:
  - `observation_count`
  - `r_squared`
- Preserve existing error when no compatible prior model state exists:
  - `estat firststage requires a prior ivregress model`

## `panel` report semantic expansion

### Syntax

```stata
panel
```

### Rules

- Existing `panel set <id_var> <time_var>` and `panel clear` behavior remains unchanged.
- Existing `panel` with no active metadata remains unchanged (`Panel: none`).
- After panel metadata is set, `panel` report output includes deterministic structure metrics:
  - total observations
  - distinct entity count
  - distinct time count
  - per-entity minimum and maximum observation counts
  - balancedness indicator (`yes` when min==max, else `no`)

## Acceptance Criteria

- `estat firststage` works after both `ivregress` and `cfregress`.
- Existing `ivregress` diagnostics and `cfregress` `predict`/`estat endogenous` behavior remain stable.
- `panel` report includes deterministic structure metrics when metadata is set.
- Existing `panel set`, `panel clear`, and `panel`-without-metadata behavior remain stable.
- Focused executor/backend/formatter/CLI tests pass.
