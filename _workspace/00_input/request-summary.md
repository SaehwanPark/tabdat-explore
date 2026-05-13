# Phase 14 Slice 5 Request Summary

## User Goal

Resume development from the latest checkpoint by delivering the next bounded Phase 14 slice with
checkpoint commits, updated SDD/handoff artifacts, and a ready-for-review PR.

## Scope

- Phase 14 Slice 5:
  - add control-function core through
    `cfregress <y> [exog_vars], endog(<var>) iv(<vars>)[, robust cluster(<var>) noconstant]`
  - keep deterministic, bounded two-step residual-inclusion execution

## Constraints

- Preserve approach order from `SPEC.md`:
  1. Python libraries first
  2. R via `rpy2` only if Python-first is insufficient
  3. lower-level custom numerical implementation only as a last resort
- Keep behavior deterministic and bounded to one vertical-slice surface.
- Keep existing `ivregress`/`xtreg`/`xtdata`/`estat` Phase 14 behavior stable.

## Non-goals

- No new `estat` diagnostics in this slice.
- No new `predict` support for control-function outputs.
- No broad panel-workflow redesign.
- No nonlinear estimators.
- No R fallback adapter work while Python-first coverage is sufficient.
