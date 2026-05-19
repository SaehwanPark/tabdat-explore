# Phase 17 Completion Contract (Slices 5-7)

## Roadmap Phase

- Phase 17 advanced empirical methods
  - Slice 5: `xtabond` post-estimation/prediction extension
  - Slice 6: nonlinear panel starter (`xtlogit`)
  - Slice 7: semiparametric/nonparametric starter (`lowess`)

## `xtabond` extensions

### Added behavior

- `estat overid` executes after successful `xtabond`.
- `predict <newvar>[, xb residuals]` executes after successful `xtabond`.

### Guards

- `predict` requires matching panel metadata and required model variables.
- `predict ..., pr` is not available after `xtabond`.

## `xtlogit`

### Syntax

```stata
xtlogit <y> <xvars>, fe [robust]
```

### Rules

- Requires active dataset.
- Requires prior `panel <id_var> <time_var>` metadata.
- Outcome must be binary (`0`/`1`).
- Bounded fixed-effects nonlinear-panel workflow.

## `lowess`

### Syntax

```stata
lowess <y> <x>, gen(<newvar>) [bandwidth=<0,1>]
```

### Rules

- Requires active dataset.
- Requires numeric `<y>` and `<x>`.
- `gen(...)` required and must be a new column name.
- `bandwidth` optional, default `2/3`, and must satisfy `0 < bandwidth < 1`.

## Acceptance Criteria

- Focused parser/executor/CLI/shell/help tests pass for all new/extended behaviors.
- Existing command-family behavior remains stable.
- In-app help includes accurate topics for newly added commands and changed behavior.
