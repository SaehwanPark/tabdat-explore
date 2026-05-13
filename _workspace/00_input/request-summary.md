# Phase 14 Slice 7 Request Summary

## User Goal

Resume development from the latest checkpoint by delivering the next bounded Phase 14 slice with
checkpoint commits, updated SDD/handoff artifacts, and a ready-for-review PR.

## Scope

- Phase 14 Slice 7:
  - add control-function endogenous diagnostics through a dedicated post-estimation surface:
    - `estat endogenous`
  - route diagnostics from prior `cfregress` state without changing `cfregress` syntax/options

## Constraints

- Preserve approach order from `SPEC.md`:
  1. Python libraries first
  2. R via `rpy2` only if Python-first is insufficient
  3. lower-level custom numerical implementation only as a last resort
- Keep behavior deterministic and bounded to one vertical-slice surface.
- Keep existing `regress`/`ivregress`/`xtreg`/`xtdata`/`estat` Phase 14 behavior stable.

## Non-goals

- No new `predict` syntax or option surface.
- No changes to IV diagnostics command behavior (`estat firststage`, `estat overid`).
- No broad panel-workflow redesign.
- No nonlinear estimators.
- No R fallback adapter work while Python-first coverage is sufficient.
